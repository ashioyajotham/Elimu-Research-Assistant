from typing import Any, List, Dict


def format_react_markdown(task: str, final_answer: str, trace: List[Dict[str, Any]]) -> str:
    """
    Turn a ReAct run into a markdown report with final answer plus trace.
    """
    lines = [f"# {task}", "", "## Final Answer", ""]
    lines.append(final_answer.strip() if final_answer.strip() else "_No answer generated._")

    if trace:
        lines.append("\n## ReAct Trace\n")
        for step in trace:
            lines.append(f"### Step {step.get('step')}")
            lines.append(f"- Thought: {step.get('thought', '')}")
            if step.get("action"):
                lines.append(f"- Action: {step['action']}")
                if step.get("action_input"):
                    lines.append(f"- Action Input: `{step['action_input']}`")
            if step.get("observation"):
                lines.append(f"- Observation: {step['observation']}")
            lines.append("")

    return "\n".join(lines)

