[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Installing uv

`curl -LsSf https://astral.sh/uv/install.sh | sh`

### Adding dependencies

`uv add httpx`

### Creating a virtual environment

`uv venv`

## Obtain Search Engine API Keys (Optional)

### [Tavily](https://app.tavily.com/)
- **Features**: Handles searching, scraping, filtering, and extracting relevant information.  
- **Free Tier**: 1,000 free requests per month.  

### [Bing](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
- **Features**: Enables high-quality search results with advanced filtering.  
- **Free Tier**: 1,000 free requests per month, 3 transactions per second.  


## Run critic_search

1. Rename `settings.yaml.template` to `settings.template`.

2. Run command.

```python
python -m critic_search
```