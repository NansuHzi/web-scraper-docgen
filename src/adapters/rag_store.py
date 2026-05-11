import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable

import chromadb
from chromadb.config import Settings as ChromaSettings


def _split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """递归文本分块，按自然分隔符切割"""
    separators = ["\n\n", "\n", "。", "，", " ", ""]
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        best_cut = end
        window_start = max(start, end - chunk_size // 2)
        for sep in separators:
            pos = text.rfind(sep, window_start, end)
            if pos != -1:
                best_cut = pos + len(sep)
                break

        chunks.append(text[start:best_cut])
        start = best_cut - chunk_overlap
        if start < 0:
            start = 0

    return [c.strip() for c in chunks if c.strip()]


class RAGStore:
    """RAG 知识库管理器 — ChromaDB + sentence-transformers"""

    def __init__(
        self,
        persist_dir: str = "output/chroma_db",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        ttl_hours: int = 24,
    ):
        self._persist_dir = persist_dir
        self._embedding_model_name = embedding_model
        self._ttl = timedelta(hours=ttl_hours)
        self._stores: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._embedding_fn = None
        self._chroma_client = None
        self._running = False
        self._progress_callbacks: dict[str, Callable] = {}
        self._init_chroma()

    def _init_chroma(self):
        import os
        os.makedirs(self._persist_dir, exist_ok=True)
        self._chroma_client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _get_embedding_fn(self):
        if self._embedding_fn is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_fn = SentenceTransformer(self._embedding_model_name)
        return self._embedding_fn

    def build_sync(self, rag_id: str, urls: list[str]) -> dict:
        """同步构建知识库（在后台线程中调用）"""
        from ..core.utils import scrape_url_content

        with self._lock:
            self._stores[rag_id] = {
                "status": "building",
                "urls": urls,
                "chunk_count": 0,
                "created_at": datetime.now(),
                "collection_name": rag_id,
                "error": None,
            }

        try:
            model = self._get_embedding_fn()
            collection = self._chroma_client.get_or_create_collection(
                name=rag_id,
                metadata={"hnsw:space": "cosine"},
            )

            # Phase 1: Scrape all URLs concurrently
            async def _scrape_all():
                tasks = [scrape_url_content(url, max_chars=6000) for url in urls]
                return await asyncio.gather(*tasks, return_exceptions=True)

            scrape_results = asyncio.run(_scrape_all())

            # Phase 2: Process embeddings for successfully scraped content
            total_chunks = 0
            for i, (url, result) in enumerate(zip(urls, scrape_results)):
                with self._lock:
                    self._stores[rag_id]["progress"] = f"{i + 1}/{len(urls)}"

                if isinstance(result, Exception):
                    with self._lock:
                        self._stores[rag_id]["error"] = f"URL {url}: {result}"
                    continue

                text = result
                if not text:
                    continue

                try:
                    chunks = _split_text(text, chunk_size=800, chunk_overlap=150)
                    if not chunks:
                        continue

                    embeddings = model.encode(chunks, show_progress_bar=False).tolist()
                    ids = [f"{rag_id}_{total_chunks + j}" for j in range(len(chunks))]
                    metadatas = [{"url": url, "chunk_index": j, "source": url} for j in range(len(chunks))]

                    collection.add(
                        ids=ids,
                        documents=chunks,
                        embeddings=embeddings,
                        metadatas=metadatas,
                    )
                    total_chunks += len(chunks)

                except Exception as e:
                    with self._lock:
                        self._stores[rag_id]["error"] = f"URL {url}: {e}"
                    continue

            with self._lock:
                self._stores[rag_id]["status"] = "ready"
                self._stores[rag_id]["chunk_count"] = total_chunks

            return {"status": "ready", "chunk_count": total_chunks}

        except Exception as e:
            with self._lock:
                self._stores[rag_id]["status"] = "failed"
                self._stores[rag_id]["error"] = str(e)
            raise

    def start_build(self, rag_id: str, urls: list[str]):
        """在后台线程中启动知识库构建"""
        t = threading.Thread(target=self.build_sync, args=(rag_id, urls), daemon=True)
        t.start()

    def query(self, rag_id: str, query_text: str, top_k: int = 5) -> list[dict]:
        """语义搜索知识库，返回相关文档片段及元数据"""
        try:
            model = self._get_embedding_fn()
            collection = self._chroma_client.get_collection(name=rag_id)
            query_embedding = model.encode([query_text], show_progress_bar=False).tolist()

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            items = []
            for i, doc in enumerate(documents):
                items.append({
                    "content": doc,
                    "source": metadatas[i].get("source", "") if i < len(metadatas) else "",
                    "score": round(1.0 - distances[i], 4) if i < len(distances) else 0,
                })
            return items
        except Exception:
            return []

    def list_stores(self) -> list[dict]:
        """列出所有知识库"""
        with self._lock:
            return [
                {
                    "rag_id": rid,
                    "status": s["status"],
                    "url_count": len(s.get("urls", [])),
                    "chunk_count": s.get("chunk_count", 0),
                    "created_at": s["created_at"].isoformat(),
                    "error": s.get("error"),
                }
                for rid, s in sorted(
                    self._stores.items(),
                    key=lambda x: x[1].get("created_at", datetime.min),
                    reverse=True,
                )
            ]

    def delete_store(self, rag_id: str) -> bool:
        """删除知识库"""
        with self._lock:
            if rag_id not in self._stores:
                return False
            del self._stores[rag_id]

        try:
            self._chroma_client.delete_collection(name=rag_id)
        except Exception:
            pass
        return True

    def get_stats(self, rag_id: str) -> Optional[dict]:
        with self._lock:
            store = self._stores.get(rag_id)
            if not store:
                return None
            return {
                "rag_id": rag_id,
                "status": store["status"],
                "urls": store["urls"],
                "chunk_count": store.get("chunk_count", 0),
                "created_at": store["created_at"].isoformat(),
                "error": store.get("error"),
                "progress": store.get("progress", ""),
            }

    def start_cleanup(self):
        self._running = True
        t = threading.Thread(target=self._cleanup_loop, daemon=True)
        t.start()

    def stop_cleanup(self):
        self._running = False

    def _cleanup_loop(self):
        while self._running:
            try:
                self._cleanup_expired()
            except Exception:
                pass
            time.sleep(3600)

    def _cleanup_expired(self):
        with self._lock:
            now = datetime.now()
            expired = [
                rid for rid, data in self._stores.items()
                if now - data["created_at"] > self._ttl
            ]
            for rid in expired:
                try:
                    self._chroma_client.delete_collection(name=rid)
                except Exception:
                    pass
                del self._stores[rid]


rag_store = RAGStore()
