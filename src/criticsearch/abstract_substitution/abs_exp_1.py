"""
========================================
Generates multi‑level reverse‑upgrade benchmark questions.

Usage:
    python -m criticsearch.abstract_substitution.abs_exp_1 --out <output_file.json> --max_level <max_level> --max_tries <max_tries>
Dependencies:
    pip install openai httpx beautifulsoup4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI
from bs4 import BeautifulSoup
from criticsearch.config import settings
from criticsearch.rich_output import printer
from criticsearch.base_agent import BaseAgent
from criticsearch.utils import (
    extract_queries_from_response,
    extract_answer_from_response,
    extract_boxed_content,
    extract_and_validate_json,
    extract_actions,
    extract_tag_content,
)

# === Constants & API Keys ===
GPT_MODEL = getattr(settings, "default_model", "gpt-4o")
GPT_API_KEY = settings.models[GPT_MODEL].get("api_key")
GPT_BASE_URL = settings.models[GPT_MODEL].get("base_url")
MAX_TOKENS = settings.models[GPT_MODEL].get("max_tokens", 8192)

TAVILY_API_KEY = settings.tavily.api_key
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"

PROMPT_ROOT_FOLDER = "prompts"
FORMAT_INSTRUCTION = """
Your answer must be contained within \\boxed{...}, otherwise your response will be considered incorrect. This format must be followed without exception.
For example, you can answer: \\boxed{China}, but not: China. You can answer: The answer is \\boxed{3}, but not: 3.
"""
# === Initialization ===
agent = BaseAgent()

def pretty_json(data):
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)

# === OpenAI LLM Call Helper ===
def call_llm(
    prompt: str,
    *,
    model: str = GPT_MODEL,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
) -> str:
    """Call OpenAI chat completion (stand‑alone)."""
    printer.rule("LLM Prompt")
    printer.print(prompt, style="bold yellow")
    if system_prompt:
        printer.print(f"[system prompt]: {system_prompt}", style="italic cyan")
    client = OpenAI(api_key=GPT_API_KEY, base_url=GPT_BASE_URL)
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=MAX_TOKENS,
    )
    result = resp.choices[0].message.content
    printer.rule("LLM Raw Output")
    printer.print(result, style="bold green")
    return result

# === Tavily Search & Extract ===
async def tavily_search(query: str, *, include_raw_content: bool = True) -> List[dict]:
    # printer.rule("Tavily Search Query")
    # printer.print(query, style="bold yellow")
    payload = {"query": query, "include_raw_content": include_raw_content, "api_key": TAVILY_API_KEY}
    async with httpx.AsyncClient(http2=True, timeout=30) as client:
        r = await client.post(TAVILY_SEARCH_URL, json=payload)
    time.sleep(0.1)
    results = r.json().get("results", [])
    # printer.rule("Tavily Search Results")
    # printer.print(pretty_json(results), style="bold green")
    return results

async def tavily_extract(urls: List[str]) -> Dict[str, dict]:
    printer.rule("Tavily Extract URLs")
    printer.print(pretty_json(urls), style="bold yellow")
    async with httpx.AsyncClient(http2=True, timeout=30) as client:
        r = await client.post(
            TAVILY_EXTRACT_URL,
            json={"urls": urls},
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
        )
    result = r.json()
    printer.rule("Tavily Extract Results")
    printer.print(pretty_json(result), style="bold green")
    return result

async def fallback_scrape(urls: List[str]) -> Dict[str, str]:
    printer.rule("Fallback Scrape URLs")
    printer.print(pretty_json(urls), style="bold yellow")
    headers = {"User-Agent": "Mozilla/5.0"}
    async def fetch(u: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(u, headers=headers)
            if r.status_code != 200:
                return ""
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script", "style", "noscript", "meta"]):
                t.decompose()
            return "\n".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        except Exception:
            return ""
    texts = await asyncio.gather(*(fetch(u) for u in urls))
    result = {u: t for u, t in zip(urls, texts)}
    printer.rule("Fallback Scrape Results")
    printer.print(pretty_json(result), style="bold green")
    return result

# === Regex Utils ===
BOXED_RE = re.compile(r"\\boxed{([^}]+)}")
ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL | re.IGNORECASE)

def extract_boxed(text: str) -> str:
    m = BOXED_RE.search(text)
    return m.group(1).strip() if m else ""

def extract_answer_tag(text: str) -> str:
    m = ANSWER_TAG_RE.search(text)
    return m.group(1).strip() if m else ""

# === Data Structures ===
@dataclass
class QAItem:
    level: int
    question: str
    answer: str
    parent_question: Optional[str]
    evidence: List[str]
    strategy: str

    def to_dict(self) -> dict:
        return asdict(self)

# === Workflow ===
class ReverseUpgradeWorkflow:
    def __init__(self, *, max_level: int = 5, max_tries: int = 5):
        self.max_level = max_level
        self.max_tries = max_tries
        self.items: List[QAItem] = []

    @staticmethod
    def random_domain():
        domains = [
            "TV shows & movies",
            "Other",
            "Science & technology",
            "Art",
            "History",
            "Sports",
            "Music",
            "Video games",
            "Geography",
            "Politics",
        ]
        return random.choice(domains)
    
    def method_choice(self, question: str, answer: str) -> str:
        
        methods = [
            "equivalent replacement",
            "simple abstraction",
        ]
        model_choice = agent.chat_with_template(
            template_name="abs_method_choice.txt",
            template_data={"question": question, "answer": answer},
            root_folder=PROMPT_ROOT_FOLDER,
        )
        method = extract_tag_content(model_choice, "method")
        queries = extract_tag_content(model_choice, "queries")

        norm = method.strip().lower().replace(" ", "")
        for m in methods:
            if norm == m.lower().replace(" ", ""):
                return m, queries
            
        return methods[0], queries
    
    async def multi_verify(self, seed: QAItem) -> bool:
        """
        对给定的 QAItem 进行多重校验。
        Returns:
            bool: True 表示验证通过（模型无法回答），False 表示验证失败（模型能回答）
        """
        prompt = (
            "You need to answer the question\n"
            f"Question: {seed.question}\n"
            f"{FORMAT_INSTRUCTION}"
        )
        
        # 第一步：直接校验模型内部知识是否能回答
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            direct_answer = agent.chat(prompt, model = "gpt-4o")
            boxed_answer = extract_boxed(direct_answer)
            if not boxed_answer:
                printer.rule(f"格式错误重试 #{attempt}")
                printer.print("模型原始返回：", style="bold red")
                printer.print(direct_answer, style="bold red")
                if attempt == max_retries:
                    raise RuntimeError(f"连续 {max_retries} 次格式错误（答案未包含在 \\boxed{{}} 中），终止执行")
                continue
            
            if boxed_answer == seed.answer:    
                printer.print("验证失败：模型能直接回答", style="bold red")
                return False
            break

        # 第二步：如果模型不能直接回答，进行搜索
        search_results = await tavily_search(seed.question)
        
        for attempt in range(1, max_retries + 1):
            search_based_answer = agent.chat(prompt + f"here are some search results:\n\n{search_results}", model = "gpt-4o") 
            boxed_answer = extract_boxed(search_based_answer)
            if not boxed_answer:
                printer.rule(f"搜索验证格式错误重试 #{attempt}")
                printer.print("模型原始返回：", style="bold red")
                printer.print(search_based_answer, style="bold red")
                if attempt == max_retries:
                    raise RuntimeError(f"连续 {max_retries} 次格式错误（基于搜索的答案未包含在 \\boxed{{}} 中），终止执行")
                continue
                
            if boxed_answer == seed.answer:
                printer.print("验证失败：模型能通过搜索回答", style="bold red")
                return False
            break

        printer.print("验证通过：模型无法直接回答也无法通过搜索回答", style="bold green")
        return True
    
    async def query_update(self, method, queries, seed: Optional[QAItem]):
        search_results = await asyncio.gather(*(tavily_search(q) for q in queries)) 
        question_update_resp = agent.chat_with_template(
            template_name="abs_query_update.txt",
            template_data={"method": method, "search_results": search_results, "question": seed.question, "answer": seed.answer},
            root_folder=PROMPT_ROOT_FOLDER,
        )
        # 提取出update之后的question
        updated_item = extract_and_validate_json(extract_tag_content(question_update_resp, "data"))
        updated_question = updated_item["updated_question"].strip()
        updated_evidence = updated_item.get("updated_evidence", [])

        printer.rule("Query Update Output")
        printer.print(pretty_json(updated_item), style="bold green")
        printer.rule("Query Update Evidence")       
        printer.print(pretty_json(updated_evidence), style="bold green")

        return QAItem(
            level=seed.level + 1,
            question=updated_question,
            answer=seed.answer,
            parent_question=seed.question,
            evidence=seed.evidence + updated_evidence,
            strategy=method,
        )   

    async def generate_seed(self) -> QAItem:
        max_query_retries = 3
        for attempt in range(1, max_query_retries + 1):
            random_domain = self.random_domain()
            query_resp = agent.chat_with_template(
                template_name="search_query_for_seed_fact.txt",
                template_data={"domain": random_domain},
                root_folder=PROMPT_ROOT_FOLDER,
            )
            queries = extract_queries_from_response(query_resp)[:3]
            if queries:
                printer.rule(f"Extracted Queries for Seed Fact in {random_domain} Domain")
                printer.print(queries, style="bold cyan")
                break
            printer.print(f"第 {attempt} 次抽取到空 queries，重试中…", style="bold red")
            printer.print(query_resp, style="bold red")
        else:
            raise RuntimeError("连续 3 次 Extracted Queries 为空，终止执行")

        search_results = await asyncio.gather(*(tavily_search(q) for q in queries))

        seed_fact_resp = extract_and_validate_json(agent.chat_with_template(            template_name="seed_idea_from_internet.txt",            template_data={"domain": random_domain,"search_results": search_results,},             root_folder=PROMPT_ROOT_FOLDER        ))
        printer.rule(f"Generate Seed Fact Output after browsing in {random_domain}")
        printer.print(pretty_json(seed_fact_resp), style="bold green")
        return QAItem(
            level=0,
            question=seed_fact_resp["seed"]["question"].strip(),
            answer=seed_fact_resp["seed"]["answer"].strip(),
            parent_question=None,
            evidence=seed_fact_resp["seed"].get("evidence", []),
            strategy="seed",
        )

    async def run(self):
        printer.rule(f"Workflow Start with {GPT_MODEL}")
        seed = await self.generate_seed()
        self.items.append(seed)
        current = seed

        # 按照 max_level 和 max_tries 进行多级问题升级
        for level in range(self.max_level):
            retries = 0
            while retries < self.max_tries:
                retries += 1
                printer.rule(f"Level {level+1} Update Attempt {retries}")
                method, queries = self.method_choice(current.question, current.answer)
                updated = await self.query_update(method, queries, current)
                passed = await self.multi_verify(updated)
                if not passed:  # 验证失败（模型能回答）
                    printer.print("多重校验未通过（模型能回答），重试 query_update …", style="bold red")
                    continue
                printer.print("多重校验通过（模型无法回答），记录更新后的 QAItem", style="bold green")
                self.items.append(updated)  # 只有验证通过才记录
                current = updated
                break
            else:
                printer.print(f"Stopped at level {current.level}; no valid update after {self.max_tries} tries.", style="bold red")
                return

        printer.rule("Workflow End")

    def save(self, path: Path):
        printer.rule("Saving Results")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([it.to_dict() for it in self.items], f, ensure_ascii=False, indent=2)
        printer.print(f"Saved {len(self.items)} items to {path}", style="bold green")
        printer.rule("Saved JSON Preview")
        printer.print(pretty_json([it.to_dict() for it in self.items]), style="bold cyan")

    @staticmethod
    def _safe_json(text: str) -> dict:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        raw = m.group(1) if m else text
        raw = raw.strip("`\n ")
        return json.loads(raw)

def random_domain():
    domains = ["TV shows & movies", "Other", "Science & technology", "Art", "History", "Sports", "Music", "Video games", "Geography", "Politics"]
    return random.choice(domains)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("trace_data.json"))
    parser.add_argument("--max_level", type=int, default=5)
    parser.add_argument("--max_tries", type=int, default=5)
    parser.add_argument("--batch", type=int, default=1, help="批量运行次数，>1 则追加写入同一文件")
    parser.add_argument("--concurrency", type=int, default=1, help="最大并行并发数")
    args = parser.parse_args()

    # 单次执行
    if args.batch <= 1:
        wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
        asyncio.run(wf.run())
        wf.save(args.out)
        print(f"Saved {len(wf.items)} items to {args.out}")
        return

    # 批量并行执行并追加
    async def _batch():
        # 1. 读取已有数据
        all_items = []
        if args.out.exists():
            with open(args.out, "r", encoding="utf-8") as f:
                all_items = json.load(f)

        # 2. 并发控制信号量
        sem = asyncio.Semaphore(args.concurrency)

        # 3. 定义单次运行任务
        async def run_one(idx: int):
            async with sem:
                printer.rule(f"Batch Run {idx+1}/{args.batch}")
                wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
                await wf.run()
                return [it.to_dict() for it in wf.items]

        # 4. 提交所有任务并收集结果
        batches = await asyncio.gather(*(run_one(i) for i in range(args.batch)))

        # 5. 扁平化并写回文件
        for batch_items in batches:
            all_items.extend(batch_items)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        printer.print(f"Completed {args.batch} runs, total items: {len(all_items)}", style="bold green")

    asyncio.run(_batch())

if __name__ == "__main__":
    main()

"""
%%%
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --batch 20 --concurrency 20
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --max_level 3 --max_tries 2 --batch 2 --concurrency 3
"""