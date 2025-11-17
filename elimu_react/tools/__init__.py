"""
Tool registry for the Elimu ReAct agent.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .base import Tool
from .search import SearchTool
from .scrape import ScrapeTool


class ToolManager:
    """Simple in-memory registry of available tools."""

    def __init__(self) -> None:
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"Tool '{tool.name}' already registered.")
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self.tools.values())

    def get_tool_descriptions(self) -> str:
        if not self.tools:
            return "No tools available."

        lines = ["Available tools:\n"]
        for tool in self.tools.values():
            lines.append("\n" + "-" * 80)
            lines.append(f"Tool: {tool.name}")
            lines.append("-" * 80)
            lines.append(tool.description)
        return "\n".join(lines)

    def execute_tool(self, name: str, **kwargs) -> str:
        tool = self.get_tool(name)
        if not tool:
            available = ", ".join(sorted(self.tools.keys()))
            return f"Error: Tool '{name}' not found. Available tools: {available}"
        try:
            return tool.execute(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            return f"Error executing tool '{name}': {exc}"


__all__ = ["ToolManager", "Tool", "SearchTool", "ScrapeTool"]

