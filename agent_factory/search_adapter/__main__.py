from .tavily_client import TavilyClient

if __name__ == "__main__":
    client = TavilyClient()
    response = client.search(query="Who is Leo Messi?")

    if response.results:
        print(response.results[0].content)