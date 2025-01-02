# critic_search/tools/search_adapter/models.py
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_serializer
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from critic_search.config import settings
from critic_search.log import logger

from .db.database import engine
from .db.models import HistoryQuery, UniqueContent


class SearchResult(BaseModel):
    title: str
    url: str
    content: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    error_message: Optional[str] = None

    @model_serializer
    def ser_model(self) -> str:
        if self.error_message:
            formatted_response = (
                f"\nQuery: {self.query}\nError: {self.error_message}\n" + "-" * 50
            )
        elif self.results == []:
            formatted_response = (
                f"\nQuery: {self.query}\nError: No results found.\n" + "-" * 50
            )
        else:
            formatted_response = f"\nQuery: {self.query}\nSearch Results:\n" + "-" * 50
            for i, res in enumerate(self.results[: settings.search_max_responses], 1):
                formatted_response += (
                    f"\n[{i}]:\nTITLE: {res.title}\nURL: {res.url}\nCONTENT: {res.content}\n"
                    + "-" * 50
                )
        return formatted_response


class SearchResponseList(BaseModel):
    responses: List[SearchResponse] = Field(default_factory=list)

    @model_serializer
    def ser_model(self) -> str:
        total_results = 0
        unique_results_count = 0
        result_str = ""

        with Session(engine) as session:
            for response in self.responses:
                if response.error_message:
                    logger.warning(
                        f"Skipping response due to error: {response.error_message}"
                    )
                    continue

                try:
                    # Sub-transaction for HistoryQuery
                    with session.begin_nested():
                        history_entry = HistoryQuery(query=response.query)
                        session.add(history_entry)
                        session.flush()  # Write HistoryQuery to the database
                        logger.debug(f"Inserted HistoryQuery: {history_entry}")

                    # Sub-transaction for UniqueContent
                    unique_results = []
                    for res in response.results:
                        total_results += 1  # Increment total results counter
                        try:
                            with session.begin_nested():
                                unique_content = UniqueContent(content=res.content)
                                session.add(unique_content)
                                session.flush()  # Write UniqueContent to the database
                                unique_results.append(res)
                                unique_results_count += (
                                    1  # Increment unique results counter
                                )
                                logger.debug(
                                    f"Inserted UniqueContent: {unique_content}"
                                )
                        except IntegrityError:
                            # Handle duplicate content gracefully
                            logger.debug(f"Duplicate content skipped: {res.content}")
                            session.rollback()  # Rollback only this sub-transaction

                    # Finalize the deduplicated results for the response
                    response.results = unique_results
                    result_str += response.model_dump()  # type: ignore

                    logger.info(
                        f"Processed query '{response.query}' with {len(unique_results)} unique results."
                    )

                except Exception:
                    # Rollback the entire transaction for this response
                    logger.exception(f"Failed to process query '{response.query}'.")
                    session.rollback()

            # Commit all successful operations
            try:
                session.commit()
            except Exception:
                logger.exception("Failed to commit the session.")
                session.rollback()

        # Log the deduplication summary
        duplicates_removed = total_results - unique_results_count
        logger.success(
            f"Serialization completed. Total results: {total_results}, "
            f"Unique results: {unique_results_count}, "
            f"Duplicates removed: {duplicates_removed}."
        )

        return result_str
