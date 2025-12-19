import dagster as dg
from dagster_openai import OpenAIResource

from ask_ai_dagster.defs.io_managers import document_io_manager
from ask_ai_dagster.defs.resources.github import GithubResource
from ask_ai_dagster.defs.resources.pinecone import PineconeResource
from ask_ai_dagster.defs.resources.scraper import SitemapScraperResource


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "github": GithubResource(github_token=dg.EnvVar("GITHUB_TOKEN")),
            "scraper": SitemapScraperResource(
                sitemap_url=dg.EnvVar("SITEMAP_URL")
            ),
            "pinecone": PineconeResource(
                pinecone_api_key=dg.EnvVar("PINECONE_API_KEY"),
                openai_api_key=dg.EnvVar("OPENAI_API_KEY"),
            ),
            "openai": OpenAIResource(
                api_key=dg.EnvVar("OPENAI_API_KEY"),
            ),
            "document_io_manager": document_io_manager.configured(
                {"base_dir": "data/documents"}
            ),
        }
    )
