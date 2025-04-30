from typing import List

import httpx


class TavilyExtract:
    def __init__(self, api_key: str):
        self.base_url = "https://api.tavily.com/extract"
        self._api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    async def extract_content(self, urls: List[str]):
        payload = {"urls": urls}

        async with httpx.AsyncClient(http2=True) as client:
            try:
                response = await client.post(
                    self.base_url, headers=self.headers, json=payload
                )
                # Parse the response data and return the whole response object
                data = response.json()
                return data

            except httpx.RequestError as e:
                return {"detail": {"error": f"Request error occurred: {str(e)}"}}
