from .search_aggregator import SearchAggregator

if __name__ == "__main__":
    import asyncio

    async def main():
        search_aggregator = SearchAggregator()

        # 调用异步搜索方法
        response = await search_aggregator.search(query=["Who is Leo Messi?"])

        print(response)

    # 使用 asyncio.run 执行异步主函数
    asyncio.run(main())
