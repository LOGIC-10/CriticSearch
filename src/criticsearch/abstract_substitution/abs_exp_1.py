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
    printer.rule("Tavily Search Query")
    printer.print(query, style="bold yellow")
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

    async def generate_seed(self) -> QAItem:
        random_domain = self.random_domain()
        query_resp = agent.chat_with_template(template_name="search_query_for_seed_fact.txt",template_data={"domain": random_domain}, root_folder=PROMPT_ROOT_FOLDER)
        # 提取第一次为了domain seed搜索的query并直接调用搜索工具获得搜索结果
        queries = extract_queries_from_response(query_resp)
        printer.rule("Extracted Queries")
        printer.print(queries, style="bold cyan")
        search_results = await asyncio.gather(*(tavily_search(q) for q in queries))

        seed_fact_resp = extract_and_validate_json(agent.chat_with_template(template_name="seed_idea_from_internet.txt",template_data={"domain": random_domain,"search_results": search_results,}, root_folder=PROMPT_ROOT_FOLDER))
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

    async def upgrade_once(self, prev: QAItem) -> QAItem:
        prompt = (
            "Reverse-upgrade the benchmark question according to spec.\n"
            f"Original: {prev.question}\nAnswer: {prev.answer}\n\n"
            "Perform one of: equivalent replacement, simple abstraction, or complex abstraction+info.\n"
            "Return JSON: {\"new_question\": ..., \"support_urls\": [...], \"strategy\": ...}"
        )
        printer.rule(f"Upgrade Prompt (Level {prev.level + 1})")
        printer.print(prompt, style="bold yellow")
        resp = call_llm(prompt)
        printer.rule(f"Upgrade LLM Output (Level {prev.level + 1})")
        printer.print(resp, style="bold green")
        pl = self._safe_json(resp)
        printer.rule(f"Parsed Upgrade JSON (Level {prev.level + 1})")
        printer.print(pretty_json(pl), style="bold cyan")
        return QAItem(
            level=prev.level + 1,
            question=pl["new_question"].strip(),
            answer=prev.answer,
            parent_question=prev.question,
            evidence=pl.get("support_urls", prev.evidence),
            strategy=pl.get("strategy", "unknown"),
        )

    async def knowledge_validator(self, question: str, gold: str) -> bool:
        prompt = f"<question>{question}</question>\nAnswer with boxed value only inside <answer>."
        printer.rule("Knowledge Validator Prompt")
        printer.print(prompt, style="bold yellow")
        resp = call_llm(prompt, temperature=0)
        printer.rule("Knowledge Validator LLM Output")
        printer.print(resp, style="bold green")
        pred = extract_boxed(extract_answer_tag(resp))
        printer.print(f"Extracted Boxed: {pred}", style="bold cyan")
        return pred == gold

    async def search_validator(self, question: str, gold: str) -> bool:
        printer.rule("Search Validator - Question")
        printer.print(question, style="bold yellow")
        results = await tavily_search(question)
        urls = [r.get("url") for r in results[:3] if r.get("url")]
        printer.print(f"Top URLs: {urls}", style="bold cyan")
        if not urls:
            return False
        ext = await tavily_extract(urls)
        texts: List[str] = []
        for u in urls:
            raw = ext.get(u, {}).get("raw_content", "")
            if not raw:
                scraped = await fallback_scrape([u])
                raw = scraped.get(u, "")
            texts.append(raw)
        ctx = "\n\n".join(texts)[:40000]
        printer.rule("Search Validator - Context")
        printer.print(ctx, style="dim")
        prompt = f"<context>{ctx}</context>\n<question>{question}</question>\nAnswer with boxed value."
        printer.rule("Search Validator Prompt")
        printer.print(prompt, style="bold yellow")
        resp = call_llm(prompt, temperature=0)
        printer.rule("Search Validator LLM Output")
        printer.print(resp, style="bold green")
        pred = extract_boxed(extract_answer_tag(resp))
        printer.print(f"Extracted Boxed: {pred}", style="bold cyan")
        return pred == gold

    async def run(self):
        printer.rule("Workflow Start")
        seed = await self.generate_seed()
        exit(1)
        self.items.append(seed)
        current = seed
        for _ in range(self.max_level):
            retries = 0
            while retries < self.max_tries:
                retries += 1
                printer.rule(f"Upgrade Attempt {retries} (Level {current.level + 1})")
                candidate = await self.upgrade_once(current)
                if await self.knowledge_validator(candidate.question, candidate.answer):
                    printer.print("Knowledge validator failed, retrying...", style="bold red")
                    continue
                if await self.search_validator(candidate.question, candidate.answer):
                    printer.print("Search validator failed, retrying...", style="bold red")
                    continue
                self.items.append(candidate)
                current = candidate
                printer.print(f"Upgrade success at level {current.level}", style="bold green")
                break
            else:
                printer.print(f"Stopped at level {current.level}; no valid upgrade after {self.max_tries} tries.", style="bold red")
                break
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
    parser.add_argument("--out", type=Path, default=Path("trace.json"))
    parser.add_argument("--max_level", type=int, default=5)
    parser.add_argument("--max_tries", type=int, default=5)
    args = parser.parse_args()
    wf = ReverseUpgradeWorkflow(max_level=args.max_level, max_tries=args.max_tries)
    asyncio.run(wf.run())
    wf.save(args.out)
    print(f"Saved {len(wf.items)} items to {args.out}")

if __name__ == "__main__":
    main()
