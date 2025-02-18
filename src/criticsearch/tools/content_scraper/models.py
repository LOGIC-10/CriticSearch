from typing import List, Optional

from pydantic import BaseModel, Field, model_serializer


class ScrapedData(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


class ScrapedDataList(BaseModel):
    data: List[ScrapedData] = Field(default_factory=list)
    max_content_length: int = 10000  # Max length for individual content
    max_output_length: int = 100000  # Max length for the entire serialized result

    @model_serializer
    def ser_model(self) -> str:
        # List to store concatenated strings
        result = []

        for data in self.data:
            if data.error:
                result.append(f"Error for URL {data.url}: {data.error}\n")
                continue  # Skip further processing if there's an error

            assert data.content is not None

            # Truncate content to ensure it does not exceed max_content_length
            if len(data.content) > self.max_content_length:
                data.content = (
                    data.content[: self.max_content_length] + "[TOO LONG, END]"
                )

            result.append(
                f"URL: {data.url}\nTitle: {data.title}\nContent:\n{data.content}\n"
            )

        output = "\n---\n".join(result)

        # Apply final length truncation to the overall result
        if len(output) > self.max_output_length:
            output = output[: self.max_output_length] + "\n[OUTPUT TOO LONG, TRUNCATED]"

        return output
