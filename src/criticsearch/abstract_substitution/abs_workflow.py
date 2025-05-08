# -*- coding: utf-8 -*-
"""
========================================
Generates multi‑level reverse‑upgrade benchmark questions.

Usage:
    python -m criticsearch.abstract_substitution.abs_workflow --out <output_file.json> --max_level <max_level> --max_tries <max_tries>
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
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# Ensure the log file handler is added only once even if the module is reloaded
if not logger.handlers:
    fh = logging.FileHandler('abs_workflow.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

# 开始监控所有 printer 输出
_orig_printer_print = printer.print
_orig_printer_rule = printer.rule
def _logged_printer_print(msg, *args, **kwargs):
    _orig_printer_print(msg, *args, **kwargs)
    # Attempt to convert msg to string safely for logging
    try:
        log_msg = str(msg)
    except Exception:
        log_msg = repr(msg) # Fallback to repr if str fails
    logger.info(log_msg)
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
            for t in soup(["script", "style", "noscript", "meta"]): # Keeping original tags
                t.decompose()
            # Keeping original text extraction method
            return "\n".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        except Exception:
             # Keeping original bare except
            return ""
    texts = await asyncio.gather(*(fetch(u) for u in urls))
    result = {u: t for u, t in zip(urls, texts)} # Keeping original logic (includes empty results)
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
    constrained_format: str
    parent_question: Optional[str]
    evidence: List[str]
    strategy: str

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class FuzzyQAItem:
    original_question: str
    question: str
    answer: str
    constrained_format: str
    strategy: str
    evidence: List[str]

    def to_dict(self) -> dict:
        return asdict(self)

async def verify_fuzzy_item(item: FuzzyQAItem) -> bool:
    """
    验证模糊替换后的问题是否能从evidence中的facts中直接推理出答案:
    - 拼接 evidence 中的 fact 条目
    - 加入 question 和 constrained_format
    - 要求模型以 \\boxed{} 格式作答
    """
    # 拼接 evidence facts
    lines: List[str] = []
    for f in item.evidence:
        if isinstance(f, dict):
            fact = f.get("fact")
            if fact:
                lines.append(f"- {fact}")
        elif isinstance(f, str):
            txt = f.strip()
            if txt:
                lines.append(f"- {txt}")
    facts = "\n".join(lines)

    prompt = (
        f"Based on these facts:\n{facts}\n\n"
        f"Question: {item.question}\n"
        f"Format constraint: {item.constrained_format}\n"
        f"{FORMAT_INSTRUCTION}"
    )
    try:
        resp = agent.chat(prompt, model="o4-mini")
        pred = extract_boxed_content(resp)
        if not pred:
            printer.print("验证失败：未返回 boxed 内容", style="bold red")
            return False
        # 规范化比较
        norm_pred = "".join(c for c in pred.lower() if c.isalnum() or c.isspace()).replace(" ", "")
        norm_true = "".join(c for c in item.answer.lower() if c.isalnum() or c.isspace()).replace(" ", "")
        if norm_pred != norm_true:
            printer.print(f"验证失败：答案不匹配 (pred={pred}  true={item.answer})", style="bold red")
            return False
        printer.print("验证通过：格式及答案均正确", style="bold green")
        return True
    except Exception as e:
        printer.print(f"验证过程出错：{e}", style="bold red")
        logger.exception("verify_fuzzy_item error")
        return False

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

    def method_choice(self, question: str, answer: str) -> tuple[str, str]: # Restored original return type hint assumption
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
        # Assuming queries is a string in the original logic based on return hint
        queries = extract_tag_content(model_choice, "queries")

        # Keeping original logic for method selection and default
        norm = method.strip().lower().replace(" ", "")
        for m in methods:
            if norm == m.lower().replace(" ", ""):
                return m, queries

        # Original code defaulted to methods[0] without warning
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
        max_retries = 5 # Keeping original retry count
        for attempt in range(1, max_retries + 1):
            # Keeping original direct call to agent.chat
            direct_answer = agent.chat(prompt, model = "gpt-4o")
            boxed_answer = extract_boxed_content(direct_answer)
            if not boxed_answer:
                printer.rule(f"格式错误重试 #{attempt}")
                printer.print("模型原始返回：", style="bold red")
                printer.print(direct_answer, style="bold red")
                if attempt == max_retries:
                    # Keeping original RuntimeError
                    raise RuntimeError(f"连续 {max_retries} 次格式错误（答案未包含在 \\boxed{{}} 中），终止执行")
                continue # Original code just continued

            # Keeping original direct string comparison
            if boxed_answer == seed.answer:
                printer.print("验证失败：模型能直接回答", style="bold red")
                return False
            break # Original code broke here if format was ok and answer didn't match

        # 第二步：如果模型不能直接回答，进行搜索
        # Keeping original search call logic
        search_results = await tavily_search(seed.question) # Original didn't specify include_raw_content=False

        # Keeping original second verification loop
        for attempt in range(1, max_retries + 1):
            # Keeping original construction of prompt with search results
            search_based_answer = agent.chat(prompt + f"here are some search results:\n\n{search_results}", model = "gpt-4o")
            boxed_answer = extract_boxed_content(search_based_answer)
            if not boxed_answer:
                printer.rule(f"搜索验证格式错误重试 #{attempt}")
                printer.print("模型原始返回：", style="bold red")
                printer.print(search_based_answer, style="bold red")
                if attempt == max_retries:
                     # Keeping original RuntimeError
                    raise RuntimeError(f"连续 {max_retries} 次格式错误（基于搜索的答案未包含在 \\boxed{{}} 中），终止执行")
                continue

            # Keeping original direct string comparison
            if boxed_answer == seed.answer:
                printer.print("验证失败：模型能通过搜索回答", style="bold red")
                return False
            break # Original code broke here

        printer.print("验证通过：模型无法直接回答也无法通过搜索回答", style="bold green")
        return True

    async def query_update(self, method: str, queries: str, seed: Optional[QAItem]) -> QAItem: # Assuming queries is string based on method_choice
        if not seed:
             # Adding this check as it's logically necessary but was missing
             raise ValueError("Cannot update query without a seed QAItem")

        # Assuming queries is a newline-separated string or similar based on original context
        # Splitting queries string into a list for tavily_search
        query_list = [q.strip() for q in queries.split('\n') if q.strip()]
        if not query_list: # Handle empty queries string
            printer.print("Warning: No valid queries found in queries string. Using original question as query.", style="bold yellow")
            query_list = [seed.question]


        search_results = await asyncio.gather(*(tavily_search(q) for q in query_list))
        question_update_resp = agent.chat_with_template(
            template_name="abs_query_update.txt",
            template_data={"method": method, "search_results": search_results, "question": seed.question, "answer": seed.answer},
            root_folder=PROMPT_ROOT_FOLDER,
        )
        # 提取出update之后的question
        # Keeping original extraction logic
        updated_item = extract_and_validate_json(extract_tag_content(question_update_resp, "data"))
        updated_question = updated_item["updated_question"].strip()
        updated_evidence = updated_item.get("updated_evidence", [])

        printer.rule("Query Update Output")
        printer.print(pretty_json(updated_item), style="bold green")
        printer.rule("Query Update Evidence")
        printer.print(pretty_json(updated_evidence), style="bold green")

        # Keeping original evidence combination logic
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
        queries = [] # Initialize queries here
        random_domain = self.random_domain() # Moved up to be available for logging if needed
        for attempt in range(1, max_query_retries + 1):
            # Keeping original logic for generating queries
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
            # Add a small delay if retrying (optional but good practice)
            # await asyncio.sleep(0.5)
        else:
            # Keeping original RuntimeError
            raise RuntimeError("连续 3 次 Extracted Queries 为空，终止执行")

        # Keeping original search and seed fact generation logic
        search_results = await asyncio.gather(*(tavily_search(q) for q in queries))

        seed_fact_resp = extract_and_validate_json(agent.chat_with_template(
            template_name="seed_idea_from_internet.txt",
            template_data={"domain": random_domain,"search_results": search_results,},
            root_folder=PROMPT_ROOT_FOLDER
        ))
        printer.rule(f"Generate Seed Fact Output after Browse in {random_domain}")
        printer.print(pretty_json(seed_fact_resp), style="bold green")
        # Keeping original QAItem creation
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
        # Seed 生成
        try:
            seed = await self.generate_seed()
            self.items.append(seed)
            current = seed
        except Exception as e:
            # Keeping original exception logging and return
            logger.exception("Error in generate_seed")
            printer.print(f"Error in generate_seed: {e}", style="bold red")
            return

        # 按照 max_level 和 max_tries 进行多级问题升级
        for level in range(self.max_level):
            retries = 0
            # Using a flag to break outer loop, similar logic to original 'else' on inner loop
            level_update_successful = False
            while retries < self.max_tries:
                retries += 1
                printer.rule(f"Level {level+1} Update Attempt {retries}")
                try:
                    # Keeping original method choice and update logic
                    method, queries = self.method_choice(current.question, current.answer)
                    # Keeping original random method override logic
                    method = random.choice([method, "simple abstraction"])
                    updated = await self.query_update(method, queries, current)
                    passed = await self.multi_verify(updated)
                except Exception as e:
                    # Keeping original exception handling for the update process
                    logger.exception(f"Error in level {level+1} attempt {retries}")
                    printer.print(f"Error in update process: {e}", style="bold red")
                    continue # Continue to next retry

                # Keeping original verification check logic
                if not passed:
                    printer.print("多重校验未通过（模型能回答），重试 query_update …", style="bold red")
                    continue # Continue to next retry

                # Keeping original success logic
                printer.print("多重校验通过（模型无法回答），记录更新后的 QAItem", style="bold green")
                self.items.append(updated)
                current = updated
                level_update_successful = True # Mark level as successful
                break # Break retry loop

            # If after all retries the level wasn't updated successfully
            if not level_update_successful:
                printer.print(f"Stopped at level {current.level}; no valid update after {self.max_tries} tries.", style="bold red")
                return # Stop the entire workflow run

        printer.rule("Workflow End")

    async def entity_decompose_run(self):
        
        pass

    def save(self, path: Path):
        # Keeping original save logic exactly
        printer.rule("Saving Results")
        with file_lock:
            existing = []
            if path.exists():
                 # Check for empty file before loading JSON
                if path.stat().st_size > 0:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                            # Add check if loaded data is actually a list
                            if not isinstance(existing, list):
                                logger.warning(f"Existing file {path} did not contain a list. Overwriting.")
                                existing = []
                    except json.JSONDecodeError:
                        logger.error(f"Could not decode JSON from existing file {path}. Overwriting.")
                        existing = []
                    except Exception as e:
                        logger.exception(f"Error reading existing file {path}. Overwriting.")
                        existing = []
                else:
                    logger.info(f"Existing file {path} is empty. Starting fresh list.")

            existing.extend([it.to_dict() for it in self.items])
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)
                # Original print statement:
                printer.print(f"Saved {len(self.items)} items to {path}", style="bold green")
                printer.rule("Saved JSON Preview")
                printer.print(pretty_json([it.to_dict() for it in self.items]), style="bold cyan")
            except Exception as e:
                 logger.exception(f"Error writing JSON to {path}")
                 printer.print(f"Error saving results to {path}: {e}", style="bold red")


    # Keeping original _safe_json method (even if unused)
    @staticmethod
    def _safe_json(text: str) -> dict:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        raw = m.group(1) if m else text
        raw = raw.strip("`\n ")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
             # Original didn't log error here, just returned {}
             return {} # Return empty dict on failure


    # Keeping original GPT-Search methods exactly
    # 恢复 GPT-Search 专用的 Seed 生成
    async def gpt_search_generate_seed(self, domain) -> QAItem:
        """Stub for GPT Search seed generation."""
        # TODO: 实现 GPT Search 专用的 seed 生成逻辑
        resp = agent.chat_with_template(
            template_name="gpt_search_seed.txt",
            root_folder=PROMPT_ROOT_FOLDER,
            template_data={"domain": domain},
        )
        printer.rule("GPT-Search Seed Generation Output")
        printer.print(resp, style="bold green")

        json_resp = extract_and_validate_json(resp)
        if not json_resp:
            raise RuntimeError("GPT-Search seed generation failed")
        return QAItem(
            level=0,
            question=json_resp["seed"]["question"].strip(),
            answer=json_resp["seed"]["answer"].strip(),
            constrained_format=json_resp["seed"].get("constrained_format", ""),
            parent_question=None,
            evidence=json_resp["seed"].get("evidence", []),
            strategy="seed",
        )

    # 恢复 GPT-Search 专用的 Query 更新
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
        updated_question = json_resp["updated_question"].strip()
        updated_evidence = json_resp.get("updated_evidence", [])
        method = json_resp.get("method", "None")
        printer.rule("GPT-Search Query Update Output")
        printer.print(pretty_json(json_resp), style="bold green")
        printer.rule("GPT-Search Query Update Evidence")
        printer.print(pretty_json(updated_evidence), style="bold green")
        return QAItem(
            level=seed.level + 1,
            question=updated_question,
            answer=seed.answer,
            constrained_format=seed.constrained_format,
            parent_question=seed.question,
            evidence=seed.evidence + updated_evidence,
            strategy=method,
        )

    # GPT-Search 主流程入口
    async def gpt_search_run(self):
        GPT_MODEL = "gpt-4o-search-preview" # Original code set this here
        printer.rule(f"GPT-Search Workflow Start with {GPT_MODEL}")
        # Seed 生成
        try:
            seed = await self.gpt_search_generate_seed(self.random_domain())
            self.items.append(seed)
            current = seed
        except Exception as e:
            logger.exception("Error in gpt_search_generate_seed")
            printer.print(f"Error in gpt_search_generate_seed: {e}", style="bold red")
            return

        # 多级升级
        for level in range(self.max_level):
            retries = 0
            # Using a flag similar to run() method for consistency with original logic flow
            level_update_successful_gs = False
            while retries < self.max_tries:
                retries += 1
                printer.rule(f"GPT-Search Level {level+1} Update Attempt {retries}")
                try:
                    updated = await self.gpt_search_query_update(current)
                    passed = await self.multi_verify(updated)
                except Exception as e:
                    logger.exception(f"Error in GPT-Search level {level+1} attempt {retries}")
                    printer.print(f"Error in GPT-Search update: {e}", style="bold red")
                    continue

                if not passed:
                    printer.print("GPT-Search: 多重校验未通过（模型能回答），重试 query_update …", style="bold red")
                    continue

                printer.print("GPT-Search: 多重校验通过（模型无法回答），记录更新后的 QAItem", style="bold green")
                self.items.append(updated)
                current = updated
                level_update_successful_gs = True
                break # Break retry loop

            if not level_update_successful_gs:
                printer.print(
                    f"GPT-Search stopped at level {current.level}; no valid update after {self.max_tries} tries.",
                    style="bold red",
                )
                return

        printer.rule("GPT-Search Workflow End")

# Keeping original standalone random_domain function
def random_domain():
    domains = ["TV shows & movies", "Other", "Science & technology", "Art", "History", "Sports", "Music", "Video games", "Geography", "Politics"]
    return random.choice(domains)

def find_all_wrong_items(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    返回所有模型都答错的条目映射（question -> entry）。
    判定：除 GroundTruth 和 constrained_format 外，
    若所有其它字段中的 'is_correct' 都为 False，则认为此条目全部答错。
    """
    wrong_items: Dict[str, Dict[str, Any]] = {}
    for q, entry in data.items():
        # 收集所有模型字段
        model_fields = [v for k, v in entry.items() if k not in ("GroundTruth", "constrained_format")]
        # 若至少有一个模型且全部 is_correct=False
        if model_fields and all(not m.get("is_correct", False) for m in model_fields if isinstance(m, dict)):
            wrong_items[q] = entry
    return wrong_items

