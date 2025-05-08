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
import logging
import threading
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

# 日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler('abs_exp_1.log', encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

# 开始监控所有 printer 输出
_orig_printer_print = printer.print
_orig_printer_rule = printer.rule
def _logged_printer_print(msg, *args, **kwargs):
    _orig_printer_print(msg, *args, **kwargs)
    logger.info(str(msg))
def _logged_printer_rule(msg, *args, **kwargs):
    _orig_printer_rule(msg, *args, **kwargs)
    logger.info(f"SECTION: {msg}")
printer.print = _logged_printer_print
printer.rule = _logged_printer_rule

# 开始监控所有内置 print 输出
import builtins
_orig_print = builtins.print
def print(*args, **kwargs):
    _orig_print(*args, **kwargs)
    logger.info(' '.join(str(a) for a in args))
builtins.print = print

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
# 全局文件锁
file_lock = threading.Lock()

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
            "if you cannot answer, please generate \\boxed{Sorry, I don't know.}\n"
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
                # 随机化一下方法，以后看表现调整
                method = random.choice([method, "simple abstraction"])
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

    async def gpt_search_generate_seed(self, domain) -> QAItem:
        """Stub for GPT Search seed generation."""
        # TODO: 实现 GPT Search 专用的 seed 生成逻辑
        resp = agent.chat_with_template(template_name="gpt_search_seed.txt", root_folder=PROMPT_ROOT_FOLDER, template_data={"domain": domain})
        json_resp = extract_and_validate_json(resp)
        if not json_resp:
            raise RuntimeError("GPT-Search seed generation failed")
        
        return QAItem(
                level=0,
                question=json_resp["seed"]["question"].strip(),
                answer=json_resp["seed"]["answer"].strip(),
                parent_question=None,
                evidence=json_resp["seed"].get("evidence", []),
                strategy="seed",
            )

    async def gpt_search_query_update(self, seed: QAItem) -> QAItem:
        """Stub for GPT Search query update."""
        # TODO: 实现 GPT Search 专用的 query update 逻辑

        resp = agent.chat_with_template(
            template_name="gpt_search_Q_update.txt",
            template_data={"question": seed.question, "answer": seed.answer},
            root_folder=PROMPT_ROOT_FOLDER,
        )

        json_resp = extract_and_validate_json(extract_tag_content(resp, "data"))
        if not json_resp:
            raise RuntimeError("GPT-Search query update failed")
        
        # 提取出update之后的question
        updated_question = json_resp["updated_question"].strip()
        updated_evidence = json_resp.get("updated_evidence", [])
        method = json_resp.get("method", "None")
        printer.rule("GPT-Search Query Update Output")
        printer.print(pretty_json(json_resp), style="bold green")
        printer.rule("GPT-Search Query Update Evidence")
        printer.print(pretty_json(updated_evidence), style="bold green")
        # 记录更新后的 QAItem
        updated = QAItem(
            level=seed.level + 1,
            question=updated_question,
            answer=seed.answer,
            parent_question=seed.question,
            evidence=seed.evidence + updated_evidence,
            strategy=method,
        )

        return updated

    async def gpt_search_run(self):
        GPT_MODEL = "gpt-4o-search-preview"
        printer.rule(f"GPT Search Workflow Start with {GPT_MODEL}")
        # 第一步：Seed 生成
        seed = await self.gpt_search_generate_seed()
        self.items.append(seed)
        current = seed

        # 按照 max_level 和 max_tries 进行多级问题升级
        for level in range(self.max_level):
            retries = 0
            while retries < self.max_tries:
                retries += 1
                printer.rule(f"GPT-Search Level {level+1} Update Attempt {retries}")
                # 使用 GPT Search 专用的 query update
                updated = await self.gpt_search_query_update(current)
                # 多重校验
                passed = await self.multi_verify(updated)
                if not passed:
                    printer.print("GPT-Search: 多重校验未通过（模型能回答），重试 query_update …", style="bold red")
                    continue
                printer.print("GPT-Search: 多重校验通过（模型无法回答），记录更新后的 QAItem", style="bold green")
                self.items.append(updated)
                current = updated
                break
            else:
                printer.print(
                    f"GPT-Search stopped at level {current.level}; no valid update after {self.max_tries} tries.",
                    style="bold red",
                )
                return

        printer.rule("GPT-Search Workflow End")

    def save(self, path: Path):
        printer.rule("Saving Results")
        with file_lock:
            existing = []
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.extend([it.to_dict() for it in self.items])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
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

