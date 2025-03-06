from concurrent.futures import ThreadPoolExecutor
import concurrent
from rouge_score import rouge_scorer
from typing import List, Dict
from tqdm import tqdm
import re

class ReportVerifier:
    def __init__(self, agent):
        self.agent = agent
        self.scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        
    def verify_section(self, context: str, extracted_facts: List[Dict]) -> float:
        print("\n=== Starting Factual QA Verification ===")
        print(f"Total questions to verify: {len(extracted_facts)}\n")

        def verify_single_question(fact):
            qa_data = {
                "context": context,
                "user_question": fact["question"],
                "constrained_format": fact["format"]
            }
            
            print(f"\nVerifying Question: {fact['question']}")
            print(f"Format: {fact['format']}")
            
            response = self.agent.chat_with_template(
                "factQA_verifier.txt",
                qa_data
            )
            
            return self._check_answer(response, fact["answer"])
            
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(verify_single_question, fact): fact 
                      for fact in extracted_facts}
            results = []
            
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(extracted_facts),
                desc="Verifying questions"
            ):
                results.append(future.result())
                
        accuracy = self._calculate_score(results, len(extracted_facts))
        return accuracy

    def _normalize_text(self, text: str) -> str:
        """标准化文本,只保留字母数字,转小写并去除空格
        
        Args:
            text: 输入文本
            
        Returns:
            标准化后的文本
        """
        # 只保留字母和数字
        text = re.sub(r'[^a-zA-Z0-9]', '', text)
        # 转换为小写
        text = text.lower()
        return text

    def _check_answer(self, model_answer: str, ground_truth: str) -> tuple:
        if model_answer is None:
            return False, 0.0
        
        pattern = r'\\boxed{(.*?)}'
        model_boxed = re.findall(pattern, model_answer)
        ground_truth_boxed = re.findall(pattern, ground_truth)
        
        is_correct = False
        rouge_score = 0.0
        
        if model_boxed and ground_truth_boxed:
            # 对答案进行标准化处理
            model_ans = self._normalize_text(model_boxed[0])
            ground_truth = self._normalize_text(ground_truth_boxed[0])
            
            # 完全匹配检查
            is_correct = model_ans == ground_truth
            
            if not is_correct:
                scores = self.scorer.score(ground_truth, model_ans)
                rouge_score = scores['rougeL'].fmeasure

            # 输出时显示原始答案和标准化后的答案
            print("-" * 50)
            if is_correct:
                print("✓ Exact Match")
            else:
                print(f"✗ Partial Match (ROUGE-L: {rouge_score:.2%})")
            print(f"Expected (original): {ground_truth_boxed[0]}")
            print(f"Got (original): {model_boxed[0]}")
            print(f"Expected (normalized): {ground_truth}")
            print(f"Got (normalized): {model_ans}")
            print("-" * 50)
                
        return is_correct, rouge_score

    def _calculate_score(self, results: List, total: int) -> float:
        exact_matches = sum(1 for correct, _ in results if correct)
        rouge_scores = [score for correct, score in results if not correct]
        avg_rouge = sum(rouge_scores) / total if rouge_scores else 0
        
        final_accuracy = 0.7 * (exact_matches / total) + 0.3 * avg_rouge
        
        print("\n=== Verification Results Summary ===")
        print(f"Total Questions: {total}")
        print(f"Exact Matches: {exact_matches}/{total} ({exact_matches/total:.2%})")
        print(f"Average ROUGE-L for Partial Matches: {avg_rouge:.2%}")
        print(f"Final Weighted Score: {final_accuracy:.2%}")
        print("=" * 40 + "\n")
        
        return final_accuracy
