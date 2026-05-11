from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..adapters.topic_manager import topic_manager
from ..core.crew import create_topic_analysis_crew
from ..api.scraper import _topic_semaphore
import asyncio
import json
import re
from datetime import datetime

router = APIRouter()


class AnalyzeTopicsRequest(BaseModel):
    topics: list[dict]


@router.get("/topics/hot")
async def get_hot_topics(source: str = Query("all", description="数据来源: all, weibo, zhihu")):
    async with _topic_semaphore:
        try:
            weibo_topics = []
            zhihu_topics = []

            if source in ("all", "weibo"):
                weibo_topics = topic_manager.scrape_weibo_hot()

            if source in ("all", "zhihu"):
                zhihu_topics = await topic_manager.scrape_zhihu_hot()

            if not weibo_topics and not zhihu_topics:
                raise HTTPException(status_code=503, detail="无法获取热搜数据，请稍后重试")

            llm_recommendations = []
            if weibo_topics or zhihu_topics:
                prompt = topic_manager.build_llm_prompt(weibo_topics, zhihu_topics)
                try:
                    crew, _ = create_topic_analysis_crew(prompt)
                    result = await asyncio.to_thread(crew.kickoff)

                    result_text = ""
                    if hasattr(result, 'raw'):
                        result_text = str(result.raw)
                    elif hasattr(result, 'tasks_output') and len(result.tasks_output) > 0:
                        last_task = result.tasks_output[-1]
                        result_text = str(last_task.raw if hasattr(last_task, 'raw') else last_task)
                    else:
                        result_text = str(result)

                    llm_recommendations = _parse_llm_response(result_text)
                except Exception as e:
                    llm_recommendations = _build_fallback_recommendations(weibo_topics, zhihu_topics)
                    llm_recommendations.insert(0, {"note": f"LLM分析失败，返回基础推荐: {str(e)}"})

            return {
                "weibo_topics": weibo_topics,
                "zhihu_topics": zhihu_topics,
                "llm_recommendations": llm_recommendations,
                "generated_at": datetime.now().isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取热搜失败: {str(e)}")


@router.get("/topics/hot/weibo")
async def get_weibo_hot():
    """仅获取微博热搜"""
    try:
        topics = topic_manager.scrape_weibo_hot()
        return {"topics": topics, "source": "weibo", "count": len(topics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/hot/zhihu")
async def get_zhihu_hot():
    """仅获取知乎热榜"""
    try:
        topics = await topic_manager.scrape_zhihu_hot()
        return {"topics": topics, "source": "zhihu", "count": len(topics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/analyze")
async def analyze_topics(request: AnalyzeTopicsRequest):
    """分析自定义话题列表"""
    try:
        if not request.topics:
            raise HTTPException(status_code=400, detail="话题列表不能为空")

        topic_text = "\n".join(
            f"{i+1}. {t.get('title', '')} [{t.get('source', '')}]"
            for i, t in enumerate(request.topics[:30])
        )

        prompt = "分析以下话题列表，推荐值得撰写文档的选题：\n\n" + topic_text
        prompt += "\n\n请输出 JSON: {\"recommendations\": [{\"rank\": 1, \"title\": \"...\", \"reason\": \"...\", \"angle\": \"...\", \"estimated_interest\": \"high|medium|low\"}]}"

        crew, _ = create_topic_analysis_crew(prompt)
        result = await asyncio.to_thread(crew.kickoff)

        result_text = ""
        if hasattr(result, 'raw'):
            result_text = str(result.raw)
        elif hasattr(result, 'tasks_output') and len(result.tasks_output) > 0:
            last_task = result.tasks_output[-1]
            result_text = str(last_task.raw if hasattr(last_task, 'raw') else last_task)
        else:
            result_text = str(result)

        recommendations = _parse_llm_response(result_text)
        return {"recommendations": recommendations}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"话题分析失败: {str(e)}")


def _parse_llm_response(text: str) -> list[dict]:
    """解析 LLM 返回的 JSON 推荐结果"""
    try:
        json_match = re.search(r'\{[\s\S]*"recommendations"[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("recommendations", [])
    except (json.JSONDecodeError, KeyError):
        pass

    try:
        json_match = re.search(r'\[[\s\S]*\{[\s\S]*\}[\s\S]*\]', text)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return data
    except json.JSONDecodeError:
        pass

    return [{"raw_analysis": text[:500]}]


def _build_fallback_recommendations(weibo_topics: list[dict], zhihu_topics: list[dict]) -> list[dict]:
    """LLM 不可用时的基础推荐"""
    all_topics = sorted(weibo_topics + zhihu_topics, key=lambda x: x.get("rank", 99))
    recommendations = []
    for t in all_topics[:8]:
        title = t.get("title", "")
        if not title:
            continue
        recommendations.append({
            "rank": len(recommendations) + 1,
            "title": title,
            "reason": f"当前{t['source']}热搜话题",
            "angle": f"深入分析{title}相关的技术背景和发展趋势",
            "estimated_interest": "medium",
            "related_topics": [],
        })
    return recommendations
