from typing import Any
from dagster import ConfigurableResource, get_dagster_logger
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from langchain_core.documents import Document

from ask_ai_dagster.defs.resources.queries import (
    GITHUB_DISCUSSIONS_QUERY,
    GITHUB_ISSUES_QUERY,
)


class GithubResource(ConfigurableResource):
    """Resource for fetching issues and discussions from a GitHub."""

    github_token: str

    def client(self):
        return Client(
            schema=None,
            transport=RequestsHTTPTransport(
                url="https://api.github.com/graphql",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github.v4.idl",
                },
                retries=3,
            ),
            fetch_schema_from_transport=True,
        )

    def get_issues(self, start_date: str, end_date: str) -> list[dict]:
        issues_query = GITHUB_ISSUES_QUERY.replace(
            "START_DATE", start_date
        ).replace("END_DATE", end_date)
        return self._query(issues_query, "issues")

    def get_discussions(self, start_date: str, end_date: str) -> list[dict]:
        discussions_query = GITHUB_DISCUSSIONS_QUERY.replace(
            "START_DATE", start_date
        ).replace("END_DATE", end_date)
        return self._query(discussions_query, "discussions")

    def _query(self, query: str, object_type: str) -> list[dict]:
        logger = get_dagster_logger()
        client = self.client()
        cursor = None
        results = []

        while True:
            logger.info(
                f"Fetching results from Github: {object_type} with cursor: {cursor}"
            )
            query = gql(
                query.replace(
                    "CURSOR_PLACEHOLDER", f'"{cursor}"' if cursor else "null"
                )
            )

            result = client.execute(query)
            search = result.get("search")
            edges = search.get("edges")
            for node in edges:
                results.append(node.get("node"))
            logger.info(f"Total results: {len(results)}")

            if not search.get("pageInfo").get("hasNextPage"):
                break

            cursor = search.get("pageInfo").get("endCursor")

        return results

    def convert_issues_to_documents(
        self, items: list[dict[str, Any]]
    ) -> list[Document]:
        """Convert GitHub issues to LangChain documents.

        This function transforms GitHub issue data into LangChain Document objects,
        preserving issue-specific metadata and content structure including labels,
        state information, and comments.

        Args:
            items: List of GitHub issue items as dictionaries

        Returns:
            List of LangChain Document objects formatted for vector storage
        """
        logger = get_dagster_logger()
        documents = []

        logger.info(f"Starting conversion of {len(items)} issues to documents")
        for item in items:
            try:
                metadata = {
                    "source": "github_issue",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "number": item.get("number"),
                    "state": item.get("state"),
                    "created_at": item.get("createdAt"),
                    "closed_at": item.get("closedAt"),
                    "state_reason": item.get("stateReason"),
                    "reaction_count": item.get("reactions", {}).get(
                        "totalCount", 0
                    ),
                }

                content_parts = [
                    f"Title: {item.get('title', '')}",
                    f"State: {item.get('state', '')}",
                    f"Description: {item.get('bodyText', '')}",
                ]

                if "labels" in item and "nodes" in item["labels"]:
                    labels = [label["name"] for label in item["labels"]["nodes"]]
                    if labels:
                        content_parts.append(f"Labels: {', '.join(labels)}")

                if "comments" in item and "nodes" in item["comments"]:
                    for comment in item["comments"]["nodes"]:
                        if comment and "body" in comment:
                            content_parts.append(f"Comment: {comment['body']}")

                document = Document(
                    page_content="\n\n".join(content_parts), metadata=metadata
                )
                documents.append(document)

                logger.info(
                    f"Processed issue #{item.get('number')}: {item.get('title')} ({metadata['state']})"
                )
            except Exception as e:
                logger.error(f"Error processing issue #{item.get('number')}: {e}")
                continue

        logger.info(
            f"Completed conversion of {len(items)} issues to {len(documents)} documents"
        )
        return documents

    def convert_discussions_to_documents(
        self, items: list[dict[str, Any]]
    ) -> list[Document]:
        """Convert GitHub discussions to LangChain documents.

        This function transforms GitHub discussion data into LangChain Document objects,
        preserving the hierarchical structure of discussions including answers and comments.
        It's specifically designed to handle the Q&A format and category information
        that's unique to GitHub discussions.

        Args:
            items: List of GitHub discussion items as dictionaries

        Returns:
            List of LangChain Document objects formatted for vector storage
        """
        logger = get_dagster_logger()
        documents = []

        logger.info(
            f"Starting conversion of {len(items)} discussions to documents"
        )
        for item in items:
            try:
                metadata = {
                    "source": "github_discussion",
                    "id": item.get("id"),
                    "url": item.get("url"),
                    "created_at": item.get("createdAt"),
                    "title": item.get("title"),
                    "number": item.get("number"),
                    "category": item.get("category", {}).get("name"),
                    "is_answered": item.get("isAnswered", False),
                    "upvote_count": item.get("upvoteCount", 0),
                }

                content_parts = [
                    f"Title: {item.get('title', '')}",
                    f"Category: {item.get('category', {}).get('name', 'Uncategorized')}",
                    f"Question: {item.get('bodyText', '')}",
                ]

                if item.get("answer"):
                    content_parts.append(
                        f"Accepted Answer: {item['answer'].get('bodyText', '')}"
                    )

                if "comments" in item and "nodes" in item["comments"]:
                    for comment in item["comments"]["nodes"]:
                        if comment and "bodyText" in comment:
                            # Skip if this comment is the same as the accepted answer
                            if not item.get("answer") or comment[
                                "bodyText"
                            ] != item["answer"].get("bodyText"):
                                content_parts.append(
                                    f"Comment: {comment['bodyText']}"
                                )

                if "labels" in item and "nodes" in item["labels"]:
                    labels = [label["name"] for label in item["labels"]["nodes"]]
                    if labels:
                        content_parts.append(f"Labels: {', '.join(labels)}")

                doc = Document(
                    page_content="\n\n".join(content_parts), metadata=metadata
                )
                documents.append(doc)

                logger.info(
                    f"Processed discussion #{item.get('number')}: {item.get('title')} ({metadata['category']})"
                )
            except Exception as e:
                logger.error(
                    f"Error processing discussion #{item.get('number')}: {e}"
                )
                continue

        logger.info(
            f"Completed conversion of {len(items)} discussions to {len(documents)} documents"
        )
        return documents
