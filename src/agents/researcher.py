from crewai import Agent
from crewai.tools import tool
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.core.llm import deepseek_llm


@tool
def scrape_webpage(url: str) -> str:
    """抓取指定URL的网页内容，提取纯文本和标题（支持JavaScript动态渲染）"""
    try:
        # 尝试使用 Playwright 进行浏览器自动化抓取（支持JS动态内容）
        
        with sync_playwright() as p:
            # 启动浏览器（无头模式）
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # 访问页面并等待加载
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 额外等待2秒确保动态内容完全加载
            page.wait_for_timeout(2000)
            
            # 获取渲染后的HTML内容
            html_content = page.content()
            title = page.title()
            
            # 关闭浏览器
            browser.close()
        
        # 使用 BeautifulSoup 解析渲染后的HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # 提取主要文本内容（优先提取文章区域）
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # 清理空白行和多余空格
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        # 检查是否抓取到有效内容
        if not cleaned_text or len(cleaned_text.strip()) < 50:
            raise Exception(f"网页内容为空或过少（{len(cleaned_text)}字符），无法继续处理")
        
        # 限制长度节省Token，但保留更多内容（5000字符）
        return f"网页标题: {title}\n\n网页内容摘要:\n{cleaned_text[:5000]}..."
    except Exception as e:
        # 抛出异常以终止整个 Crew 流程
        raise Exception(f"网页抓取失败: {str(e)}。任务已终止。")


class Researcher:
    def __init__(self):
        self.agent = Agent(
            role='网页内容研究员',
            goal='准确抓取并且提取网页中的关键信息',
            backstory='你拥有10年经验的网页内容分析专家，擅长从复杂的网页中提取结构化数据，为后续文档撰写提供原材料。',
            tools=[scrape_webpage],  # 将工具绑定给Agent
            llm=deepseek_llm,  # ← 指定使用 DeepSeek
            verbose=True
        )
