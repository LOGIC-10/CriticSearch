import json
import os
from typing import Dict, Any, List

def reorder_constrained_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """将每条记录中 constrained_format 放在 GroundTruth 之后"""
    new_data = {}
    for q, entry in data.items():
        gt = entry.get("GroundTruth")
        cf = entry.get("constrained_format")
        # 其余字段
        others = {k: v for k, v in entry.items() if k not in ("GroundTruth", "constrained_format")}
        # 重建顺序
        reordered = {"GroundTruth": gt}
        if cf is not None:
            reordered["constrained_format"] = cf
        reordered.update(others)
        new_data[q] = reordered
    return new_data

def find_all_wrong_items(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    返回所有模型都答错的条目映射（question -> entry）。
    判定：除 GroundTruth 和 constrained_format 外，
    若所有其它字段中的 'is_correct' 都为 False，则认为此条目全部答错。
    """
    wrong_items: Dict[str, Dict[str, Any]] = {}
    for q, entry in data.items():
        # 收集所有模型字段
        model_fields = [v for k, v in entry.items() if k not in ("GroundTruth", "constrained_format")]
        # 若至少有一个模型且全部 is_correct=False
        if model_fields and all(not m.get("is_correct", False) for m in model_fields if isinstance(m, dict)):
            wrong_items[q] = entry
    return wrong_items

# 示例用法
if __name__ == "__main__":
    path = "fuzzy_replacement_bench_eval_cache.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # cache 也可能是 list
    if isinstance(raw, list):
        raw = {e["question"]: e for e in raw}
    # 重用原有逻辑
    reordered = reorder_constrained_format(raw)
    wrong = find_all_wrong_items(reordered)
    print(f"全部模型答错的条目共 {len(wrong)} 条")
    # 按 bench.json 样式输出 list
    base, ext = os.path.splitext(path)
    new_path = f"{base}_refined{ext}"
    refined_list: List[Dict[str, Any]] = []
    for q, entry in raw.items():
        if q in wrong:
            refined_list.append({
                "original_question": entry.get("original_question"),
                "question":          q,
                "answer":            entry.get("GroundTruth"),
                "constrained_format":entry.get("constrained_format"),
                "strategy":          entry.get("strategy"),
                "evidence":          entry.get("evidence", [])
            })
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(refined_list, f, ensure_ascii=False, indent=2)
    print(f"已保存全部答错数据到 {new_path}")