# --- Modified evaluate function for concurrency & search model override ---
def evaluate(
    json_file: Path = Path("trace_data.json"),
    use_cache: bool = True,
    cache_file: Path | None = None,
    eval_concurrency: int = 10,
    search_model: str = "gpt-4o-search-preview",  # Added search_model parameter
    level: Optional[int] = None                 
):
    """
    Evaluate level-5 items in a JSON trace, using concurrency for LLM calls.
    Stores results per model in the cache.

    - json_file: 待评估的 trace JSON 路径
    - use_cache: 是否启用缓存
    - cache_file: 缓存文件路径，默认与 json_file 同目录，名为 "<stem>_eval_cache.json"
    - eval_concurrency: Max concurrent evaluations.
    - search_model: Model to use for evaluation LLM calls. This model name is used as the key in the cache.
    - level: 指定评估的 level，若为 None 则评估所有记录。
    """
    printer.print(f"Evaluation using model: {search_model}", style="bold cyan")

    if cache_file is None:
        cache_file = json_file.parent / f"{json_file.stem}_eval_cache.json"

    # --- Load Cache ---
    cache: Dict[str, Dict[str, Any]] = {}
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for q, models in raw.items():
                    if isinstance(models, dict):
                        cache[q] = {}
                        for m, val in models.items():
                            if m == "GroundTruth":
                                cache[q]["GroundTruth"] = val
                            elif isinstance(val, dict):
                                cache[q][m] = val
                            elif isinstance(val, bool):
                                cache[q][m] = {"is_correct": val, "prediction": ""}
                            else:
                                logger.warning(f"Ignoring invalid cache value for {q}/{m}")
            else:
                logger.warning(f"Cache file {cache_file} invalid, resetting")
                cache = {}
        except Exception:
            logger.exception("Error loading cache, resetting")
            cache = {}

    # --- Load Records ---
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)
            if not isinstance(records, list):
                 printer.print(f"Error: Evaluation file {json_file} does not contain a JSON list.", style="bold red")
                 return
    except FileNotFoundError:
        printer.print(f"Error: Evaluation file not found: {json_file}", style="bold red")
        return
    except json.JSONDecodeError:
        printer.print(f"Error: Could not decode JSON from evaluation file: {json_file}", style="bold red")
        return
    except Exception as e:
        logger.exception(f"Error reading evaluation file {json_file}: {e}")
        printer.print(f"Error reading evaluation file {json_file}: {e}", style="bold red")
        return

    # --- Filter and Prepare Items ---
    if level is None:
        items_to_evaluate = [r for r in records if isinstance(r, dict)]
    else:
        items_to_evaluate = [r for r in records if isinstance(r, dict) and r.get("level") == level]
    total_items = len(items_to_evaluate)
    if total_items == 0:
        printer.print(f"No items{' of level '+str(level) if level is not None else ''} found in {json_file}.", style="yellow")
        return

    item_map = {item['question'].strip().lower(): item for item in items_to_evaluate}

    # 在构建 item_map 之后，确保 cache 里有 constrained_format
    for key, item in item_map.items():
        if key in cache:
            # 如果 cache[key] 中没有 constrained_format，就补上
            if 'constrained_format' not in cache[key]:
                cache[key]['constrained_format'] = item.get('constrained_format', '')
                logger.info(f"补充 cache 中缺失的 constrained_format: {key} -> {cache[key]['constrained_format']}")

    items_needing_eval: List[Dict] = []
    items_found_in_cache_for_this_model = correct_in_cache_for_this_model = 0

    for item in items_to_evaluate:
        if "question" not in item or "answer" not in item:
            printer.print(f"Skipping record due to missing keys: {item}", style="yellow")
            continue # Skip malformed records

        key = item['question'].strip().lower()

        if use_cache and key in cache and search_model in cache[key]:
            entry = cache[key][search_model]
            items_found_in_cache_for_this_model += 1
            if entry.get("is_correct"):
                correct_in_cache_for_this_model += 1
            # 打印缓存预测
            pred = entry.get("prediction", "")
            printer.print(f"[Cache] Q: {key}  Pred: {pred}", style="dim")
        else:
            if key not in {i['question'].strip().lower() for i in items_needing_eval}:
                items_needing_eval.append(item)

    printer.print(f"Total items found: {total_items}")
    printer.print(f"Items found in cache for model '{search_model}': {items_found_in_cache_for_this_model} ({correct_in_cache_for_this_model} correct)")
    printer.print(f"Items needing evaluation by model '{search_model}' (LLM call): {len(items_needing_eval)}")

    # --- Worker Function ---
    def evaluate_item_worker(item: Dict, worker_search_model: str) -> Tuple[str, bool, str, str]:
        """Worker function to evaluate a single item using LLM."""
        q = item["question"]
        ans_true = item["answer"]
        constrained_format = item.get("constrained_format", "")
        key = q.strip().lower()
        is_correct = False

        prompt = (
            f"{FORMAT_INSTRUCTION}\nPlease answer the following question and return it strictly in the \\boxed{{...}} format.\n"
            f"For the answer you provided in \\boxed{{}}, this answer must follow this format: {constrained_format}\n"
            "If you cannot answer, please generate \\boxed{Sorry, I don't know.}\n"
            f"Question: {q}\n"
        )
        try:
            resp = agent.chat(prompt, model=worker_search_model)
            ans_pred = extract_boxed_content(resp)

            # 打印出GT answer 和preidct answer
            printer.print(f"Evaluating Question: {q}")
            printer.print(f"GT Answer: {ans_true}", style="bold red")
            printer.print(f"Predicted Answer: {ans_pred}", style="bold green")  

            if ans_pred:
                 ans_pred_norm = "".join(c for c in ans_pred.strip().lower() if c.isalnum() or c.isspace())
                 ans_true_norm = "".join(c for c in ans_true.strip().lower() if c.isalnum() or c.isspace())
                 is_correct = (ans_pred_norm == ans_true_norm)
                

        except Exception as e:
            logger.exception(f"Error during evaluation LLM call for Q: {q} using model {worker_search_model}")
            printer.print(f"Error evaluating question {q} with model {worker_search_model}: {e}", style="bold red")
            is_correct = False

        return key, is_correct, ans_pred, ans_true

    # --- Concurrent Execution ---
    newly_evaluated: Dict[str, Dict[str, Any]] = {}
    correct_newly_evaluated: int = 0

    if items_needing_eval:
        printer.rule(f"Running {len(items_needing_eval)} evaluations concurrently (max {eval_concurrency}) for model '{search_model}'...")
        with ThreadPoolExecutor(max_workers=eval_concurrency) as executor:
            # Pass the specified search_model to the worker
            future_to_item = {executor.submit(evaluate_item_worker, item, search_model): item for item in items_needing_eval}

            processed_count = 0
            for future in as_completed(future_to_item):
                key, ok, ans_pred, ans_true = future.result()
                # 同时保存预测和正确答案
                newly_evaluated[key] = {
                    "is_correct": ok,
                    "prediction": ans_pred,
                    "answer": ans_true
                }
                if ok:
                    correct_newly_evaluated += 1
                if processed_count % 10 == 0 or processed_count == len(items_needing_eval):
                     printer.print(f"  Evaluated {processed_count}/{len(items_needing_eval)}...", style="dim")

    # --- Combine Results & Save Cache ---
    if use_cache:
        for key, res in newly_evaluated.items():
            if key not in cache:
                cache[key] = {}
            # 保存 GroundTruth
            cache[key]["GroundTruth"] = res["answer"]
            # 保存 constrained_format
            cache[key]["constrained_format"] = item_map.get(key, {}).get("constrained_format", "")
            # 各模型结果放在模型名下
            cache[key][search_model] = {
                "is_correct": res["is_correct"],
                "prediction": res["prediction"]
            }
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            printer.print(f"Cache updated and saved to {cache_file}", style="dim")
        except Exception as e:
             logger.exception(f"Error saving cache file {cache_file}: {e}")
             printer.print(f"Error saving cache file {cache_file}: {e}", style="red")

    # --- Final Report ---
    total_correct_for_this_model = correct_in_cache_for_this_model + correct_newly_evaluated
    total_evaluated_for_this_model = items_found_in_cache_for_this_model + len(newly_evaluated)
    acc = total_correct_for_this_model / total_evaluated_for_this_model if total_evaluated_for_this_model else 0.0
    printer.rule(f"Evaluation Results for Model: {search_model}")
    printer.print(f"Total items considered: {total_items}", style="bold")
    printer.print(f"Total items evaluated for '{search_model}' (cache + new): {total_evaluated_for_this_model}", style="bold")
    printer.print(f"Correct predictions for '{search_model}': {total_correct_for_this_model}", style="bold")
    printer.print(f"Accuracy for '{search_model}': {acc:.4%}", style="bold green")

