"""
Elimu-specific ReAct agent factory.

This package adapts the upstream `web_research_agent` architecture so that the
educational CLI can rely on the same ReAct (Reasoning+Acting) loop while
layering Kenyan classroom guidance.
"""

from typing import Optional, Sequence

from config.config import get_config
from .llm import LLMInterface
from .agent import ReActAgent
from .tools import (
    ToolManager,
    SearchTool,
    ScrapeTool,
)

DEFAULT_MODEL_CANDIDATES: Sequence[str] = (
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-8b",
)


def build_elimu_agent(
    temperature: Optional[float] = None,
    max_iterations: Optional[int] = None,
    max_tool_output_length: Optional[int] = None,
) -> ReActAgent:
    """
    Construct a ReAct agent configured for Elimu Research Assistant.

    Args:
        temperature: Optional override for model temperature.
        max_iterations: Optional override for reasoning iterations.
        max_tool_output_length: Optional override for observation truncation.

    Returns:
        Configured ReActAgent instance.
    """

    config = get_config()

    gemini_key = config.get("gemini_api_key")
    if not gemini_key:
        raise ValueError("Gemini API key is not configured. Run `elimu config` first.")

    serper_key = config.get("serper_api_key")
    if not serper_key:
        raise ValueError("Serper API key is not configured. Run `elimu config` first.")

    desired_models = [
        config.get("model_name"),
        config.get("model_fallback"),
        *DEFAULT_MODEL_CANDIDATES,
    ]

    llm = LLMInterface(
        api_key=gemini_key,
        model_candidates=[model for model in desired_models if model],
        temperature=temperature or config.get("model_temperature", 0.15),
    )

    tool_manager = ToolManager()
    tool_manager.register_tool(
        SearchTool(
            api_key=serper_key,
            timeout=config.get("timeout", 30),
            educational_focus=config.get("educational_focus", True),
            prioritize_kenyan_sources=config.get("prioritize_kenyan_sources", True),
        )
    )
    tool_manager.register_tool(
        ScrapeTool(
            timeout=config.get("timeout", 30),
            max_chars=config.get("max_tool_output_length", 6000),
        )
    )

    return ReActAgent(
        llm=llm,
        tool_manager=tool_manager,
        max_iterations=max_iterations or config.get("max_iterations", 12),
        max_tool_output_length=max_tool_output_length
        or config.get("max_tool_output_length", 6000),
    )


__all__ = ["build_elimu_agent", "ReActAgent"]

