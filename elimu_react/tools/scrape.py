"""
Fetch and cleanly extract web content for the ReAct agent.
"""

from __future__ import annotations

from typing import Optional
import requests
from bs4 import BeautifulSoup
import html2text

from .base import Tool


class ScrapeTool(Tool):
    """Extract readable text from a URL or fallback to an informative error."""

    def __init__(self, timeout: int = 30, max_chars: int = 6000) -> None:
        self.timeout = timeout
        self.max_chars = max_chars
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.bypass_tables = False
        self.html_converter.ignore_images = True

    @property
    def name(self) -> str:
        return "scrape"

    @property
    def description(self) -> str:
        return """Fetch the content of a URL and return clean text.

Parameters:
- url (str, required): the page to fetch.
- extract (str, optional): "summary" to shorten, default full article text.
"""

    def execute(self, url: str, extract: str = "main") -> str:
        if not url:
            return "Error: URL required for scrape tool."

        response = self._fetch(url)
        if isinstance(response, str):
            return response

        html = response
        text = (
            self._extract_summary(html)
            if extract == "summary"
            else self._extract_main_content(html)
        )
        if len(text) > self.max_chars:
            text = text[: self.max_chars] + f"\n... [truncated to {self.max_chars} chars]"
        return text

    # ------------------------------------------------------------------ helpers

    def _fetch(self, url: str) -> str | bytes:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        }
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.exceptions.Timeout:
            return f"Error: fetching {url} timed out after {self.timeout}s."
        except requests.exceptions.RequestException as exc:
            return f"Error: could not fetch {url}: {exc}"

    def _extract_main_content(self, page: bytes) -> str:
        soup = BeautifulSoup(page, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        selectors = [
            "article",
            "main",
            ".content",
            "#content",
            ".post",
            ".entry-content",
        ]

        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                return node.get_text(separator="\n").strip()

        text = soup.get_text(separator="\n")
        return text.strip()

    def _extract_summary(self, page: bytes) -> str:
        markdown = self.html_converter.handle(page.decode("utf-8", errors="ignore"))
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        return "\n".join(lines[:40])

