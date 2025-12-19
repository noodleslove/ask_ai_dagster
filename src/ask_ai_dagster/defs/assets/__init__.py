import dagster as dg

from ask_ai_dagster.defs.assets.ingestion import (
    github_issues_raw,
    github_issues_embeddings,
    github_discussions_raw,
    github_discussions_embeddings,
    docs_scrape_raw,
    docs_embedding,
)


@dg.definitions
def assets() -> dg.Definitions:
    return dg.Definitions(
        assets={
            "github_issues_raw": github_issues_raw,
            "github_issues_embeddings": github_issues_embeddings,
            "github_discussions_raw": github_discussions_raw,
            "github_discussions_embeddings": github_discussions_embeddings,
            "docs_scrape_raw": docs_scrape_raw,
            "docs_embedding": docs_embedding,
        }
    )