async def test_fuzzy_replacement():
    """Test the fuzzy_replacement prompt with some example inputs."""
    test_cases = ["全球"]
    
    printer.rule("Testing Fuzzy Replacement")
    for test_input in test_cases:
        try:
            result = agent.chat_with_template(
                template_name="fuzzy_replacement.txt",
                template_data={"input": test_input},
                root_folder=PROMPT_ROOT_FOLDER,
                model="gpt-4o"
            )
            parsed_result = extract_and_validate_json(result)
            printer.print(f"\nInput: {test_input}", style="bold yellow")
            printer.print(f"Output: {parsed_result}", style="bold green")
        except Exception as e:
            printer.print(f"Error processing {test_input}: {e}", style="bold red")
            logger.exception(f"Error in fuzzy replacement test for input: {test_input}")

async def test_entity_extraction():
    """Test the entity_extraction prompt with example inputs."""
    test_cases = [
        "The CEO of Apple Inc. in 2024 is Tim Cook.",
        "2020年东京奥运会最终在2021年举行。",
        "习近平是中国国家主席。",
        "The Eiffel Tower is located in Paris, France.",
        "2022年北京冬奥会由中国举办。",
        "Elon Musk founded SpaceX in 2002.",
        "2023年诺贝尔文学奖得主是一位非洲作家。",
        "The capital of Japan is Tokyo.",
        "2021年7月，河南遭遇严重洪灾。",
        "Barack Obama served as the U.S. president from 2009 to 2017.",
        "2024年11月，美国将举行总统大选。",
        "Harry Potter was written by J.K. Rowling.",
        "The COVID-19 pandemic began in late 2019.",
        "乔丹是NBA历史上最伟大的球员之一。",
        "The United Nations was founded in 1945.",
        "2023年杭州亚运会吸引了数千名运动员参与。",
        "The Great Wall of China can be seen from space, though it's a myth.",
        "2022年，俄罗斯与乌克兰爆发冲突。",
        "Albert Einstein was awarded the Nobel Prize in Physics in 1921.",
        "2023年5月，ChatGPT在全球范围内被广泛使用。",
    ]
    
    printer.rule("Testing Entity Extraction")
    for test_input in test_cases:
        try:
            result = agent.chat_with_template(
                template_name="entity_extraction.txt",
                template_data={"input": test_input},
                root_folder=PROMPT_ROOT_FOLDER,
                model="gpt-4o"
            )
            printer.print(f"\nInput: {test_input}", style="bold yellow")
            printer.print(f"Output: {result}", style="bold green")

            # 尝试解析JSON结果并格式化显示
            try:
                parsed_result = extract_and_validate_json(result)
                printer.print("\nParsed entities:", style="bold blue")
                for entity_type, entities in parsed_result.get("entities", {}).items():
                    if entities:  # 只显示非空的实体类型
                        printer.print(f"{entity_type}: {', '.join(entities)}")
            except json.JSONDecodeError:
                printer.print("Warning: Failed to parse JSON output", style="bold red")

        except Exception as e:
            printer.print(f"Error processing {test_input}: {e}", style="bold red")
            logger.exception(f"Error in entity extraction test for input: {test_input}")

