import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..core.utils import scrape_url_content


def _split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """简单的递归文本分块，按自然分隔符切割"""
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

        # 在窗口内找最佳切割点
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
    """RAG 知识库管理器 — 基于 ChromaDB + sentence-transformers"""

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

    def build(self, rag_id: str, urls: list[str]) -> dict:
        """构建知识库 — 抓取所有 URL，分块，嵌入，存入 ChromaDB"""
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

            total_chunks = 0
            for i, url in enumerate(urls):
                text = asyncio.run(scrape_url_content(url, max_chars=None))
                chunks = _split_text(text, chunk_size=1000, chunk_overlap=200)
                if not chunks:
                    continue

                embeddings = model.encode(chunks, show_progress_bar=False).tolist()
                ids = [f"{rag_id}_{total_chunks + j}" for j in range(len(chunks))]
                metadatas = [{"url": url, "chunk_index": j} for j in range(len(chunks))]

                collection.add(
                    ids=ids,
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                total_chunks += len(chunks)

            with self._lock:
                self._stores[rag_id]["status"] = "ready"
                self._stores[rag_id]["chunk_count"] = total_chunks

            return {"status": "ready", "chunk_count": total_chunks}

        except Exception as e:
            with self._lock:
                self._stores[rag_id]["status"] = "failed"
                self._stores[rag_id]["error"] = str(e)
            raise

    def query(self, rag_id: str, question: str, top_k: int = 5) -> list[str]:
        """查询知识库，返回相关文档片段"""
        try:
            model = self._get_embedding_fn()
            collection = self._chroma_client.get_collection(name=rag_id)
            query_embedding = model.encode([question], show_progress_bar=False).tolist()

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
            )

            documents = results.get("documents", [[]])[0]
            return documents
        except Exception:
            return []

    def get_stats(self, rag_id: str) -> Optional[dict]:
        with self._lock:
            store = self._stores.get(rag_id)
            if not store:
                return None
            return {
                "rag_id": rag_id,
                "status": store["status"],
                "urls": store["urls"],
                "chunk_count": store["chunk_count"],
                "created_at": store["created_at"].isoformat(),
                "error": store.get("error"),
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
