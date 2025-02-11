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

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def run_fact_extraction(self):
        """
        使用 self.sections 中的每个 markdown 文本调用 fact_extraction，
        并行执行，返回一个包含各 section 响应的列表。
        """
        def process_section(section_text):
            template_str = self.agent.load_template("fact_extraction.txt")
            data = {
                "wiki_text": section_text,
                "UserQuery": self.user_query,
            }
            prompt = self.agent.render_template(template_str, data)
            response = self.agent.common_chat(usr_prompt=prompt)
            if not isinstance(response, list):
                try:
                    candidate = json.loads(response)
                    if isinstance(candidate, list):
                        return candidate
                except Exception as e:
                    raise Exception("Section response conversion failed") from e
                raise Exception("Section response is not a list")
            return response

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_section, self.sections))
        return results

    def run_outline_generation(self):  # TODO: 这里应该是要放到Evaluation的��里面的，改名叫Examinees_outline_generation
        # Load and render "outline_generation.txt" with Query
        template_str = self.agent.load_template("outline_generation.txt")
        data = {
            "Query": self.user_query,
        }
        prompt = self.agent.render_template(template_str, data)
        response = self.agent.common_chat(usr_prompt=prompt)
        return response

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

    def generate_benchmark_item(self):
        # Build both GTs and then run all benchmark evaluations.
        fact_extraction_result = self.run_fact_extraction()
        return {
            "breadth_gt": self.breadth_gt,
            # "depth_gt": self.depth_gt,
            "fact_extraction": fact_extraction_result,
            # "factual_qa": factualqa_result,
        }

    def verify_extraction_meaningful(self):
        # Check if the fact extraction result is meaningful enough and correct.
        pass


# %% [markdown]
# ## Example Usage

# %%
if __name__ == "__main__":
    json_file = "/Users/logic/Documents/CodeSpace/CriticSearch/final_wiki/2024_Syrian_opposition_offensives.json"
    benchmark = ReportBenchmark(json_file)
    results = benchmark.generate_benchmark_item()
    print("Benchmark Item curation Results:")
    print(results)
# %%
