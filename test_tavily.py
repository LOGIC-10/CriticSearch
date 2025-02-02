# Step 1: Import the TavilyClient
from tavily import TavilyClient

# Step 2: Instantiate your TavilyClient
client = TavilyClient(api_key="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")

# Step 3: Extract content from a URL using Tavily Extract
url = "https://www.nifc.gov/nicc-files/predictive/outlooks/monthly_seasonal_outlook.pdf"
response = client.extract(url)

# Step 4: Print the extracted content
print(response)
