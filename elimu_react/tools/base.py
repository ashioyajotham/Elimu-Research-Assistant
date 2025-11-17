"""
Abstract base class for Elimu tools.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier used by the LLM."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Markdown description shared with the LLM."""

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool and return a textual observation."""

