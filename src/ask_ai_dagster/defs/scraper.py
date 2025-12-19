from typing import Optional
import dagster as dg
import requests

from bs4 import BeautifulSoup
from langchain_core.documents import Document


class SitemapScraperResource(dg.ConfigurableResource):
    """Resource for scraping sitemaps."""

    sitemap_url: str
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def parse_sitemap(self) -> list[dict]:
        """Extract URLs from a sitemap."""
        response = requests.get(self.sitemap_url, headers=self.headers)
        soup = BeautifulSoup(response.content, "xml")
        return list(
            set(loc.text.strip() for loc in soup.find_all("loc") if loc.text.strip())
        )

    def scrape_url(self, url: str) -> Optional[Document]:
        """Scrape a URL and return a Document."""
        logger = dg.get_dagster_logger()
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            logger.info(f"Scraped URL: {url}")

            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            title = soup.title.string if soup.title else ""
            main_content = soup.find("main") or soup.find("article") or soup.body

            if main_content:
                content = []
                for elem in main_content.stripped_strings:
                    if elem.strip():
                        content.append(elem.strip())
                text_content = "\n".join(content)
            else:
                text_content = "\n".join(
                    s.strip() for s in soup.stripped_strings if s.strip()
                )

            return Document(
                page_content=text_content, metadata={"source": url, "title": title}
            )
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return None
