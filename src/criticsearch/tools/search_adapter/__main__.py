from .search_aggregator import SearchAggregator

if __name__ == "__main__":
    search_aggregator = SearchAggregator()

    response = search_aggregator.search_with_multiplex(
        queries=["Who is Leo Messi?", "Who is Cristiano Ronaldo?"]
    )

    print(response.model_dump())
