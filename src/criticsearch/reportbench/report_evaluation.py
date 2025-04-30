import json
from report_benchmark import ReportBenchmark  # 引入 ReportBenchmark
from tree_comparison import tree_similarity

class ReportEvaluation:
    def __init__(self, report_benchmark: ReportBenchmark, student_report: str):
        # 使用 ReportBenchmark 实例获得 ground truths
        self.report_benchmark = report_benchmark
        # 新增的 StudentReport 字段
        self.student_report = student_report

    def examinees_outline_generation(self):
        # 使用 ReportBenchmark 的 BaseAgent 调用，生成学生树（此前在 ReportBenchmark 中的 run_outline_generation）
        template_str = self.report_benchmark.agent.load_template("outline_generation.txt")
        data = {
            "Query": self.report_benchmark.user_query,
        }
        prompt = self.report_benchmark.agent.render_template(template_str, data)
        response = self.report_benchmark.agent.chat(usr_prompt=prompt)
        return response

    def evaluate_breadth(self):
        # 直接使用 examinees_outline_generation 生成学生树
        student_tree_str = self.examinees_outline_generation()
        student_tree = json.loads(student_tree_str)
        score = tree_similarity(self.report_benchmark.breadth_gt, student_tree)
        return score

    def evaluate_factualqa(self):
        # 基于传入的 StudentReport 执行 FactualQA 评估
        template_str = self.report_benchmark.agent.load_template("factual_qa.txt")
        data = {
            "Query": self.report_benchmark.user_query,
            "BreadthGT": json.dumps(self.report_benchmark.breadth_gt),
            "DepthGT": self.student_report,
        }
        prompt = self.report_benchmark.agent.render_template(template_str, data)
        response = self.report_benchmark.agent.chat(usr_prompt=prompt)
        return response

    def extract_student_tree_structure(self):
        # 新增函数：从 student_report 中抽取目录树逻辑结构
        template_str = self.report_benchmark.agent.load_template("student_tree_extraction.txt")
        data = {"StudentReport": self.student_report}
        prompt = self.report_benchmark.agent.render_template(template_str, data)
        response = self.report_benchmark.agent.chat(usr_prompt=prompt)
        return json.loads(response)
    
    def evaluate_depth(self):
        # 深度评估逻辑暂不实现，基于factual QA结果评估ACC
        # 这里实现抽取student report based answer 的acc来计算最后的分数
        pass


if __name__ == "__main__":
    # 示例：先生成 ReportBenchmark 实例，再调用 ReportEvaluation 进行评估
    json_file = "/Users/logic/Documents/CodeSpace/CriticSearch/final_wiki/2024_Syrian_opposition_offensives.json"
    bench = ReportBenchmark(json_file)
    # 示例传入 student_report 字符串
    student_report = "Your student report content here"
    eval_inst = ReportEvaluation(bench, student_report)
    breadth_score = eval_inst.evaluate_breadth()
    print("Breadth Evaluation Score:", breadth_score)
    factualqa_result = eval_inst.evaluate_factualqa()
    print("FactualQA Evaluation Result:", factualqa_result)
