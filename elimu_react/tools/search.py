"""
Serper.dev-backed search tool with Kenyan educational bias.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from .base import Tool


class SearchTool(Tool):
    """Google search via Serper.dev, optimized for Kenyan educators."""

    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        educational_focus: bool = True,
        prioritize_kenyan_sources: bool = True,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.educational_focus = educational_focus
        self.prioritize_kenyan_sources = prioritize_kenyan_sources
        self.base_url = "https://google.serper.dev/search"

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return """Search Google for contextual information.

Parameters:
- query (str, required): the search query

Returns a formatted list of results (title, link, snippet). Prioritises Kenyan,
East African, and reputable educational sources when available.
"""

    def execute(self, query: str) -> str:
        if not query or not query.strip():
            return "Error: search query cannot be empty."

        enriched_query = self._enrich_query(query)
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }
            payload = {"q": enriched_query, "num": 10}
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return self._format_results(data, enriched_query)
        except requests.exceptions.Timeout:
            return f"Error: search timed out after {self.timeout}s."
        except requests.exceptions.RequestException as exc:
            return f"Error: search request failed: {exc}"
        except json.JSONDecodeError as exc:
            return f"Error: could not parse search response: {exc}"

    # ------------------------------------------------------------------ helpers

    def _enrich_query(self, query: str) -> str:
        q = query.strip()
        if not self.educational_focus:
            return q

        lowered = q.lower()
        needs_kenya = self.prioritize_kenyan_sources and "kenya" not in lowered
        if needs_kenya:
            q += " Kenya"

        if any(term in lowered for term in ["lesson", "curriculum", "education", "teacher"]):
            q += " classroom"
        return q

    def _format_results(self, data: Dict[str, Any], query: str) -> str:
        lines = [f"Search results for: {query}", "=" * 80]
        organic = data.get("organic") or []

        if self.prioritize_kenyan_sources:
            organic = self._prioritize_kenyan_domains(organic)

        if not organic:
            return f"No search results found for: {query}"

        for idx, result in enumerate(organic, start=1):
            title = result.get("title", "No title")
            link = result.get("link", "No link")
            snippet = result.get("snippet", "No description available")
            lines.extend(
                [
                    f"\n[{idx}] {title}",
                    f"URL: {link}",
                    f"Snippet: {snippet}",
                    "-" * 80,
                ]
            )

        answer_box = data.get("answerBox")
        if answer_box:
            lines.append("\nANSWER BOX")
            lines.append("=" * 80)
            if "answer" in answer_box:
                lines.append(f"Answer: {answer_box['answer']}")
            if "snippet" in answer_box:
                lines.append(f"Snippet: {answer_box['snippet']}")

        knowledge_graph = data.get("knowledgeGraph")
        if knowledge_graph:
            lines.append("\nKNOWLEDGE GRAPH")
            lines.append("=" * 80)
            for key in ["title", "description"]:
                if key in knowledge_graph:
                    lines.append(f"{key.title()}: {knowledge_graph[key]}")

        return "\n".join(lines)

    def _prioritize_kenyan_domains(self, results: Any) -> Any:
        kenyan_domains = (
            "kicd.ac.ke",
            "go.ke",
            "ac.ke",
            "co.ke",
            "or.ke",
            "nation.africa",
            "standardmedia.co.ke",
        )

        def is_kenyan(link: Optional[str]) -> bool:
            if not link:
                return False
            lower_link = link.lower()
            return any(domain in lower_link for domain in kenyan_domains)

        prioritized = [res for res in results if is_kenyan(res.get("link"))]
        remainder = [res for res in results if res not in prioritized]
        return prioritized + remainder

