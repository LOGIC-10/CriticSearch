import json
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).parent.parent / "src" / "criticsearch" / "reportbench" / "wiki_data"

def test_all_wiki_json_valid():
    failures = []
    for jf in sorted(DATA_DIR.glob("*.json")):
        text = jf.read_text(encoding="utf-8")
        # 如果文件前面有注释行，可以先做一次简单清洗：
        # text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            failures.append(f"{jf.name}: {e}")
    if failures:
        pytest.fail("以下 JSON 文件解析失败:\n" + "\n".join(failures))