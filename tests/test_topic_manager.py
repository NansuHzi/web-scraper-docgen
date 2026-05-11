import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adapters.topic_manager import TopicManager


class TestTopicManager:
    """TopicManager 单元测试"""

    def setup_method(self):
        self.manager = TopicManager()

    def test_scrape_weibo_hot(self):
        """测试微博热搜抓取（依赖外部网络）"""
        topics = self.manager.scrape_weibo_hot(max_items=10)
        assert isinstance(topics, list)

        if len(topics) > 0:
            topic = topics[0]
            assert "title" in topic
            assert topic["source"] == "weibo"
            assert "rank" in topic
            assert isinstance(topic["rank"], int)
            assert len(topic["title"]) > 0

    def test_zhihu_hot_text_parse(self):
        """测试知乎热榜文本解析"""
        mock_content = (
            "网页标题: 知乎热榜\n\n"
            "这是一个热门话题\n"
            "另一个热门讨论\n"
            "第三个话题\n"
            "登录\n"
            "注册\n"
        )
        topics = self.manager._parse_zhihu_hot_text(mock_content, max_items=5)
        assert len(topics) > 0
        for t in topics:
            assert t["source"] == "zhihu"
            assert "title" in t
            assert "rank" in t

    def test_zhihu_hot_text_parse_skips_irrelevant(self):
        """测试文本解析跳过不相关行"""
        mock_content = (
            "网页标题: 知乎\n"
            "知乎\n"
            "登录\n"
            "注册\n"
            "发现\n"
            "首页\n"
            "Actual Topic Here\n"
        )
        topics = self.manager._parse_zhihu_hot_text(mock_content, max_items=5)
        assert len(topics) == 1
        assert topics[0]["title"] == "Actual Topic Here"

    def test_build_llm_prompt(self):
        weibo = [{"title": "微博话题1", "source": "weibo", "rank": 1, "heat": "热", "hot_value": "100万"}]
        zhihu = [{"title": "知乎话题1", "source": "zhihu", "rank": 1, "heat": "", "hot_value": ""}]
        prompt = self.manager.build_llm_prompt(weibo, zhihu)
        assert "微博热搜" in prompt
        assert "知乎热榜" in prompt
        assert "微博话题1" in prompt
        assert "知乎话题1" in prompt
        assert "recommendations" in prompt

    def test_build_llm_prompt_empty(self):
        prompt = self.manager.build_llm_prompt([], [])
        assert "输出格式要求" in prompt
