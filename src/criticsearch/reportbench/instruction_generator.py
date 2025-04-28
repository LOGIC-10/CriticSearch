from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
from pathlib import Path
import random

from criticsearch.base_agent import BaseAgent

class InstructionGenerator:
    """
    遍历 wiki_data 目录下所有 json 文件，反向生成写作指令（instruction），
    并保存 file<->instruction 映射，支持随时加载查询。
    """

    def __init__(
        self,
        data_dir: str = None,
        mapping_file: str = "instruction_mapping.json",
    ):
        # 确保 data_dir 指向本模块下的 wiki_data 目录
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "wiki_data"

        # 如果 mapping_file 是相对路径，强制放到父目录 reportbench 下；否则保持绝对路径
        base_dir = Path(__file__).parent      # reportbench 目录
        mf = Path(mapping_file)
        self.mapping_file = (base_dir / mf.name) if not mf.is_absolute() else mf

        self.agent = BaseAgent()

        # debug：打印一下实际扫描目录和映射文件路径
        print(f"[DEBUG] InstructionGenerator.data_dir    = {self.data_dir.resolve()}")
        print(f"[DEBUG] InstructionGenerator.mapping_file = {self.mapping_file.resolve()}")

        # 如果已有映射，则直接加载
        self.mapping = self.load_mapping()

    def generate_instructions(self, overwrite: bool = False, max_workers: int = 20) -> dict:
        """
        并发为每个 json 文件生成一条 instruction，保存到 mapping_file。
        :param overwrite: 如果为 True，则重新生成所有文件的指令，否则跳过已存在的条目。
        :param max_workers: 线程池的最大工作线程数。
        :return: mapping: { "filename.json": "生成的指令文本", ... }
        """
        # 筛选需要处理的文件
        files = [
            jp for jp in self.data_dir.glob("*.json")
            if overwrite or jp.name not in self.mapping
        ]
        if not files:
            print("[INFO] No new JSON files to process.")
            return self.mapping

        def process_file(jp: Path):
            content = jp.read_text(encoding="utf-8")
            instruction_type = random.choice(["short", "long", "long and detailed", "super short", "one-sentence"])
            prompt = (
                "Below is the complete JSON content of an article:\n"
                f"{content}\n\n"
                f"Please design an appropriate {instruction_type} writing task instruction that would allow "
                "a model to recreate this article based on the instruction.\n"
                "Output only the instruction text, without any other explanations."
                "Make sure you don't include any specific detailed content about the article in the instruction.\n"
            )
            instr = self.agent.chat(usr_prompt=prompt)
            return jp.name, instr.strip()

        # 使用线程池并发调用
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {executor.submit(process_file, jp): jp.name for jp in files}
            for future in as_completed(future_to_name):
                fname, instruction = future.result()
                self.mapping[fname] = instruction
                print(f"[INFO] Generated instruction for {fname}")

        # 保存映射到文件
        with self.mapping_file.open("w", encoding="utf-8") as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)

        return self.mapping

    def load_mapping(self) -> dict:
        """
        加载已存在的 file<->instruction 映射，不存在则返回空 dict。
        """
        if self.mapping_file.exists():
            try:
                return json.loads(self.mapping_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def get_instruction_by_file(self, filename: str) -> str | None:
        """
        根据 JSON 文件名获取对应的 instruction。
        """
        return self.mapping.get(filename)

    def get_file_by_instruction(self, instruction: str) -> str | None:
        """
        根据 instruction 文本查找对应的 JSON 文件名（精确匹配）。
        """
        for fname, instr in self.mapping.items():
            if instr == instruction:
                return fname
        return None


if __name__ == "__main__":
    gen = InstructionGenerator()
    mapping = gen.generate_instructions(max_workers=100, overwrite=True)
    print("保存的映射关系示例：")
    for f, instr in mapping.items():
        print(f"{f}: {instr}")