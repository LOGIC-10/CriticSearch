if __name__ == "__main__":

    from .search_adapter.aggregator import SearchAggregator

    search_aggregator = SearchAggregator()

    from .tools import Tool
    print(Tool.create_schema_from_function(search_aggregator.search))