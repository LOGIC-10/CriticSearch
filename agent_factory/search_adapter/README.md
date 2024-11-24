## Usage

`python -m search_adapter`

or

```python
from search_adapter.aggregator import SearchAggregator

# 初始化 SearchAggregator
aggregator = SearchAggregator()

# 调用搜索方法
query = "Who is Lionel Messi?"
response = aggregator.search(query=query)

print(response)

# 输出搜索结果
print(f"Query: {response.get('query')}")
print(f"Response Time: {response.get('response_time')} seconds")
print("Results:")
for result in response.get("results"):
    print(f"- Title: {result.get('title')}")
    print(f"  URL: {result.get('url')}")
    print(f"  Content: {result.get('content')}...")  # 仅显示内容的前 100 个字符
```