def evaluate(
    json_file: Path = Path("trace_data.json"),
    use_cache: bool = True,
    cache_file: Path | None = None,
):
    """
    Evaluate level-5 items in a JSON trace.
    - json_file: 待评估的 trace JSON 路径
    - use_cache: 是否启用缓存
    - cache_file: 缓存文件路径，默认与 json_file 同目录，名为 "<stem>_eval_cache.json"
    """
    if cache_file is None:
        cache_file = json_file.parent / f"{json_file.stem}_eval_cache.json"
    # 加载或初始化缓存：{question_norm: bool}
    if use_cache and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # 读取所有记录
    with open(json_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    # 筛选 level==5
    items = [r for r in records if r.get("level") == 5]
    total = len(items)
    for rec in items:
        q = rec["question"]
        ans_true = rec["answer"]
        key = q.strip().lower()
        if use_cache and key in cache:
            continue
        # 构造Prompt并调用LLM
        prompt = (
            f"{FORMAT_INSTRUCTION}\nPlease answer the following question and return it strictly in the \\\boxed{{...}} format.\nQuestion: {q}"
        )
        resp = agent.chat(prompt, model="gpt-4o-search-preview")
        printer.log(f"Question:{key}", style="bold yellow")
        printer.print(f"GT Answer: {ans_true}", style="bold yellow")
        ans_pred = extract_boxed(resp)
        printer.print(f"Model Answer: {ans_pred}", style="bold yellow")
        # 标准化比较并去除标点符号
        ans_pred_norm = "".join(c for c in ans_pred.strip().lower() if c.isalnum() or c.isspace())
        ans_true_norm = "".join(c for c in ans_true.strip().lower() if c.isalnum() or c.isspace())
        ok = ans_pred_norm == ans_true_norm
        cache[key] = ok

    # 保存缓存
    if use_cache:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    # 统计准确率
    correct = sum(cache.get(it["question"].strip().lower(), False) for it in items)
    acc = correct / total if total else 0.0
    printer.rule("Evaluation Results")
    printer.print(f"Total level-5 items: {total}", style="bold")
    printer.print(f"Correct predictions: {correct}", style="bold")
    printer.print(f"Accuracy: {acc:.4%}", style="bold green")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("trace_data.json"))
    parser.add_argument("--max_level", type=int, default=5)
    parser.add_argument("--max_tries", type=int, default=5)
    parser.add_argument("--batch", type=int, default=1, help="批量运行次数，>1 则追加写入同一文件")
    parser.add_argument("--concurrency", type=int, default=1, help="最大并行并发数")
    parser.add_argument("--model", type=str, default=None, help="LLM model name to use")
    parser.add_argument("--evaluate", action="store_true", help="只运行 evaluate()，输出 level-5 测试结果并退出")

    args = parser.parse_args()

    # 支持通过命令行覆盖默认模型
    if args.model:
        global GPT_MODEL
        GPT_MODEL = args.model

    # 如果指定 --evaluate，则调用 evaluate 并退出
    if args.evaluate:
        evaluate(json_file=args.out, use_cache=True)
        return

    # 单次执行
    if args.batch <= 1:
        try:
            wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
            asyncio.run(wf.run())
            wf.save(args.out)
            print(f"Saved {len(wf.items)} items to {args.out}")
        except Exception as e:
            logger.exception("Error in single run")
            printer.print(f"Error during single run: {e}", style="bold red")
        return

    # 批量并行执行并追加
    async def _batch():

        # 2. 并发控制信号量
        sem = asyncio.Semaphore(args.concurrency)

        # 3. 定义单次运行任务
        async def run_one(idx: int):
            async with sem:
                try:
                    printer.rule(f"Batch Run {idx+1}/{args.batch}")
                    wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
                    await wf.run()
                    # 完成一次运行后立即读-插入-写回
                    items = [it.to_dict() for it in wf.items]
                    with file_lock:
                        # 读取现有数据列表，文件不存在时视为空
                        try:
                            with open(args.out, "r", encoding="utf-8") as f:
                                existing = json.load(f)
                        except FileNotFoundError:
                            existing = []
                        existing.extend(items)
                        with open(args.out, "w", encoding="utf-8") as f:
                            json.dump(existing, f, ensure_ascii=False, indent=2)
                    printer.print(f"Batch saved {len(items)} items; total now {len(existing)}", style="bold green")
                    return items
                except Exception as e:
                    logger.exception(f"Error in batch run {idx+1}")
                    printer.print(f"Error in batch run {idx+1}: {e}", style="bold red")
                    return []

        # 4. 提交所有任务并等待完成
        await asyncio.gather(*(run_one(i) for i in range(args.batch)))
        printer.print(f"Completed {args.batch} runs; file at {args.out}", style="bold green")

    asyncio.run(_batch())

if __name__ == "__main__":
    main()

"""
%%%
## 跑数据
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --batch 20 --concurrency 20
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --batch 20 --concurrency 20 --model gpt-4o
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --max_level 3 --max_tries 2 --batch 2 --concurrency 3

## 评估
python -m criticsearch.abstract_substitution.abs_exp_1 --out trace_data.json --evaluate
"""