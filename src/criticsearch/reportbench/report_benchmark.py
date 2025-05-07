# %% [markdown]
# # ReportBenchmark Notebook
# 本 Notebook 包含报告评估相关的代码单元, 后面需要移除

# %%
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from typing import Any, Optional
from criticsearch import utils
from criticsearch.rich_output import printer
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed
from criticsearch.base_agent import BaseAgent
from criticsearch.reportbench.extract_ground_truth import (
    extract_markdown_sections,
    extractDirectoryTree,
    extractMarkdownContent,
    extractSectionContentPairs,
)

from criticsearch.utils import count_tokens
from criticsearch.utils import extract_and_validate_json
from criticsearch.utils import (
    extract_tag_content,
    extract_answer_from_response,
    extract_boxed_content,
)
from criticsearch.config import settings
import os
from pathlib import Path
import hashlib
import sys
from tqdm import tqdm

# 在文件顶部添加：对模型调用 + JSON 解析 做重试
@retry(stop=stop_after_attempt(settings.max_retries), wait=wait_fixed(1), reraise=True)
def safe_chat_and_parse(agent, prompt: str, model: str):
    """
    调用 LLM 并解析返回的 JSON。解析失败会重试至 settings.max_retries。
    """
    response = agent.chat(usr_prompt=prompt, model=model)
    return extract_and_validate_json(response)

# %% [markdown]
# ## ReportBenchmark Class Definition