async def test_combination_workflow(out_file: Path):
    """Test the combination of entity extraction and fuzzy replacement using seed generation."""
    printer.rule("Testing Combination Workflow")
    
    # 1. 使用 gpt_search_generate_seed 生成种子QA
    wf = ReverseUpgradeWorkflow()
    try:
        seed = await wf.gpt_search_generate_seed(wf.random_domain())
        printer.print(f"\nSeed Question: {seed.question}", style="dim underline")
        printer.print(f"Seed Answer: {seed.answer}", style="bold green")
        
        # 2. 对问题进行实体抽取
        result = agent.chat_with_template(
            template_name="entity_extraction.txt",
            template_data={"input": seed.question},
            root_folder=PROMPT_ROOT_FOLDER,
            model="gpt-4o"
        )
        
        parsed_entities = extract_and_validate_json(result)
        if not parsed_entities or "entities" not in parsed_entities:
            raise ValueError("Failed to extract entities from the seed question")

        # 3. 对每个实体进行模糊替换（并发处理）
        replacements = []
        entities_to_process = []
        for entity_type, entities in parsed_entities["entities"].items():
            if entity_type == "OTHER":
                continue
            entities_to_process.extend([(entity_type, entity) for entity in entities])
        
        def process_entity(args):
            entity_type, entity = args
            try:
                fuzzy_result = agent.chat_with_template(
                    template_name="fuzzy_replacement.txt",
                    template_data={"input": entity},
                    root_folder=PROMPT_ROOT_FOLDER,
                    model="gpt-4o-search-preview"
                )
                parsed_fuzzy = extract_and_validate_json(fuzzy_result)
                if parsed_fuzzy and "output" in parsed_fuzzy:
                    return {
                        "type": entity_type,
                        "original": entity,
                        "fuzzy": parsed_fuzzy["output"],
                        "evidence": parsed_fuzzy.get("evidence", [])
                    }
            except Exception as e:
                printer.print(f"Error processing fuzzy replacement for {entity}: {e}", style="bold red")
                return None
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(process_entity, entities_to_process))
            replacements = [r for r in results if r is not None]

        # 4. 生成草稿模糊问题
        fuzzy_question = seed.question
        for rep in replacements:
            fuzzy_question = fuzzy_question.replace(rep["original"], rep["fuzzy"])
            seed.evidence.extend(rep["evidence"])
        
        # 5. 准备最终问题润色的输入数据
        input_data = {
            "original": {
                "question": seed.question,
                "answer": seed.answer
            },
            "entities": parsed_entities["entities"],
            "replacements": replacements,
            "fuzzy_result": {
                "question": fuzzy_question,
                "answer": seed.answer,
                "constrained_format": seed.constrained_format,
                "evidence": seed.evidence,
                "strategy": "fuzzy_replacement"
            }
        }
        
        # 6. 进行最终问题润色
        final_result = agent.chat_with_template(
            template_name="entity_final_question.txt",
            template_data={"input_data": json.dumps(input_data, ensure_ascii=False)},
            root_folder=PROMPT_ROOT_FOLDER,
            model="o4-mini"
        )
        
        try:
            parsed_final = extract_and_validate_json(final_result)
            if parsed_final and "polished_question" in parsed_final:
                input_data["fuzzy_result"]["question"] = parsed_final["polished_question"]
        except Exception as e:
            printer.print(f"Error parsing final polish result: {e}", style="bold red")
        
        # 7. 将结果转换为 FuzzyQAItem
        fuzzy_item = FuzzyQAItem(
            original_question=seed.question,
            question=input_data["fuzzy_result"]["question"],
            answer=seed.answer,
            constrained_format=seed.constrained_format,
            strategy="fuzzy_replacement",
            evidence=input_data["fuzzy_result"]["evidence"]
        )

        # 8. 验证, 未通过则丢弃
        if not await verify_fuzzy_item(fuzzy_item):
            printer.print("核验未通过，丢弃此条结果", style="bold yellow")
            return None

        return fuzzy_item

    except Exception as e:
        printer.print(f"Error in combination workflow: {e}", style="bold red")
        logger.exception("Error in combination workflow")
        return None  # 返回 None 表示执行失败

