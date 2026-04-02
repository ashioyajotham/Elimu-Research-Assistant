"""
console_ui.py — Elimu Research Assistant terminal theme.

Colour palette (Kenyan landscape):
  Primary   #2E7D32  deep forest green
  Accent    #F9A825  savanna gold
  Info      #0277BD  highland sky blue
  Error     #C62828  deep red
  Muted     grey62   dimmed/secondary text
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.rule import Rule
from rich import box
import logging
from typing import List, Dict, Any, Optional
import json

# ── Theme constants ───────────────────────────────────────────────────────────

_P = "#2E7D32"    # primary   (forest green)
_A = "#F9A825"    # accent    (savanna gold)
_I = "#0277BD"    # info      (sky blue)
_E = "#C62828"    # error     (deep red)
_S = "#43A047"    # success   (bright green)
_W = "#F57F17"    # warning   (amber)
_D = "grey62"     # dim/muted

BORDER_PRIMARY  = "green"
BORDER_ACCENT   = "yellow"
BORDER_INFO     = "cyan"
BORDER_SUCCESS  = "green"
BORDER_ERROR    = "red"
BORDER_WARNING  = "yellow"

__all__ = [
    "console",
    "_P", "_A", "_I", "_E", "_S", "_W", "_D",
    "BORDER_PRIMARY", "BORDER_ACCENT", "BORDER_INFO",
    "BORDER_SUCCESS", "BORDER_ERROR", "BORDER_WARNING",
    "BOX_PANEL", "BOX_TABLE", "BOX_HEAVY",
    "RichHandler", "configure_logging",
    "rule", "display_title", "display_task_header",
    "create_progress_context", "display_result",
    "display_completion_message", "display_plan",
    "info", "success", "warn", "error",
]

# Box styles used across the UI
BOX_PANEL   = box.ROUNDED
BOX_TABLE   = box.SIMPLE_HEAD
BOX_HEAVY   = box.HEAVY_HEAD

# ── Console singleton ─────────────────────────────────────────────────────────

console = Console()

# ── Logging integration ───────────────────────────────────────────────────────

class RichHandler(logging.Handler):
    """Logging handler that emits via Rich, using the Elimu colour theme."""

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self.console = console

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                style = f"bold {_E}"
            elif record.levelno >= logging.WARNING:
                style = _W
            elif record.levelno >= logging.INFO:
                style = _S
            else:
                style = _I
            self.console.print(f"[{style}]{record.levelname}:[/] {msg}")
        except Exception:
            self.handleError(record)


def configure_logging() -> None:
    """Replace root logger handlers with the Rich handler."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = RichHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)

    for name in ("elimu_react.agent", "elimu_react.tools.search", "elimu_react.tools.scrape"):
        lg = logging.getLogger(name)
        for h in list(lg.handlers):
            lg.removeHandler(h)
        lg.propagate = True

# ── UI primitives ─────────────────────────────────────────────────────────────

def rule(title: str = "", style: str = _P) -> None:
    """Print a themed horizontal rule."""
    console.print(Rule(title, style=style))


def display_title(title: str) -> None:
    """A bold primary-coloured title panel."""
    console.print(Panel(
        f"[bold {_P}]{title}[/]",
        border_style=BORDER_PRIMARY,
        box=BOX_PANEL,
    ))


def display_task_header(task_number: int, total_tasks: int, task_description: str) -> None:
    """Numbered task header with accent styling."""
    console.print()
    console.print(Rule(f"[bold {_A}]Task {task_number} of {total_tasks}[/]", style=_A))
    console.print(Panel(
        f"[{_A}]{task_description}[/]",
        title=f"[bold {_A}]Task {task_number}/{total_tasks}[/]",
        border_style=BORDER_ACCENT,
        box=BOX_PANEL,
    ))
    console.print()


def create_progress_context() -> Progress:
    """Themed progress bar context."""
    return Progress(
        SpinnerColumn(style=f"bold {_P}"),
        TextColumn(f"[bold {_P}]{{task.description}}"),
        BarColumn(bar_width=None, style=_P, complete_style=_S),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )


# ── Result display ────────────────────────────────────────────────────────────

def display_result(step_number: int, step_description: str, status: str, output: Any) -> None:
    """Display a step result with themed status colours."""
    if status == "success":
        status_display = f"[bold {_S}]SUCCESS[/]"
        header_color = _S
    else:
        status_display = f"[bold {_E}]ERROR[/]"
        header_color = _E

    console.print(f"\n[bold {header_color}]Step {step_number}:[/] {step_description}")
    console.print(f"Status: {status_display}")

    if status == "error":
        console.print(Panel(str(output), title="Error", border_style=BORDER_ERROR, box=BOX_PANEL))
        return

    if isinstance(output, dict):
        if "error" in output:
            console.print(Panel(output["error"], title="Error", border_style=BORDER_ERROR, box=BOX_PANEL))
        elif "content" in output:
            console.print(f"[bold]Source:[/] {output.get('title', 'Web content')} ({output.get('url', '')})")
            md = Markdown(output["content"][:500] + ("…" if len(output["content"]) > 500 else ""))
            console.print(md)
        elif "results" in output:
            console.print(f"[bold]Query:[/] {output.get('query', '')}")
            t = Table(show_header=True, header_style=f"bold {_P}", box=BOX_TABLE)
            t.add_column("#", style=_D, width=3)
            t.add_column("Title")
            t.add_column("URL", style=_I)
            for i, r in enumerate(output.get("results", []), 1):
                t.add_row(str(i), r.get("title", ""), r.get("link", ""))
            console.print(t)
        else:
            console.print_json(json.dumps(output))
    elif isinstance(output, str):
        import re
        if output.startswith("```"):
            lang_match = re.match(r"```(\w+)", output)
            language = lang_match.group(1) if lang_match else "text"
            code = re.sub(r"```\w*\n", "", output).replace("```", "")
            console.print(Syntax(code, language, theme="monokai"))
        else:
            console.print(output)
    else:
        console.print(str(output))


def display_completion_message(task_description: str, output_file: str) -> None:
    """Success panel at task completion."""
    console.print(Panel(
        f"[bold {_S}]Complete[/]\n\n"
        f"{task_description}\n\n"
        f"[{_D}]Saved to:[/] [{_I}]{output_file}[/]",
        title=f"[bold {_S}]Task Done[/]",
        border_style=BORDER_SUCCESS,
        box=BOX_PANEL,
    ))


# ── Info / warning / error helpers ───────────────────────────────────────────

def info(msg: str) -> None:
    console.print(f"[{_I}]{msg}[/]")

def success(msg: str) -> None:
    console.print(f"[bold {_S}][OK][/] {msg}")

def warn(msg: str) -> None:
    console.print(f"[{_W}][!] {msg}[/]")

def error(msg: str) -> None:
    console.print(f"[bold {_E}][ERR][/] {msg}")


# ── Plan display ──────────────────────────────────────────────────────────────

def display_plan(plan_steps: List[Dict[str, Any]]) -> None:
    """Render plan steps as a themed table."""
    t = Table(
        title=f"[bold {_P}]Execution Plan[/]",
        show_header=True,
        header_style=f"bold {_A}",
        box=BOX_TABLE,
        border_style=BORDER_PRIMARY,
    )
    t.add_column("#", style=_D, width=4)
    t.add_column("Step")
    t.add_column("Tool", style=_I)
    for i, step in enumerate(plan_steps, 1):
        t.add_row(str(i), step.get("description", ""), step.get("tool", ""))
    console.print(t)
    console.print()
