from concurrent.futures import ThreadPoolExecutor
import concurrent
from rouge_score import rouge_scorer
from typing import List, Dict
from tqdm import tqdm
import re
from loguru import logger

class ReportVerifier:
    def __init__(self, agent):
        self.agent = agent
        self.scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        
    def verify_section(self, context: str, extracted_facts: List[Dict]) -> float:
        logger.info("\n=== Starting Factual QA Verification ===")
        logger.info(f"Total questions to verify: {len(extracted_facts)}\n")

        def verify_single_question(fact):
            qa_data = {
                "context": context,
                "user_question": fact["question"],
                "constrained_format": fact["format"]
            }
            
            logger.info(f"\nVerifying Question: {fact['question']}")
            logger.info(f"Format: {fact['format']}")
            
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

    def _check_answer(self, model_answer: str, ground_truth: str) -> tuple:
        pattern = r'\\boxed{(.*?)}'
        model_boxed = re.findall(pattern, model_answer)
        ground_truth_boxed = re.findall(pattern, ground_truth)
        
        is_correct = False
        rouge_score = 0.0
        
        if model_boxed and ground_truth_boxed:
            model_ans = model_boxed[0].lower()
            ground_truth = ground_truth_boxed[0].lower()
            is_correct = model_ans == ground_truth
            
            if not is_correct:
                scores = self.scorer.score(ground_truth, model_ans)
                rouge_score = scores['rougeL'].fmeasure

            logger.info("-" * 50)
            if is_correct:
                logger.success(f"✓ Exact Match")
            else:
                logger.warning(f"✗ Partial Match (ROUGE-L: {rouge_score:.2%})")
            logger.info(f"Expected: {ground_truth}")
            logger.info(f"Got: {model_ans}")
            logger.info("-" * 50)
                
        return is_correct, rouge_score

    def _calculate_score(self, results: List, total: int) -> float:
        exact_matches = sum(1 for correct, _ in results if correct)
        rouge_scores = [score for correct, score in results if not correct]
        avg_rouge = sum(rouge_scores) / total if rouge_scores else 0
        
        final_accuracy = 0.7 * (exact_matches / total) + 0.3 * avg_rouge
        
        logger.info("\n=== Verification Results Summary ===")
        logger.info(f"Total Questions: {total}")
        logger.info(f"Exact Matches: {exact_matches}/{total} ({exact_matches/total:.2%})")
        logger.info(f"Average ROUGE-L for Partial Matches: {avg_rouge:.2%}")
        logger.info(f"Final Weighted Score: {final_accuracy:.2%}")
        logger.info("=" * 40 + "\n")
        
        return final_accuracy