def main():
    # Added --search_model argument
    parser = argparse.ArgumentParser(description="Generates or evaluates multi-level reverse-upgrade benchmark questions.")
    parser.add_argument("--out", type=Path, default=Path("trace_data.json"))
    parser.add_argument("--max_level", type=int, default=5)
    parser.add_argument("--max_tries", type=int, default=5)
    parser.add_argument("--batch", type=int, default=1, help="批量运行次数，>1 则追加写入同一文件")
    parser.add_argument("--concurrency", type=int, default=1, help="最大并行并发数 (for batch runs)")
    parser.add_argument("--model", type=str, default=None, help="LLM model name to use (for non-GPT-Search runs)")
    parser.add_argument("--evaluate", action="store_true", help="只运行 evaluate()，输出测试结果并退出")
    parser.add_argument("--eval_concurrency", type=int, default=10, help="最大并行并发数 (for --evaluate mode)")
    parser.add_argument("--search_model", type=str, default="gpt-4o-search-preview", help="Model to use for evaluation LLM calls")
    parser.add_argument("--eval_level", type=int, default=None, help="Specify level to evaluate; omit for all records")
    parser.add_argument("--test_fuzzy", action="store_true", help="运行 fuzzy replacement 测试")
    parser.add_argument("--test_entity", action="store_true", help="运行实体抽取测试")
    parser.add_argument("--test_combination", action="store_true", help="运行组合测试流程")
    parser.add_argument("--combination_batch", type=int, default=1, help="组合测试运行批次")
    parser.add_argument("--combination_concurrency", type=int, default=1, help="组合测试并发数")
    parser.add_argument("--combination_out", type=Path, default=Path("fuzzy_replacement_bench.json"), help="组合测试结果输出文件")
    
    args = parser.parse_args()

    # Keeping original model override logic
    if args.model:
        global GPT_MODEL
        GPT_MODEL = args.model
        printer.print(f"Using overridden model for generation runs: {GPT_MODEL}", style="bold yellow")

    # Add test branches
    if args.test_fuzzy:
        asyncio.run(test_fuzzy_replacement())
        return

    if args.test_entity:
        asyncio.run(test_entity_extraction())
        return

    if args.test_combination:
        printer.rule(f"Starting Combination Workflow: {args.combination_batch} instances with concurrency {args.combination_concurrency}")
        
        def _combination_batch():
            def sync_run_one_wrapper(idx: int):
                return asyncio.run(test_combination_workflow(args.combination_out))

            successful_results = []  # 存储成功执行的结果

            with ThreadPoolExecutor(max_workers=args.combination_concurrency) as executor:
                futures = {executor.submit(sync_run_one_wrapper, i): i 
                          for i in range(args.combination_batch)}
                for future in as_completed(futures):
                    try:
                        result = future.result()  # 获取执行结果
                        if result is not None:  # 只保存成功的结果
                            successful_results.append(result.to_dict())
                    except Exception as exc:
                        run_idx = futures[future] + 1
                        logger.exception(f"Combination run {run_idx} failed: {exc}")
                        printer.print(f"Combination run {run_idx} failed: {exc}", style="bold red")
                        continue  # 跳过失败的运行

            # 只有在有成功结果时才更新文件
            if successful_results:
                with file_lock:
                    existing = []
                    if args.combination_out.exists() and args.combination_out.stat().st_size > 0:
                        try:
                            with open(args.combination_out, "r", encoding="utf-8") as f:
                                existing = json.load(f)
                        except json.JSONDecodeError:
                            logger.error(f"Could not decode JSON from {args.combination_out}. Starting fresh.")
                        except Exception as e:
                            logger.exception(f"Error reading {args.combination_out}")

                    existing.extend(successful_results)
                    
                    try:
                        with open(args.combination_out, "w", encoding="utf-8") as f:
                            json.dump(existing, f, ensure_ascii=False, indent=2)
                        printer.print(f"Successfully saved {len(successful_results)} items to {args.combination_out}", style="bold green")
                    except Exception as e:
                        logger.exception(f"Error saving to {args.combination_out}")
                        printer.print(f"Error saving results: {e}", style="bold red")

            printer.print(f"Completed {args.combination_batch} combination runs", style="bold green")
            printer.print(f"Successfully processed: {len(successful_results)} items", style="bold green")
            printer.print(f"Failed: {args.combination_batch - len(successful_results)} items", style="bold yellow")
            printer.print(f"Results saved to: {args.combination_out}", style="bold green")
        
        _combination_batch()
        return

    # --- Evaluation Branch ---
    if args.evaluate:
        evaluate(
            json_file=args.out,
            use_cache=True,
            eval_concurrency=args.eval_concurrency,
            search_model=args.search_model,
            level=args.eval_level
        )
        return # Exit after evaluation

    # --- Single Run Branches (Unchanged) ---
    if args.gptsearch and args.batch <= 1:
        wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
        try:
            asyncio.run(wf.gpt_search_run())
        except Exception as e:
            logger.exception("Error in single gptsearch run")
            printer.print(f"Error during single gptsearch run: {e}", style="bold red")
        finally:
            try:
                wf.save(args.out)
                print(f"Saved {len(wf.items)} items to {args.out}")
            except Exception as e:
                logger.exception("Error saving results for single gptsearch run")
                printer.print(f"Error saving results: {e}", style="bold red")
        return

    if args.batch <= 1: # Handles non-gptsearch single run
        wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
        try:
            asyncio.run(wf.run())
        except Exception as e:
            logger.exception("Error in single run")
            printer.print(f"Error during single run: {e}", style="bold red")
        finally:
            try:
                wf.save(args.out)
                print(f"Saved {len(wf.items)} items to {args.out}")
            except Exception as e:
                logger.exception("Error saving results for single run")
                printer.print(f"Error saving results: {e}", style="bold red")
        return

    # --- Batch Run Branch (Using ThreadPoolExecutor - Confirmed uses args.concurrency) ---
    printer.rule(f"Starting Batch Run: {args.batch} instances with concurrency {args.concurrency}")
    # This function is now synchronous and uses ThreadPoolExecutor
    def _batch():
        # Define the async function exactly as it was in the original _batch
        async def run_one(idx: int):
            printer.rule(f"Batch Run {idx+1}/{args.batch}")
            wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
            try:
                # 根据标志选择流程
                if args.gptsearch:
                    await wf.gpt_search_run()
                else:
                    await wf.run()
                # 统一保存
                wf.save(args.out) # Save handles locking
                count = len(wf.items)
                printer.print(f"Batch[{idx+1}]: saved {count} items.", style="bold green")
                return [it.to_dict() for it in wf.items] # Original returned items
            except Exception as e:
                logger.exception(f"Error in batch run {idx+1}")
                printer.print(f"Error in batch run {idx+1}: {e}", style="bold red")
                 # Try to save partial results even on error
                try:
                     wf.save(args.out)
                     count = len(wf.items)
                     printer.print(f"Batch[{idx+1}]: saved {count} partial items after error.", style="yellow")
                except Exception as save_e:
                     logger.exception(f"Error saving partial results for batch {idx+1}: {save_e}")
                     printer.print(f"Error saving partial results for batch {idx+1}: {save_e}", style="red")
                return [] # Original returned empty list on error

        # Synchronous wrapper to call the async run_one using asyncio.run
        def sync_run_one_wrapper(idx: int):
            # Each thread needs its own event loop
            return asyncio.run(run_one(idx))

        # Use ThreadPoolExecutor to run the sync wrappers concurrently
        all_results = []
        # CONFIRMED: max_workers uses args.concurrency here
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {executor.submit(sync_run_one_wrapper, i): i for i in range(args.batch)}
            for future in as_completed(futures):
                try:
                    result = future.result() # Get result (list of dicts or empty list)
                    all_results.extend(result) # Collect results if needed (original gathered them)
                except Exception as exc:
                    run_idx = futures[future] + 1
                    logger.exception(f"Batch run {run_idx} failed in executor: {exc}")
                    printer.print(f'Batch run {run_idx} generated an exception: {exc}', style="bold red")

        # Original final print statement
        printer.print(f"Completed {args.batch} runs; file at {args.out}", style="bold green")

    # Call the synchronous _batch function directly
    _batch()