# %%
class ReportBenchmark:
    """
    A benchmarking class for generating report evaluations.
    Builds ground truths for report breadth & depth using two modules,
    and calls prompts (fact_extraction, outline_generation) via BaseAgent's common_chat.
    Also includes a method for FactualQA evaluation using a model (e.g., GPT-4o).
    """

    def __init__(self, json_input_path, user_query=None):
        self.json_path = json_input_path
        self.agent = BaseAgent()
        self.breadth_gt = extractDirectoryTree(
            self.json_path
        )  # Extract breadth ground truth，得到一个json结构的广度树
        self.article_content = extractMarkdownContent(self.json_path)
        self.sections = extract_markdown_sections(self.article_content)
        self.section_content_pairs = extractSectionContentPairs(json_input_path)
        self.user_query = (
            f"Generate a comprehensive long report about {self.breadth_gt.get('title', '')}"
            if user_query is None
            else user_query
        )
        # 添加缓存相关的属性
        self.cache_dir = Path("cache/benchmark_results")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self):
        """生成缓存文件的唯一标识"""
        # 使用输入文件路径和查询作为缓存key的基础
        content = f"{self.json_path}_{self.user_query}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_from_cache(self) -> Optional[Any]:
        """Load results from cache if available and non-empty."""
        cache_file = self.cache_dir / f"{self._get_cache_key()}.json"
        if not cache_file.exists() or cache_file.stat().st_size == 0:
            printer.print(f"Cache file {cache_file} is missing or empty.")
            return None
        with cache_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
        # 如果缓存内容是空列表，也视为无效
        if isinstance(data, list) and not data:
            printer.print(f"Cache file {cache_file} contains an empty list.")
            return None
        return data

    def _save_to_cache(self, results: Any) -> None:
        """Save results to cache."""
        cache_file = self.cache_dir / f"{self._get_cache_key()}.json"
        with cache_file.open('w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def sliding_window_pairing(self, max_token_length=2000):
        """
        创建 section 内容的滑动窗口，尽可能在 token 限制内合并更多的 section。
        
        Args:
            max_token_length: 每个窗口的最大 token 数量
            
        Returns:
            List[Dict]: 一个包含合并窗口的列表，每个窗口包含最高级标题、合并内容、路径等信息
        """
        # 首先提取所有 section 的标题和内容
        sections = []
        
        def extract_sections(data, path=[], depth=0):
            """递归提取所有 section 的标题、内容、深度和路径"""
            if isinstance(data, dict):
                # 如果是直接的字典对象
                title = data.get('title', '')
                content = data.get('content', '')
                
                # 获取正确的层级深度
                current_depth = depth + 1  # 默认深度加1
                # 如果数据中有明确的id，我们可以从id解析深度
                section_id = data.get('id', '')
                if section_id and '.' in section_id:
                    # 例如 "4.3.5" 表示这是第4个主标题下的第3个子标题下的第5个小节
                    # 那么深度应该是3（4是1级，4.3是2级，4.3.5是3级）
                    current_depth = len(section_id.split('.'))
                
                if title and content:
                    current_path = path + [{"title": title, "depth": current_depth}]
                    sections.append({
                        "id": section_id,                      # 新增：保存 id
                        "title": title,
                        "content": content,
                        "depth": current_depth,
                        "path": current_path.copy(),
                        "tokens": count_tokens(content)
                    })
                
                # 检查是否有 children
                if 'children' in data and data['children']:
                    current_path = path + [{"title": title, "depth": current_depth}]
                    # 递归处理 children，子节点的深度加1
                    for child in data['children']:
                        extract_sections(child, current_path, current_depth)
        
        # 从 section_content_pairs 中提取所有 section
        extract_sections(self.section_content_pairs)
        
        # 改为按 id 数值序列排序
        def path_sort_key(section):
            try:
                # "3.2.1" -> (3,2,1)，"5" -> (5,)
                return tuple(int(x) for x in section.get("id", "0").split("."))
            except ValueError:
                return (0,)
            
        sections.sort(key=path_sort_key)
        printer.rule(f"Extracted {len(sections)} sections from the report.")
        printer.print(json.dumps(sections, indent=2))
        
        
        # 创建滑动窗口
        windows = []
        i = 0
        while i < len(sections):
            current_section = sections[i]
            highest_title = current_section['title']
            highest_depth = current_section['depth']
            current_path = current_section['path']
            
            # 使用原始深度来设置标题级别
            merged_content = f"{'#' * current_section['depth']} {highest_title}\n{current_section['content']}"
            window_tokens = current_section['tokens'] + count_tokens(f"{'#' * current_section['depth']} {highest_title}\n")
            window_path = [current_section['path'][-1]]
            
            # 尝试添加后续的 section，如果它们是当前 section 的子节点或平级节点
            j = i + 1
            while j < len(sections) and window_tokens < max_token_length:
                next_section = sections[j]
                next_path = next_section['path']
                
                # 检查路径关系时使用标题字符串进行比较
                current_path_titles = [p["title"] for p in current_path]
                next_path_titles = [p["title"] for p in next_path]
                
                # 检查是否为子节点或平级节点
                is_subsection_or_sibling = False
                
                # 如果下一个 section 是当前 section 的子节点
                if len(next_path_titles) > len(current_path_titles) and all(next_path_titles[k] == current_path_titles[k] for k in range(len(current_path_titles))):
                    is_subsection_or_sibling = True
                
                # 如果下一个 section 是当前 section 的平级节点
                elif len(next_path_titles) == len(current_path_titles) and all(next_path_titles[k] == current_path_titles[k] for k in range(len(current_path_titles) - 1)):
                    is_subsection_or_sibling = True
                
                if is_subsection_or_sibling:
                    # 使用原始深度来设置标题级别，不再计算相对深度
                    section_header = '#' * next_section['depth'] + ' ' + next_section['title'] + '\n'
                    additional_tokens = count_tokens(section_header + next_section['content'])
                    
                    if window_tokens + additional_tokens <= max_token_length:
                        # 可以添加到当前窗口
                        merged_content += f"\n{section_header}{next_section['content']}"
                        window_tokens += additional_tokens
                        window_path.append({"title": next_section['title'], "depth": next_section['depth']})
                        j += 1
                    else:
                        # 超出 token 限制，不能再添加
                        break
                else:
                    # 不是子节点或平级节点，跳过
                    break
            
            # 创建窗口对象
            # 修改这里，将路径文本包含标题的层级信息
            def format_path_with_depth(path_nodes):
                formatted_titles = []
                for node in path_nodes:
                    depth = node["depth"]
                    title = node["title"]
                    formatted_title = '#' * depth + ' ' + title
                    formatted_titles.append(formatted_title)
                return ' -> '.join(formatted_titles)
            
            path_text = format_path_with_depth(window_path)
            window = {
                "highest_title": highest_title,
                "merged_section_window_content": merged_content,
                "section_window_path": window_path,
                "section_window_path_text": path_text,
                "section_window_tokens": window_tokens
            }
            
            windows.append(window)
            
            # 下一个窗口的起始位置
            i = j if j > i + 1 else i + 1
        
        printer.rule(f"Created {len(windows)} sliding windows.")
        printer.print(json.dumps(windows, indent=2))
                
        return windows

    def run_factualqa(self):
        # Load and render a template "factual_qa.txt" for FactualQA evaluation.
        # Pass Query, BreadthGT (converted to JSON string) and DepthGT.
        template_str = self.agent.load_template("factual_qa.txt")
        data = {
            "Query": self.user_query,  # Updated from self.query to self.user_query
            "BreadthGT": json.dumps(self.breadth_gt),
            "DepthGT": self.depth_gt,
        }
        prompt = self.agent.render_template(template_str, data)
        response = self.agent.chat(usr_prompt=prompt)
        return response

    def process_section_with_models(self, section_text: str, models: list) -> list:
        """使用多个模型并行处理同一段文本"""

        def process_with_model(model: str):
            try:
                template_str = self.agent.load_template("fact_extraction_new.txt")
                data = {
                    "wiki_text": section_text,
                    "UserQuery": self.user_query,
                }
                prompt = self.agent.render_template(template_str, data)

                printer.print(f"Model: {model}")
                # 通过 safe_chat_and_parse 完成模型调用 + JSON 解析
                candidate = safe_chat_and_parse(self.agent, prompt, model)
                # 如果拿到的是 list，则继续处理
                if isinstance(candidate, list):
                    parsed_data = self.parse_tagged_data_to_table(candidate)
                    return {"model": model, "data": parsed_data}
                else:
                    printer.print(f"[WARN] 模型 {model} 返回非列表结构: {candidate}")
                    return None

            except Exception as e:
                printer.print(f"[ERROR] model={model} failed after {settings.max_retries} retries:\n{e}")
                return None

        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            # submit + as_completed，方便捕获每个 future 的异常
            futures = {executor.submit(process_with_model, m): m for m in models}
            for fut in as_completed(futures):
                model = futures[fut]
                try:
                    res = fut.result()  # 这里会抛出未被捕获的异常
                    results.append(res)
                except Exception as e:
                    printer.print(f"[ERROR] task for {model} failed: {e}")

        # 过滤掉 None
        results = [r for r in results if r is not None]

        # 对每个结果进行格式验证
        verified_results = []
        for result in results:
            verified_data = []
            for item in result["data"]:
                print(f"\n\nVerifying item: {item}\n\n")
                if self.verify_qa_format(item):
                    verified_data.append(item)
            if verified_data:
                result["data"] = verified_data
                verified_results.append(result)

        # 聚合并去重
        return self.aggregate_model_results(verified_results)

    def aggregate_model_results(self, results: list) -> list:
        """聚合多个模型的结果并去重"""
        seen_items = set()
        unique_results = []
        
        for result in results:
            for item in result["data"]:
                # 创建问题和答案的组合哈希值
                item_hash = hashlib.md5(
                    f"{item['question'].strip().lower()}_{item['answer'].strip().lower()}".encode()
                ).hexdigest()
                
                if item_hash not in seen_items:
                    seen_items.add(item_hash)
                    item["source_model"] = result["model"]  # 添加来源模型信息
                    unique_results.append(item)
        
        return unique_results

    def process_window_content(self, content, max_retries=10):
        """修改现有的处理方法以使用多模型"""
        # 从settings中直接获取extract_models配置
        models = settings.extract_models if hasattr(settings, 'extract_models') else ["gpt-4o"]
        
        for attempt in range(max_retries):
            try:
                # 使用多个模型并行处理
                results = self.process_section_with_models(content, models)
                if results:  # 如果有结果则返回
                    return results
            except Exception:
                continue
        
        return []  # 如果所有尝试都失败则返回空列表

    def generate_benchmark_item(self, use_cache=True, max_window_tokens=1):
        """添加缓存支持的基准测试项生成方法"""
        if use_cache:
            cached_results = self._load_from_cache()
            if cached_results is not None:
                printer.print("Loading results from cache...")
                return cached_results

        windows = self.sliding_window_pairing(max_token_length=max_window_tokens)

        # 并发处理所有窗口
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {
                executor.submit(self.process_window_content, w["merged_section_window_content"]): w
                for w in windows
            }
            for fut in tqdm(as_completed(futures),
                            total=len(futures),
                            desc="⏳ Processing windows",
                            unit="win"):
                w = futures[fut]
                parsed = fut.result()
                if parsed:
                    results.append({
                        "path": w["section_window_path_text"],
                        "merged_section_window_content": w["merged_section_window_content"],
                        "extracted_facts": parsed
                    })

        # 缓存保存同原来
        if use_cache:
            self._save_to_cache(results)

        return results

    def verify_qa_format(self, item: dict) -> bool:
        """验证问答对是否符合格式约束"""
        data = {
            "question": item["question"],
            "format": item["format"],
            "answer": extract_boxed_content(item["answer"]),
        }
        try:
            template_str = self.agent.load_template("verify_qa_format.txt")
            prompt = self.agent.render_template(template_str, data)
            # 同样使用 safe_chat_and_parse 重试模型验证
            result = safe_chat_and_parse(self.agent, prompt, model="gpt-4o")
            printer.log(f"\nVerification Result: \n{result}\n")
            return result.get("result") is True
        except Exception as e:
            printer.print(f"[ERROR] 验证失败 after {settings.max_retries} retries: {e}")
            return False

    def parse_tagged_data_to_table(self, entries, csv_path=None):
        """解析模型返回的数据并添加来源模型字段"""
        parsed_data = []
        for entry in entries:
            # 使用通用方法提取 question 和 format
            q = extract_tag_content(entry, "question")
            fmt = extract_tag_content(entry, "constrained_format")
            # 提取 answer 并解析 boxed 内容
            raw_ans = extract_answer_from_response(entry)
            ans = extract_boxed_content(raw_ans)
            if q and fmt and ans:
                parsed_data.append({
                    "question": q,
                    "format": fmt,
                    "answer": ans,
                    "source_model": None,  # aggregate_model_results 会填充
                })
        return parsed_data

    def verify_extraction_meaningful(self):
        # Check if the fact extraction result is meaningful enough and correct.
        pass


# %% [markdown]
# ## Example Usage

# %%
def generate_benchmarks_for_folder(
    folder_path: str,
    use_cache: bool = True,
    max_workers: int = 50,
    max_window_tokens: int = 1
) -> dict:
    """批量生成文件夹中所有 json 文件的基准测试项，使用缓存并行执行"""
    if not os.path.isdir(folder_path):
        printer.print(f"[ERROR] {folder_path} 不是有效的文件夹路径。")
        return {}
    json_files = sorted(Path(folder_path).glob("*.json"))
    if not json_files:
        printer.print(f"[WARN] 文件夹 {folder_path} 不包含任何 json 文件。")
        return {}

    results = {}
    to_process = []
    # 先检查缓存，命中则直接加载
    for fp in json_files:
        bench = ReportBenchmark(str(fp))
        if use_cache:
            cached = bench._load_from_cache()
            if cached is not None:
                printer.print(f"[CACHE] 加载 {fp.name} 缓存")
                results[fp.name] = cached
                continue
        to_process.append(fp)

    # 并行处理未命中的文件
    def _process_file(fp: Path):
        printer.rule(f"Processing {fp.name}")
        bench = ReportBenchmark(str(fp))
        return fp.name, bench.generate_benchmark_item(
            use_cache=use_cache,
            max_window_tokens=max_window_tokens
        )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_file, fp): fp for fp in to_process}
        for fut in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="⏳ Processing files",
            unit="file"
        ):
            fp = futures[fut]
            try:
                name, res = fut.result()
                results[name] = res
            except Exception as e:
                printer.print(f"[ERROR] 处理 {fp.name} 失败：{e}")

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python report_benchmark.py <json_file_or_folder>")
        sys.exit(1)

    input_path = sys.argv[1]
    if os.path.isdir(input_path):
        all_results = generate_benchmarks_for_folder(input_path)
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
    else:
        results = ReportBenchmark(input_path).generate_benchmark_item(use_cache=True)
        print("Benchmark Item curation Results:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
# %%
"""
# 处理单个 json
python report_benchmark.py data/report1.json

# 或者处理整个文件夹
python src/criticsearch/reportbench/report_benchmark.py src/criticsearch/reportbench/wiki_data
"""