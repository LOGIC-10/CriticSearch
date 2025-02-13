# %% [markdown]
# # ReportBenchmark Notebook
# 本 Notebook 包含报告评估相关的代码单元, 后面需要移除

# %%
import json
from tree_comparison import tree_similarity  # imported but not used yet
from extract_ground_truth import extract_markdown_sections, extractDirectoryTree, extractMarkdownContent
from critic_search.base_agent import BaseAgent
from tenacity import retry, stop_after_attempt, wait_fixed
from concurrent.futures import ThreadPoolExecutor
import re
import pandas as pd
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
        self.breadth_gt = extractDirectoryTree(self.json_path)  # Extract breadth ground truth，得到一个json结构的广度树
        self.article_content = extractMarkdownContent(self.json_path)
        self.sections = extract_markdown_sections(self.article_content)
        self.user_query = f"Generate a comprehensive long report about {self.breadth_gt.get('title', '')}" if user_query is None else user_query

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
                print(f"Warning: Failed to process section after 10 attempts. Skipping this section. Error: {e}")
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
            format_match = re.search(r"</constrained_format>(.*?)</constrained_format>", entry)
            format_desc = format_match.group(1).strip() if format_match else ""
            
            # Extract answer
            answer_match = re.search(r"</answer>(.*?)</answer>", entry)
            answer = answer_match.group(1).strip() if answer_match else ""
            
            # Append to parsed data
            parsed_data.append({
                "Question": question,
                "Format": format_desc,
                "Answer": answer
            })
    
        # Save to CSV if path is provided and ends with '.csv'
        if csv_path and csv_path.endswith('.csv'):
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
    json_file = "/Users/logic/Documents/CodeSpace/CriticSearch/final_wiki/2024_Syrian_opposition_offensives.json"
    benchmark = ReportBenchmark(json_file)
    results = benchmark.generate_benchmark_item(visualization=True)
    print("Benchmark Item curation Results:")
    print(results)
# %%
