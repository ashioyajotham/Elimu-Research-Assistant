import re
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


def _md_to_html(md: str) -> str:
    """Minimal markdown-to-HTML converter for the subset used in ReAct output."""
    try:
        import markdown as _markdown
        return _markdown.markdown(md, extensions=["tables", "fenced_code"])
    except ImportError:
        pass

    # Fallback: manual conversion for headings, bold, italic, lists, code, hr
    html = re.sub(r"&", "&amp;", md)
    html = re.sub(r"<", "&lt;", html)
    html = re.sub(r">", "&gt;", html)

    # Fenced code blocks
    html = re.sub(r"```[^\n]*\n(.*?)```", r"<pre><code>\1</code></pre>", html, flags=re.DOTALL)
    # Inline code
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    # Bold + italic
    html = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", html)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Headings
    for level in range(4, 0, -1):
        html = re.sub(r"(?m)^{} (.+)$".format("#" * level), r"<h{0}>\1</h{0}>".format(level), html)
    # Horizontal rule
    html = re.sub(r"(?m)^---+$", "<hr>", html)
    # Unordered lists (wrap consecutive items)
    html = re.sub(r"(?m)^[-*] (.+)$", r"<li>\1</li>", html)
    html = re.sub(r"((?:<li>.*?</li>\s*)+)", r"<ul>\1</ul>", html, flags=re.DOTALL)
    # Ordered lists
    html = re.sub(r"(?m)^\d+\. (.+)$", r"<li>\1</li>", html)
    # Blank lines to paragraph breaks
    html = re.sub(r"\n{2,}", "</p><p>", html)
    html = f"<p>{html}</p>"

    return html


def format_react_html(task: str, final_answer: str, trace: List[Dict[str, Any]]) -> str:
    """Render a ReAct run as a self-contained HTML document."""
    answer_html = _md_to_html(final_answer.strip() if final_answer.strip() else "_No answer generated._")

    trace_html_parts = []
    for step in trace:
        n = step.get("step", "?")
        thought = re.sub(r"&", "&amp;", step.get("thought", ""))
        thought = re.sub(r"<", "&lt;", thought)
        thought = re.sub(r">", "&gt;", thought)
        parts = [f'<div class="step"><div class="step-num">Step {n}</div>']
        if thought:
            parts.append(f'<p><strong>Thought:</strong> {thought}</p>')
        if step.get("action"):
            parts.append(f'<p><strong>Action:</strong> <code>{step["action"]}</code></p>')
        if step.get("action_input"):
            ai = str(step["action_input"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f'<p><strong>Input:</strong> <code>{ai}</code></p>')
        if step.get("observation"):
            obs = str(step["observation"])[:400].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f'<details><summary>Observation</summary><pre>{obs}</pre></details>')
        parts.append("</div>")
        trace_html_parts.append("\n".join(parts))

    trace_section = ""
    if trace_html_parts:
        trace_section = (
            '<section class="trace"><h2>ReAct Trace</h2>'
            + "\n".join(trace_html_parts)
            + "</section>"
        )

    title_escaped = re.sub(r"<", "&lt;", re.sub(r"&", "&amp;", task))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title_escaped}</title>
<style>
:root{{--green:#2E7D32;--gold:#F9A825;--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;line-height:1.7;padding:2rem}}
header{{border-bottom:2px solid var(--gold);padding-bottom:1rem;margin-bottom:2rem}}
header h1{{color:var(--gold);font-size:1.4rem;font-weight:600}}
header p{{color:var(--muted);font-size:.85rem;margin-top:.25rem}}
section.answer{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.5rem 2rem;margin-bottom:2rem}}
section.answer h2{{color:var(--green);font-size:1rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:1rem}}
h1,h2,h3,h4{{color:var(--gold);margin:1rem 0 .4rem}}
p{{margin:.5rem 0}}
ul,ol{{padding-left:1.5rem;margin:.4rem 0}}
code{{background:#1c2128;border:1px solid var(--border);border-radius:4px;padding:.1em .4em;font-size:.9em}}
pre{{background:#1c2128;border:1px solid var(--border);border-radius:6px;padding:1rem;overflow-x:auto;margin:.5rem 0}}
pre code{{background:none;border:none;padding:0}}
strong{{color:#cdd9e5}}
hr{{border:none;border-top:1px solid var(--border);margin:1rem 0}}
section.trace{{margin-top:2rem}}
section.trace h2{{color:var(--green);font-size:1rem;text-transform:uppercase;letter-spacing:.08em;border-top:1px solid var(--border);padding-top:1rem;margin-bottom:1rem}}
.step{{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:1rem 1.25rem;margin:.6rem 0}}
.step-num{{color:var(--gold);font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem}}
details summary{{cursor:pointer;color:var(--muted);font-size:.85rem;margin-top:.4rem}}
details pre{{font-size:.8rem;margin-top:.4rem;max-height:200px;overflow-y:auto}}
</style>
</head>
<body>
<header>
  <h1>{title_escaped}</h1>
  <p>Generated by Elimu Research Assistant · ReAct + Gemini 2.x · Serper.dev</p>
</header>
<section class="answer">
  <h2>Answer</h2>
  {answer_html}
</section>
{trace_section}
</body>
</html>
"""

