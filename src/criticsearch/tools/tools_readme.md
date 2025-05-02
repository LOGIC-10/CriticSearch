```markdown
# CriticSearch 工具开发 & 注册指南

本指南演示如何在 CriticSearch 中增添“外部工具”（tool），并将其 schema 传递给模型，供模型自动调用。

---

## 目录

1. 新建工具函数  
2. 在 package 中暴露工具  
3. 注册并生成 tool schema  
4. 将 schema 传给 LLM 接口  
5. 处理模型的 tool_call  
6. 端到端示例  

---

## 1. 新建工具函数

1. 在 `src/criticsearch/tools/` 下创建子模块，例如：

    ```bash
    mkdir -p src/criticsearch/tools/my_tools
    touch src/criticsearch/tools/my_tools/__init__.py
    ```

2. 编写你的函数。例如：  
    ```python
    # filepath: src/criticsearch/tools/my_tools/weather.py
    def get_weather(city: str) -> dict:
        """
        根据城市名称获取实时天气信息。
        参数:
          city (str): 城市名
        返回:
          dict: { "city": str, "temp": float, "condition": str }
        """
        # …这里接入真实天气 API…
        return {"city": city, "temp": 21.5, "condition": "Sunny"}
    ```

---

## 2. 在 package 中暴露工具

1. 打开 `src/criticsearch/tools/__init__.py`，添加导入：

    ```python
    # filepath: src/criticsearch/tools/__init__.py
    from .my_tools.weather import get_weather
    ```

---

## 3. 注册并生成 tool schema

所有工具统一由 `ToolRegistry` 管理、生成 schema。

1. 在需要使用工具的地方（比如在 Agent 初始化前），实例化 `ToolRegistry`：

    ```python
    # filepath: src/criticsearch/base_agent.py  （或你的启动脚本）
    from criticsearch.tools.tool_registry import ToolRegistry
    from criticsearch.tools.my_tools.weather import get_weather

    tool_registry = ToolRegistry()
    # 为你的函数生成 schema 列表
    function_schemas = tool_registry.get_or_create_tool_schema(get_weather)
    ```

2. `get_or_create_tool_schema` 内部会：
   - 读取函数的签名和 Google‑style docstring  
   - 调用 `Tool.create_schema_from_function` 自动生成符合 OpenAI Functions Format 的 JSON schema  
   - 并缓存到注册表中以免重复生成  

---

## 4. 将 schema 传给 LLM 接口

以 `BaseAgent.chat_with_tools(...)` 为例（在 `src/criticsearch/base_agent.py`）：

```python
# filepath: base_agent.py
def chat_with_tools(self, usr_prompt: str):
    # …准备 messages …
    response = self.llm_client.chat_completions(
        messages=messages,
        functions=function_schemas,      # ← 把 schema 传给模型
        function_call="auto",           # 或者指定要调用哪个工具
    )
    return response
```

- `functions` 参数即为上一步生成的 `function_schemas` 列表  
- 模型若决定调用工具，会在返回的 `assistant` 消息里给出 `tool_call`  

---

## 5. 处理模型的 tool_call

1. 在收到模型返回后，检测是否包含 `tool_call`：

    ```python
    if response.choices[0].message.tool_call:
        call = response.choices[0].message.tool_call
        # call.name  → "get_weather"
        # call.arguments → JSON 参数
    ```

2. 根据 `call.name` 调用实际函数：

    ```python
    from criticsearch.tools.tool_registry import ToolRegistry

    # 复用 registry 执行函数并序列化结果
    result = tool_registry.invoke_tool(call.name, call.arguments)
    ```

3. 将结果追加到对话历史，继续与模型交互。

---

## 6. 端到端示例

1. 在 `src/criticsearch/main.py` 中：

    ```python
    from criticsearch.base_agent import BaseAgent
    from criticsearch.tools.tool_registry import ToolRegistry
    from criticsearch.tools.my_tools.weather import get_weather

    def process_single_task(task: str):
        agent = BaseAgent()
        registry = ToolRegistry()
        schemas = registry.get_or_create_tool_schema(get_weather)

        # 首轮对话：用户询问天气
        user_prompt = f"请告诉我 {task} 的天气。"
        response = agent.llm_client.chat_completions(
            messages=[{"role":"user","content":user_prompt}],
            functions=schemas,
            function_call="auto",
        )

        # 模型请求调用 get_weather
        call = response.choices[0].message.tool_call
        data = json.loads(call.arguments)
        weather_info = registry.invoke_tool(call.name, data)

        # 将工具返回结果反馈给模型
        final = agent.llm_client.chat_completions(
            messages=[
              {"role":"assistant","content":None, "tool_call": call},
              {"role":"tool", "name": call.name, "content": json.dumps(weather_info)}
            ]
        )
        print("模型最终回答：", final.choices[0].message.content)
    ```

2. 运行：

    ```bash
    python -m criticsearch.main --task "Beijing"
    ```

---

恭喜！你已完成自定义工具的开发、注册、以及与模型的集成。  
更多细节请参阅：  
- `src/criticsearch/tools/tool_registry.py`  
- `src/criticsearch/tools/models.py`  
- `src/criticsearch/base_agent.py`  
```