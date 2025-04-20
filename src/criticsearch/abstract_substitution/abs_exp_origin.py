"""
reverse_upgrade_workflow.py
---------------------------------
Automates the five‑stage *reverse‑upgrade* benchmark‑creation procedure described in
《网页深度搜索(难题)出题规范》.  

High‑level flow
===============
1. **Seed generation** – ask an LLM to pick a domain it is interested in and to output
   a *difficult* seed fact (question + answer) together with supporting URLs.  
2. **Reverse upgrade loop** – up to `MAX_LEVEL` (=5) times do:
   • Generate a harder *equivalent/abstract* version of the previous question.  
   • Run two validators:
       a. *Knowledge validator* – ask the same LLM to answer directly.  
       b. *Search validator* – allow exactly **one** web search (Tavily) then ask for an answer.  
   • If both validators **fail**, keep the new item and continue.  Otherwise retry (≤ `MAX_TRIES`).
3. **Persist** all successfully validated questions (even intermediate ones) to a JSON
   file whose structure matches the spec.

The script can be run stand‑alone:
    $ python reverse_upgrade_workflow.py --out benchmarks.json
"""

import argparse
import asyncio
import json
import random
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- third‑party / platform helpers --------------------------------------------------
from criticsearch.base_agent import BaseAgent
from criticsearch.tools.search_adapter.search_aggregator import SearchAggregator
from criticsearch.tools.content_scraper.tavily_extract import TavilyExtract

TAVILY_API_KEY = "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"  # per user instruction

# -------------------------------------------------------------------------------------
# Regex helpers supplied by the user (lightly wrapped)
# -------------------------------------------------------------------------------------
BOXED_RE = re.compile(r"\\boxed{([^}]+)}")
ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL | re.IGNORECASE)
THOUGHT_TAG_RE = re.compile(r"<thought>(.*?)</thought>", re.DOTALL | re.IGNORECASE)


def extract_boxed(text: str) -> str:
    """Return content inside first \boxed{} pair or empty string."""
    m = BOXED_RE.search(text)
    return m.group(1).strip() if m else ""


def extract_answer_tag(text: str) -> str:
    """Return raw content of first <answer>…</answer> block."""
    m = ANSWER_TAG_RE.search(text)
    return m.group(1).strip() if m else ""


def extract_thought(text: str) -> str:
    m = THOUGHT_TAG_RE.search(text)
    return m.group(1).strip() if m else ""


# -------------------------------------------------------------------------------------
# Data containers
# -------------------------------------------------------------------------------------
@dataclass
class QAItem:
    level: int  # 0 = seed, 1‑5 upgraded
    question: str
    answer: str  # gold answer
    parent_question: Optional[str]
    support_urls: List[str]
    generated_by_model: str

    def to_dict(self):
        d = asdict(self)
        d["support_urls"] = list(self.support_urls)
        return d