if __name__ == "__main__":
    main()
"""
%%%
## 跑数据
python -m criticsearch.abstract_substitution.abs_workflow --out trace_data.json --batch 20 --concurrency 20
python -m criticsearch.abstract_substitution.abs_workflow --out trace_data.json --batch 20 --concurrency 20 --model gpt-4o
python -m criticsearch.abstract_substitution.abs_workflow --out trace_data.json --max_level 3 --max_tries 2 --batch 2 --concurrency 3

## 跑数据--使用 GPT-Search workflow
python -m criticsearch.abstract_substitution.abs_workflow --batch 2 --concurrency 20 --gptsearch --out trace_data—1.json --max_level 2

## 批量评估
python -m criticsearch.abstract_substitution.abs_workflow --out fuzzy_replacement_bench_refined.json --evaluate --search_model gemini-2.0-flash-search --eval_concurrency 7
python -m criticsearch.abstract_substitution.abs_workflow --out fuzzy_replacement_bench.json --evaluate --search_model gpt-4o-search-preview --eval_concurrency 7

## 测试 fuzzy replacement
python -m criticsearch.abstract_substitution.abs_workflow --test_fuzzy

## 测试实体抽取
python -m criticsearch.abstract_substitution.abs_workflow --test_entity

## 测试组合流程
python -m criticsearch.abstract_substitution.abs_workflow --test_combination --combination_batch 5 --combination_concurrency 20 --combination_out bench0427.json
"""