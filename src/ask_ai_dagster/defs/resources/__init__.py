import dagster as dg

from ask_ai_dagster.defs.resources.github import GithubResource
from ask_ai_dagster.defs.resources.pinecone import PineconeResource
from ask_ai_dagster.defs.resources.scraper import SitemapScraperResource


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "github": GithubResource(github_token=dg.EnvVar("GITHUB_TOKEN")),
            "scraper": SitemapScraperResource(sitemap_url=dg.EnvVar("SITEMAP_URL")),
            "pinecone": PineconeResource(
                pinecone_api_key=dg.EnvVar("PINECONE_API_KEY"),
                openai_api_key=dg.EnvVar("OPENAI_API_KEY"),
            ),
        }
    )
