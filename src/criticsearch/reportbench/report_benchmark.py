# %% [markdown]
# # ReportBenchmark Notebook
# 本 Notebook 包含报告评估相关的代码单元, 后面需要移除

# %%
import json
import re
from concurrent.futures import ThreadPoolExecutor

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
import os
import hashlib
from pathlib import Path

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

    def _load_from_cache(self):
        """从缓存加载结果"""
        cache_file = self.cache_dir / f"{self._get_cache_key()}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_to_cache(self, results):
        """保存结果到缓存"""
        cache_file = self.cache_dir / f"{self._get_cache_key()}.json"
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
        
        # 按深度和标题路径排序，确保父节点在子节点之前
        # 使用路径长度和路径中的标题字符串进行排序
        def path_sort_key(section):
            path_len = len(section['path'])
            # 将路径转换为可比较的字符串序列
            path_titles = [p["title"] for p in section['path']]
            return (path_len, tuple(path_titles))
            
        sections.sort(key=path_sort_key)
        
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
        
        return windows

    def run_fact_extraction(self):
        """
        使用 self.sections 中的每个 markdown 文本调用 fact_extraction，
        并行执行，返回一个包含各 section 响应的列表。
        如果对某个 section 10 次尝试后都失败，则发出警告并跳过该 section。
        """

        def process_section(section_text):
            @retry(stop=stop_after_attempt(10), wait=wait_fixed(1), reraise=True)
            def attempt():
                template_str = self.agent.load_template("fact_extraction.txt")
                data = {
                    "wiki_text": section_text,
                    "UserQuery": self.user_query,
                }
                prompt = self.agent.render_template(template_str, data)
                response = self.agent.common_chat(usr_prompt=prompt)
                if not isinstance(response, list):
                    if not response.strip():
                        raise Exception("Empty response received from common_chat")
                    try:
                        candidate = json.loads(response)
                        print(candidate)
                        if isinstance(candidate, list):
                            return candidate
                    except Exception as e:
                        raise Exception("Section response conversion failed") from e
                    raise Exception("Section response is not a list")
                return response

            try:
                return attempt()
            except Exception as e:
                print(
                    f"Warning: Failed to process section after 10 attempts. Skipping this section. Error: {e}"
                )
                return None

        with ThreadPoolExecutor() as executor:
            raw_results = list(executor.map(process_section, self.sections))
        # Filter out any sections that failed after 10 attempts
        results = [result for result in raw_results if result is not None]
        return results  # 返回 List[List[str]]，每个元素是一个 section 的 fact extraction 结果

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
        response = self.agent.common_chat(usr_prompt=prompt)
        return response

    def process_window_content(self, content, max_retries=10):
        """处理单个窗口内容,如果结果为空则重试"""
        for attempt in range(max_retries):
            try:
                result = self.process_section(content)
                if result:
                    parsed_data = self.parse_tagged_data_to_table(result)
                    if parsed_data:  # 如果解析出的数据不为空
                        return parsed_data
                print(f"Attempt {attempt + 1}: Empty result, retrying...")
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
        return []  # 如果所有尝试都失败,返回空列表

    def generate_benchmark_item(self, use_cache=True):
        """添加缓存支持的基准测试项生成方法"""
        if use_cache:
            cached_results = self._load_from_cache()
            if cached_results is not None:
                print("Loading results from cache...")
                return cached_results
        
        # 原有的生成逻辑
        results = []
        windows = self.sliding_window_pairing()
        
        # 准备抽取任务的输入
        window_contents = []
        window_paths = []
        for window in windows:
            window_contents.append(window["merged_section_window_content"])
            window_paths.append(window["section_window_path_text"])
        
        # 组合抽取结果和路径信息
        final_results = []
        for path, content in zip(window_paths, window_contents):
            parsed_data = self.process_window_content(content)
            if parsed_data:
                final_results.append({
                    "path": path,
                    "merged_section_window_content": content,
                    "extracted_facts": parsed_data
                })
        
        # 保存结果到缓存
        if use_cache:
            self._save_to_cache(final_results)
            
        return final_results

    def process_section(self, section_text):
        """将原来run_fact_extraction中的process_section逻辑移到单独的方法"""
        @retry(stop=stop_after_attempt(10), wait=wait_fixed(1), reraise=True)
        def attempt():
            template_str = self.agent.load_template("fact_extraction.txt")
            data = {
                "wiki_text": section_text,
                "UserQuery": self.user_query,
            }
            prompt = self.agent.render_template(template_str, data)
            response = self.agent.common_chat(usr_prompt=prompt)
            if not isinstance(response, list):
                if not response.strip():
                    raise Exception("Empty response received from common_chat")
                try:
                    candidate = json.loads(response)
                    print(candidate)
                    if isinstance(candidate, list):
                        return candidate
                except Exception as e:
                    raise Exception("Section response conversion failed") from e
                raise Exception("Section response is not a list")
            return response

        try:
            return attempt()
        except Exception as e:
            print(
                f"Warning: Failed to process section after 10 attempts. Skipping this section. Error: {e}"
            )
            return None

    def parse_tagged_data_to_table(self, entries, csv_path=None):
        parsed_data = []
        for entry in entries:
            # Extract question
            question_match = re.search(r"</question>(.*?)</question>", entry)
            question = question_match.group(1).strip() if question_match else ""

            # Extract format description
            format_match = re.search(
                r"</constrained_format>(.*?)</constrained_format>", entry
            )
            format_desc = format_match.group(1).strip() if format_match else ""

            # Extract answer
            answer_match = re.search(r"</answer>(.*?)</answer>", entry)
            answer = answer_match.group(1).strip() if answer_match else ""

            # 验证answer中是否包含\boxed{...}格式的内容
            boxed_match = re.search(r"\\boxed{([^}]+)}", answer)
            if boxed_match:  # 只有当匹配到boxed内容时才添加到结果中
                parsed_data.append(
                    {"question": question, "format": format_desc, "answer": answer}
                )

        return parsed_data

    def verify_extraction_meaningful(self):
        # Check if the fact extraction result is meaningful enough and correct.
        pass


# %% [markdown]
# ## Example Usage

# %%
if __name__ == "__main__":
    json_file = "/workspaces/CriticSearch/src/criticsearch/reportbench/wiki_data/2024_Syrian_opposition_offensives.json"
    benchmark = ReportBenchmark(json_file)
    # print(benchmark.section_content_pairs)
    print(json.dumps(benchmark.sliding_window_pairing(max_token_length=800), indent=2))
    results = benchmark.generate_benchmark_item(use_cache=True)
    print("Benchmark Item curation Results:")
    print(json.dumps(results, indent=2))
# %%
