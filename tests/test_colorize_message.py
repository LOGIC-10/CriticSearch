# from rich.console import Console

# # 创建控制台对象
# console = Console()

# # 普通信息输出
# console.print([1, 2, 3])
# console.print("[blue underline]Looks like a link")
# console.print(locals())
# console.print("FOO", style="white on blue")

# # 使用 .log 方法输出日志
# console.log("This is a log message with a timestamp.")
# console.log("[green]System initialized successfully![/green]")
# console.log({"key": "value", "number": 123}, style="dim")

# # 异常处理并打印异常信息
# def divide(x, y):
#     try:
#         result = x / y
#         console.log(f"Result: {result}")
#     except Exception as e:
#         console.log("[red]An exception occurred![/red]")
#         console.print_exception(max_frames=5)

# # 示例：正常执行
# divide(10, 2)

# # 示例：出现异常（除以零）
# divide(10, 0)

import yaml
from rich.console import Console
from rich.syntax import Syntax

# 创建一个 console 实例
console = Console()

# 定义一个样例 YAML 数据
yaml_data = """
name: John Doe
age: 30
address:
  street: 1234 Elm St
  city: Springfield
  state: IL
hobbies:
  - Reading
  - Traveling
  - Cycling
"""

# 将 YAML 数据加载为字典
yaml_dict = yaml.safe_load(yaml_data)

# 使用 rich 的 Syntax 来格式化 YAML 内容
yaml_syntax = Syntax(yaml_data, "yaml", theme="plain", line_numbers=True)

# 打印格式化的 YAML 数据
console.print(yaml_syntax)