# -------------------------------------------------------------------------------------
# Core workflow class
# -------------------------------------------------------------------------------------
class ReverseUpgradeWorkflow:
    def __init__(
        self,
        agent: BaseAgent,
        *,
        model: str = "gpt-4o",
        max_level: int = 5,
        max_tries: int = 5,
    ) -> None:
        self.agent = agent
        self.model = model
        self.max_level = max_level
        self.max_tries = max_tries
        self.search_aggregator = SearchAggregator()
        self.scraper = TavilyExtract(TAVILY_API_KEY)
        self.items: List[QAItem] = []

    # ------------------------------------------------------------------
    # Step 0 – get a seed fact
    # ------------------------------------------------------------------
    async def generate_seed(self) -> QAItem:
        seed_prompt = (
            "You are an expert benchmark designer. Pick **one** field you find fascinating and "
            "provide *one* DIFFICULT seed fact that cannot be answered by simply googling the fact "
            "verbatim, yet the answer is unique and verifiable from the web.  "
            "Return **ONLY** a JSON object with keys: question (string), answer (string), "
            "support_urls (array of URLs)."
        )
        response = self.agent.chat(usr_prompt=seed_prompt, model=self.model)
        payload = self._safe_json(response)
        return QAItem(
            level=0,
            question=payload["question"].strip(),
            answer=payload["answer"].strip(),
            parent_question=None,
            support_urls=payload.get("support_urls", []),
            generated_by_model=self.model,
        )

    # ------------------------------------------------------------------
    # Produce one harder version of *prev_item*
    # ------------------------------------------------------------------
    async def upgrade_question(self, prev_item: QAItem) -> QAItem:
        ug_prompt = (
            "You are improving benchmark difficulty by *reverse‑upgrading* the question below.\n\n"
            f"ORIGINAL_QUESTION:\n{prev_item.question}\n\n"
            "Perform **one** of: equivalent replacement, simple abstraction, OR complex abstraction + clarification, "
            "as defined in the spec.  The new question MUST still have the SAME definitive answer\n"
            f"(which is: {prev_item.answer!r}).\n"
            "Return **only** valid JSON with keys: new_question (string), support_urls (array, can reuse), "
            "strategy (string)."
        )
        response = self.agent.chat(usr_prompt=ug_prompt, model=self.model)
        payload = self._safe_json(response)
        return QAItem(
            level=prev_item.level + 1,
            question=payload["new_question"].strip(),
            answer=prev_item.answer,  # answer unchanged
            parent_question=prev_item.question,
            support_urls=payload.get("support_urls", prev_item.support_urls),
            generated_by_model=self.model,
        )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    async def knowledge_validator(self, question: str) -> bool:
        """True if model answers *correctly*."""
        k_prompt = (
            f"<question>{question}</question>\n"
            "Answer ONLY with: <answer>…</answer>, with the value wrapped in \\boxed{}.")
        reply = self.agent.chat(usr_prompt=k_prompt, model=self.model)
        ans_raw = extract_answer_tag(reply)
        predicted = extract_boxed(ans_raw)
        return predicted.strip() == self.items[0].answer  # gold in first item

    async def search_validator(self, question: str) -> bool:
        # use *one* search query (same as question) then LLM answer
        # 1. search
        search_results = await self.search_aggregator.search(query=[question])
        urls = [r.url for r in search_results[:3]]  # take a few
        # 2. grab content
        scraped = await self.scraper.extract_content(urls)
        corpus = "\n\n".join(s.get("raw_content", "") for s in scraped.values())
        # 3. ask LLM *with* context, forcing single turn
        s_prompt = (
            f"Refer ONLY to the context below (from at most one web search).\n"
            "<context>\n" + corpus[:4000] + "\n</context>\n"  # truncate if needed
            f"<question>{question}</question>\nAnswer with boxed value.")
        reply = self.agent.chat(usr_prompt=s_prompt, model=self.model)
        predicted = extract_boxed(extract_answer_tag(reply))
        return predicted.strip() == self.items[0].answer

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    async def run(self):
        # Seed phase
        seed_item = await self.generate_seed()
        self.items.append(seed_item)
        current = seed_item

        # iterative reverse‑upgrade
        for _ in range(self.max_level):
            tries = 0
            success = False
            while tries < self.max_tries and not success:
                tries += 1
                candidate = await self.upgrade_question(current)
                # 1st validator
                if await self.knowledge_validator(candidate.question):
                    continue  # knowledge too easy
                # 2nd validator
                if await self.search_validator(candidate.question):
                    continue  # one‑search too easy
                # both failed ⇒ accept
                self.items.append(candidate)
                current = candidate
                success = True
            if not success:
                print(f"Level {current.level+1} failed after {self.max_tries} retries; terminating trace.")
                break

    # ------------------------------------------------------------------
    def export(self, path: Path):
        with path.open("w", encoding="utf-8") as f:
            json.dump([it.to_dict() for it in self.items], f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_json(text: str) -> Dict[str, Any]:
        """Extract JSON from raw LLM text (handles fenced blocks)."""
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        raw = fence.group(1) if fence else text
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # fallback: strip backticks and retry
            raw2 = raw.replace("```", "").strip()
            return json.loads(raw2)


# -------------------------------------------------------------------------------------
# CLI entry‑point
# -------------------------------------------------------------------------------------

def cli():
    parser = argparse.ArgumentParser(description="Reverse‑upgrade benchmark generator")
    parser.add_argument("--out", type=Path, default=Path("trace.json"), help="output JSON file")
    parser.add_argument("--max_level", type=int, default=5)
    parser.add_argument("--max_tries", type=int, default=5)
    args = parser.parse_args()

    agent = BaseAgent()
    workflow = ReverseUpgradeWorkflow(
        agent,
        max_level=args.max_level,
        max_tries=args.max_tries,
    )
    asyncio.run(workflow.run())
    workflow.export(args.out)
    print(f"Saved {len(workflow.items)} QA levels to {args.out}")


if __name__ == "__main__":
    cli()
