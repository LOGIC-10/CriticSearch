import asyncio
from .base_agent import BaseAgent
from .main import _action_router
from .reportbench.verifier import ReportVerifier

class Session:
    """
    按 step 接口包装 CriticSearch 流程，供 RAGEN 环境调用。
    """
    def __init__(self, prompt: str):
        # 初始化 agent
        self.user_prompt = prompt
        self.agent = BaseAgent()
        self.agent.receive_task(prompt)
        self.agent.training_data = [{"from": "human", "value": prompt}]
        self.agent.memo = set()
        # 流程状态
        self.search_results = ""
        self.detailed_web_results = ""
        self.agent_report = ""
        # 用于评估写作结果
        self.verifier = ReportVerifier(self.agent)
        self.last_score = 0.0

    def search(self, queries: list[str]) -> str:
        # 执行异步搜索
        self.search_results = asyncio.run(
            self.agent.search_aggregator.search(queries)
        )
        return self.search_results

    def browse(self, urls: list[str]) -> str:
        # 执行网页爬取
        web = asyncio.run(self.agent.content_scraper.scrape(urls=urls))
        self.detailed_web_results += "\n\n" + web
        return web

    def take_notes(self, text: str) -> str:
        # 记录笔记
        notes = self.agent.taking_notes(text)
        self.agent.training_data.append({
            "from": "agent", "action": "TAKING_NOTES", "action_content": notes
        })
        return notes

    def start_writing(self, section: str) -> str:
        # 调用 _action_router 生成本段落
        content = _action_router(
            self.agent,
            self.search_results,
            self.user_prompt,
            section,
            iteration=0,
            agent_report=self.agent_report,
            guide_line=section,
            detailed_web_results=self.detailed_web_results,
        )
        # 累计报告
        self.agent_report += "\n" + content
        # TODO: 验证本段落（此处第二参暂传空 list，如有 GT 可改为真实 facts）
        self.last_score = self.verifier.verify_section(content, [])
        return content