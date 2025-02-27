# %% [markdown]
# # ReportBenchmark Notebook
# 本 Notebook 包含报告评估相关的代码单元, 后面需要移除

# %%
import json
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed
from tree_comparison import tree_similarity  # imported but not used yet
from criticsearch.base_agent import BaseAgent
from extract_ground_truth import (
    extract_markdown_sections,
    extractDirectoryTree,
    extractMarkdownContent,
    extractSectionContentPairs,
)
from criticsearch.utils import count_tokens

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
            # 修改这里，将 section_window_path_text 设置为窗口中所有部分的标题
            path_titles = [p["title"] for p in window_path]
            path_text = " > ".join(path_titles)
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

    def generate_benchmark_item(self, visualization=False):
        # Build both GTs and then run all benchmark evaluations.
        fact_extraction_result = self.run_fact_extraction()
        final_parsed_data = []
        for section in fact_extraction_result:
            parsed_data = self.parse_tagged_data_to_table(section)
            final_parsed_data.append(parsed_data)

        if visualization:
            # Merge all parsed data into single list
            merged_data = []
            for parsed_data in final_parsed_data:
                merged_data.extend(parsed_data)
            # Create DataFrame and export CSV
            df = pd.DataFrame(merged_data)
            csv_file = "visualization.csv"
            df.to_csv(csv_file, index=False)
            print("Visualization DataFrame:")
            print(df)

        return {
            "title": self.breadth_gt.get("title", ""),
            "breadth_gt": self.breadth_gt,
            "fact_extraction": final_parsed_data,
        }

    def parse_tagged_data_to_table(self, entries, csv_path=None):
        """
        Parse a list of strings with tagged data and convert them into a table.

        Each entry in the list is expected to contain:
        - A question enclosed between </question> and </question>
        - A format description enclosed between </constrained_format> and </constrained_format>
        - An answer enclosed in </answer> and </answer>

        Parameters:
            entries (list of str): List of strings with tagged content.
            csv_path (str): Optional file path to save CSV.

        Returns:
            list of dict: List of dictionaries with parsed data.
        """

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

            # Append to parsed data
            parsed_data.append(
                {"Question": question, "Format": format_desc, "Answer": answer}
            )

        # Save to CSV if path is provided and ends with '.csv'
        if csv_path and csv_path.endswith(".csv"):
            # Create DataFrame
            df = pd.DataFrame(parsed_data)
            df.to_csv(csv_path, index=False)
            print(f"Table saved to {csv_path}")
            return df

        return parsed_data

    def verify_extraction_meaningful(self):
        # Check if the fact extraction result is meaningful enough and correct.
        pass


# %% [markdown]
# ## Example Usage

# %%
if __name__ == "__main__":
    json_file = "./wiki_data/2024_Syrian_opposition_offensives.json"
    benchmark = ReportBenchmark(json_file)
    # print(benchmark.section_content_pairs)
    print(json.dumps(benchmark.sliding_window_pairing(max_token_length=800), indent=2))
    # results = benchmark.generate_benchmark_item(visualization=True)
    # print("Benchmark Item curation Results:")
    # print(results)
# %%
