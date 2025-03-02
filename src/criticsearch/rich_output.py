# rich_output.py
from pathlib import Path

from rich.console import Console


class RichPrinter:
    def __init__(self, console: Console = None):
        # 如果没有传入 Console 对象，默认使用一个新的 Console 实例
        self.console = console or Console(record=True)

        # 默认样式配置
        self.default_title_style = "[cyan bold]"
        self.default_line_characters = "="  # 使用 `=` 作为分隔线样式

    def rule(self, title: str):
        self.console.rule(
            f"{self.default_title_style}{title}",
            characters=self.default_line_characters,  # 默认使用 `=` 符号的分隔线
        )

    def log(self, message: str, style: str = None):
        """打印带有样式的日志消息"""
        self.console.log(message, style=style)

    def print(self, message: str, style: str = None):
        """打印普通的消息"""
        self.console.print(message, style=style)

    def print_exception(self, message: str, max_frames: int = 5):
        printer.log(f"{message}", style="bold red")

        """打印异常信息"""
        self.console.print_exception(max_frames=max_frames)

    def save_output_to_file(self, file_path: Path = Path("output.txt")):
        with open(file_path, "wt", encoding="utf-8") as report_file:
            # Redirect Console output to the specified file
            console_for_export = Console(file=report_file)

            # Export the console's current text output and write it to the file
            console_for_export.log(self.console.export_text())

            # Add a rule at the end of the output to indicate the file has been generated
            console_for_export.rule("Output file Generated.")


printer = RichPrinter()

# 使用方法：
if __name__ == "__main__":
    # 创建 RichPrinter 实例
    printer = RichPrinter()

    # 使用默认样式打印标题
    printer.rule("Section Content")

    # 打印普通日志消息
    printer.print("This is a normal message.")

    # 打印带有样式的消息
    printer.print("This is a styled message.", style="italic blue")

    # 打印带有样式的日志
    printer.log("This is a log message.", style="bold green")

    # 打印异常信息
    try:
        result = 1 / 0
    except Exception as e:
        printer.print_exception("An exception occurred!")

    printer.save_to_text_file("output_report.txt")
