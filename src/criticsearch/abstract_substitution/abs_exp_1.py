"""
reverse_upgrade_workflow.py (stand‑alone)
========================================
Generates multi‑level reverse‑upgrade benchmark questions without external packages.

Usage:
    python reverse_upgrade_workflow.py --out trace.json
Dependencies:
    pip install openai httpx beautifulsoup4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI
from bs4 import BeautifulSoup
from criticsearch.config import settings

# === Constants & API Keys ===
GPT_MODEL = getattr(settings, "default_model", "gpt-4o")
GPT_API_KEY = settings.models[GPT_MODEL].get("api_key")
GPT_BASE_URL = settings.models[GPT_MODEL].get("base_url")
MAX_TOKENS = settings.models[GPT_MODEL].get("max_tokens", 1024)

TAVILY_API_KEY = settings.tavily.api_key
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"

# === OpenAI LLM Call Helper ===
def call_llm(
    prompt: str,
    *,
    model: str = GPT_MODEL,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
) -> str:
    """Call OpenAI chat completion (stand‑alone)."""
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
    return resp.choices[0].message.content

# === Tavily Search & Extract ===
async def tavily_search(query: str, *, include_raw_content: bool = True) -> List[dict]:
    payload = {"query": query, "include_raw_content": include_raw_content, "api_key": TAVILY_API_KEY}
    async with httpx.AsyncClient(http2=True, timeout=30) as client:
        r = await client.post(TAVILY_SEARCH_URL, json=payload)
    time.sleep(0.1)
    return r.json().get("results", [])

async def tavily_extract(urls: List[str]) -> Dict[str, dict]:
    async with httpx.AsyncClient(http2=True, timeout=30) as client:
        r = await client.post(
            TAVILY_EXTRACT_URL,
            json={"urls": urls},
            headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
        )
    return r.json()

async def fallback_scrape(urls: List[str]) -> Dict[str, str]:
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
    return {u: t for u, t in zip(urls, texts)}

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
    support_urls: List[str]
    strategy: str

    def to_dict(self) -> dict:
        return asdict(self)

# === Workflow ===
class ReverseUpgradeWorkflow:
    def __init__(self, *, max_level: int = 5, max_tries: int = 5):
        self.max_level = max_level
        self.max_tries = max_tries
        self.items: List[QAItem] = []

    async def generate_seed(self) -> QAItem:
        prompt = (
            "You are an expert benchmark designer. Pick one field that fascinates you "
            "and output one difficult seed QA fact (cannot be answered by simply googling) "
            "with a unique verifiable answer.\n\n"
            "Return only JSON: {\"question\": ..., \"answer\": ..., \"support_urls\": [...]}"
        )
        resp = call_llm(prompt)
        payload = self._safe_json(resp)
        return QAItem(
            level=0,
            question=payload["question"].strip(),
            answer=payload["answer"].strip(),
            parent_question=None,
            support_urls=payload.get("support_urls", []),
            strategy="seed",
        )

    async def upgrade_once(self, prev: QAItem) -> QAItem:
        prompt = (
            "Reverse-upgrade the benchmark question according to spec.\n"
            f"Original: {prev.question}\nAnswer: {prev.answer}\n\n"
            "Perform one of: equivalent replacement, simple abstraction, or complex abstraction+info.\n"
            "Return JSON: {\"new_question\": ..., \"support_urls\": [...], \"strategy\": ...}"
        )
        resp = call_llm(prompt)
        pl = self._safe_json(resp)
        return QAItem(
            level=prev.level + 1,
            question=pl["new_question"].strip(),
            answer=prev.answer,
            parent_question=prev.question,
            support_urls=pl.get("support_urls", prev.support_urls),
            strategy=pl.get("strategy", "unknown"),
        )

    async def knowledge_validator(self, question: str, gold: str) -> bool:
        prompt = f"<question>{question}</question>\nAnswer with boxed value only inside <answer>."
        resp = call_llm(prompt, temperature=0)
        pred = extract_boxed(extract_answer_tag(resp))
        return pred == gold

    async def search_validator(self, question: str, gold: str) -> bool:
        results = await tavily_search(question)
        urls = [r.get("url") for r in results[:3] if r.get("url")]
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
        ctx = "\n\n".join(texts)[:4000]
        prompt = f"<context>{ctx}</context>\n<question>{question}</question>\nAnswer with boxed value."
        resp = call_llm(prompt, temperature=0)
        pred = extract_boxed(extract_answer_tag(resp))
        return pred == gold

    async def run(self):
        seed = await self.generate_seed()
        self.items.append(seed)
        current = seed
        for _ in range(self.max_level):
            retries = 0
            while retries < self.max_tries:
                retries += 1
                candidate = await self.upgrade_once(current)
                if await self.knowledge_validator(candidate.question, candidate.answer):
                    continue
                if await self.search_validator(candidate.question, candidate.answer):
                    continue
                self.items.append(candidate)
                current = candidate
                break
            else:
                print(f"Stopped at level {current.level}; no valid upgrade after {self.max_tries} tries.")
                break

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([it.to_dict() for it in self.items], f, ensure_ascii=False, indent=2)

    @staticmethod
    def _safe_json(text: str) -> dict:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        raw = m.group(1) if m else text
        raw = raw.strip("`\n ")
        return json.loads(raw)


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
