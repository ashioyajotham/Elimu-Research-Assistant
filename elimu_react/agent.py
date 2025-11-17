"""
Elimu-flavoured ReAct agent.

Based on the upstream `web_research_agent` implementation but tuned for Kenyan
educational use cases (lesson plans, handouts, case studies, assessments).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .llm import LLMInterface
from .tools import ToolManager


@dataclass
class Step:
    """Represents a single reasoning/action step."""

    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None


class ReActAgent:
    """Reasoning + Acting loop controller."""

    def __init__(
        self,
        llm: LLMInterface,
        tool_manager: ToolManager,
        max_iterations: int = 15,
        max_tool_output_length: int = 5000,
    ) -> None:
        self.llm = llm
        self.tool_manager = tool_manager
        self.max_iterations = max_iterations
        self.max_tool_output_length = max_tool_output_length
        self.steps: List[Step] = []

    def run(self, task: str) -> str:
        """Execute the ReAct loop for a single task."""
        self.steps = []

        for _ in range(self.max_iterations):
            prompt = self._build_prompt(task)
            response = self.llm.generate(prompt)
            thought, action, action_input, final_answer = self._parse_response(response)

            step = Step(thought=thought)

            if final_answer:
                self.steps.append(step)
                return final_answer

            if action and action_input is not None:
                step.action = action
                step.action_input = action_input
                observation = self._execute_action(action, action_input)
                step.observation = observation
                self.steps.append(step)
            else:
                step.observation = (
                    "No valid action detected. Use an available tool or provide Final Answer."
                )
                self.steps.append(step)

        return self._generate_best_effort_answer(task)

    # ---- Prompting -----------------------------------------------------------------

    def _build_prompt(self, task: str) -> str:
        prompt_parts: List[str] = []
        prompt_parts.append(self._system_instructions())
        prompt_parts.append("\n" + self.tool_manager.get_tool_descriptions())
        prompt_parts.append(f"\n\nTASK:\n{task}")

        if self.steps:
            prompt_parts.append("\n\nPREVIOUS STEPS:")
            for idx, step in enumerate(self.steps, start=1):
                prompt_parts.append(f"\nStep {idx}:")
                prompt_parts.append(f"Thought: {step.thought}")
                if step.action:
                    prompt_parts.append(f"Action: {step.action}")
                    prompt_parts.append(
                        f"Action Input: {self._format_action_input(step.action_input)}"
                    )
                if step.observation:
                    obs = step.observation
                    if len(obs) > self.max_tool_output_length:
                        obs = (
                            obs[: self.max_tool_output_length]
                            + f"\n... [truncated from {len(step.observation)} chars]"
                        )
                    prompt_parts.append(f"Observation: {obs}")

        prompt_parts.append("\n\nWhat is your next step?")
        return "\n".join(prompt_parts)

    @staticmethod
    def _system_instructions() -> str:
        return """You are the Elimu Research Assistant—an AI co-teacher for Kenyan classrooms.

You strictly follow the ReAct (Reasoning + Acting) loop so that every move is auditable.
You always strive to produce classroom-ready artefacts (case studies, lesson plans,
handouts, assessments) rich with Kenyan context, credible citations, and clear
learning objectives.

For each cycle:
1. Thought: explain what you will do next (never skip this).
2. Action: choose one of the available tools.
3. Action Input: provide JSON parameters for that tool.
4. Observation: the tool result (provided to you) informs the next Thought.

When you have enough information, provide:
Thought: why you can now answer with confidence.
Final Answer: a structured response tailored for teachers (include sections,
Kenyan examples, discussion prompts, and cite sources inline).

Rules:
- Never fabricate URLs or statistics—only cite what the tools reveal.
- Prefer Kenyan, East African, or African Union data before global sources.
- Encourage pedagogy: highlight learning objectives, classroom activities, and assessment angles.
- For case studies, include background, stakeholders, challenges, and discussion questions.
- Maintain professional yet encouraging tone suitable for educators.
"""

    # ---- Parsing -------------------------------------------------------------------

    def _parse_response(
        self, response: str
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        thought = ""
        action = None
        action_input = None
        final_answer = None

        thought_match = re.search(
            r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if thought_match:
            thought = thought_match.group(1).strip()

        final_answer_match = re.search(
            r"Final Answer:\s*(.+)", response, re.DOTALL | re.IGNORECASE
        )
        if final_answer_match:
            final_answer = final_answer_match.group(1).strip()
            return thought, None, None, final_answer

        action_match = re.search(r"Action:\s*(\w+)", response, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()

        action_input_match = re.search(
            r"Action Input:\s*(\{.+?\}|\{.+)", response, re.DOTALL | re.IGNORECASE
        )
        if action_input_match:
            action_input_str = action_input_match.group(1).strip()
            action_input = self._parse_action_input(action_input_str)

        return thought, action, action_input, final_answer

    def _parse_action_input(self, raw_input: str) -> Optional[Dict[str, Any]]:
        try:
            brace_count = 0
            end_index = 0
            for idx, char in enumerate(raw_input):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_index = idx + 1
                        break
            if end_index:
                raw_input = raw_input[:end_index]
            return json.loads(raw_input)
        except Exception:
            return self._parse_action_input_fallback(raw_input)

    @staticmethod
    def _parse_action_input_fallback(raw_input: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        patterns = [
            r'"(\w+)":\s*"([^"]+)"',
            r"'(\w+)':\s*'([^']+)'",
            r"(\w+):\s*\"([^\"}]+)\"",
            r"(\w+)=([^,}\s]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, raw_input):
                key, value = match.groups()
                params[key] = value
        return params

    @staticmethod
    def _format_action_input(action_input: Optional[Dict[str, Any]]) -> str:
        if not action_input:
            return "{}"
        try:
            return json.dumps(action_input, indent=2, ensure_ascii=False)
        except Exception:
            return str(action_input)

    # ---- Tool Execution ------------------------------------------------------------

    def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        return self.tool_manager.execute_tool(action, **action_input)

    def _generate_best_effort_answer(self, task: str) -> str:
        prompt = f"""The agent reached its iteration limit while researching:

{task}

Use the following step trace to craft the most complete educational answer you can:
"""
        for idx, step in enumerate(self.steps, start=1):
            prompt += f"\nStep {idx} Thought: {step.thought}\n"
            if step.observation:
                prompt += f"Observation: {step.observation[:800]}\n"

        prompt += "\nRespond with a structured Kenyan classroom resource."
        return self.llm.generate(prompt)

    # ---- Tracing -------------------------------------------------------------------

    def get_execution_trace(self) -> List[Dict[str, Any]]:
        trace: List[Dict[str, Any]] = []
        for idx, step in enumerate(self.steps, start=1):
            entry: Dict[str, Any] = {"step": idx, "thought": step.thought}
            if step.action:
                entry["action"] = step.action
                entry["action_input"] = step.action_input
            if step.observation:
                entry["observation"] = (
                    step.observation[:500] + "..."
                    if len(step.observation or "") > 500
                    else step.observation
                )
            trace.append(entry)
        return trace

