## Usage

`python -m search_adapter`

or

```python
from agent_factory.search_adapter.search_aggregator import SearchAggregator

# 初始化 SearchAggregator
aggregator = SearchAggregator()

# 调用搜索方法
query = "Who is Lionel Messi?"
response = aggregator.search(query=query)

# 输出搜索结果
print(f"Query: {response.query}")
print(f"Response Time: {response.response_time} seconds")
print("Results:")
for result in response.results:
    print(f"- Title: {result.title}")
    print(f"  URL: {result.url}")
    print(f"  Content: {result.content[:100]}...")  # 仅显示内容的前 100 个字符
```