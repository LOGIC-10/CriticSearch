[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

# Critic Search

Critic Search is an intelligent querying and analysis framework designed to enhance the process of information retrieval. By leveraging a powerful LLM-based agent, it dynamically generates precise search queries tailored to user-defined requirements. After gathering the initial set of results, the system critically evaluates and refines them, iteratively adjusting queries to achieve increasingly relevant and accurate outputs. Through this repeated cycle of critical review and refinement, Critic Search delivers results that are both contextually grounded and deeply insightful, enabling users to efficiently obtain the most valuable information from vast data sources.

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


## Using pip(Alternative)

### Installing dependencies

```python
pip install -r requirements.txt
```

## Run critic_search

1. Rename `settings.yaml.template` to `settings.template`.

2. Run command.

```python
criticsearch
```