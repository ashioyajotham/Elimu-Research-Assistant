#!/usr/bin/env python3
import os
import sys
import re
import click
from pathlib import Path
import time
import textwrap

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import from our modules using absolute imports
from utils.logger import get_logger, set_log_level
from config.config import get_config, init_config
from elimu_react import build_elimu_agent
from utils.react_output import format_react_markdown, format_react_html
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule
from rich import box
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from utils.console_ui import (
    _P, _A, _I, _E, _S, _W, _D,
    BORDER_PRIMARY, BORDER_ACCENT, BORDER_INFO, BORDER_SUCCESS, BORDER_ERROR, BORDER_WARNING,
    BOX_PANEL, BOX_TABLE,
    success, warn, error as ui_error,
)

# Import the new parser
from utils.task_parser import parse_tasks_from_file

logger = get_logger(__name__)
console = Console()

# ASCII Art Banner
BANNER = """
[bold #2E7D32]
███████╗██╗     ██╗███╗   ███╗██╗   ██╗
██╔════╝██║     ██║████╗ ████║██║   ██║
█████╗  ██║     ██║██╔████╔██║██║   ██║
██╔══╝  ██║     ██║██║╚██╔╝██║██║   ██║
███████╗███████╗██║██║ ╚═╝ ██║╚██████╔╝
╚══════╝╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝[/bold #2E7D32]
[bold #F9A825]  RESEARCH ASSISTANT[/bold #F9A825]  [grey62]─  ReAct · Gemini 2.x · Serper.dev[/grey62]
"""

# Read version — importlib.metadata is authoritative for installed packages;
# VERSION file is the fallback for editable/dev installs.
def _get_version() -> str:
    try:
        from importlib.metadata import version as _pkg_version
        return _pkg_version("elimu-research-assistant")
    except Exception:
        pass
    try:
        return (Path(__file__).parent / "VERSION").read_text().strip()
    except Exception:
        return "0.0.0"

__version__ = _get_version()


def display_banner():
    """Display the ASCII art banner."""
    console.print(BANNER)
    console.print(f"[{_D}]v{__version__}  ·  Ashioya Jotham Victor[/]\n")

def display_intro():
    """Display available commands."""
    table = Table(box=BOX_TABLE, show_header=False, border_style=BORDER_PRIMARY)
    table.add_column(justify="left", style=f"bold {_A}")
    table.add_column(style=_D)
    table.add_row("research <query>",      "Run a single research task")
    table.add_row("batch-research <file>", "Process tasks from a file")
    table.add_row("shell",                 "Interactive REPL with history")
    table.add_row("config",                "API keys and model settings")
    table.add_row("logs",                  "View agent log entries")
    table.add_row("history",               "View past research queries")
    console.print(Panel(
        table,
        border_style=BORDER_PRIMARY,
        box=BOX_PANEL,
        title=f"[bold {_P}]Elimu Research Assistant[/]",
        subtitle=f"[{_D}]elimu --help for full usage[/]",
    ))

def _sanitize_filename(query):
    """Sanitize a query string to create a valid filename."""
    # First, strip surrounding quotes if present
    if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
        query = query[1:-1]
    
    # Remove quotes and other invalid filename characters more aggressively
    invalid_chars = '"\'\\/:*?<>|'
    sanitized = ''.join(c for c in query if c not in invalid_chars)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Normalize multiple underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    
    # Limit length and trim whitespace
    sanitized = sanitized.strip()[:30]
    
    # Don't return an empty string
    if not sanitized:
        sanitized = "research_result"
        
    return sanitized

def _extract_section_text(content, titles):
    """Return the first matching markdown section for the provided titles."""
    if not content:
        return ""
    normalized = content.replace("\r\n", "\n")
    pattern = r"(?is)^##\s*(?:" + "|".join(re.escape(title) for title in titles) + r")\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, normalized, re.MULTILINE)
    return match.group(1).strip() if match else ""

def _shorten_text(value, limit=420):
    """Clean and shorten text for preview tables."""
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value).strip()
    if not cleaned:
        return ""
    try:
        return textwrap.shorten(cleaned, width=limit, placeholder="…")
    except ValueError:
        return cleaned[:limit]

def _extract_scope_items(content):
    """Capture bullet points listed under a Research Scope section."""
    if not content:
        return []
    normalized = content.replace("\r\n", "\n")
    scope_match = re.search(r"(?is)research scope[:\s]*\n(.*?)(?:\n\s*\n|$)", normalized)
    if not scope_match:
        return []
    scope_lines = []
    for line in scope_match.group(1).splitlines():
        stripped = line.strip(" -*•\t")
        if stripped:
            scope_lines.append(stripped)
        if len(scope_lines) >= 4:
            break
    return scope_lines

def _build_preview_panel(content, metadata=None):
    """Render a richer preview panel combining plan, findings, and scope."""
    if not content:
        return Panel("Preview unavailable – no content returned.", border_style=BORDER_ERROR, box=BOX_PANEL, title=f"[bold {_A}]Results Preview[/]")
    
    plan_text = _extract_section_text(content, ["Plan", "Research Plan"])
    findings_text = _extract_section_text(
        content,
        ["Research Findings", "Findings", "Content", "Results"]
    )
    summary_text = _extract_section_text(content, ["Summary", "Research Summary"])
    
    if not plan_text:
        plan_text = summary_text or content.split("\n\n", 1)[0]
    if not findings_text:
        findings_text = summary_text or content
    
    plan_snippet = _shorten_text(plan_text, 380) or "Plan details will appear here once the agent surfaces them."
    findings_snippet = _shorten_text(findings_text, 520)
    if not findings_snippet:
        findings_snippet = _shorten_text(content, 520)
    
    scope_items = _extract_scope_items(content)
    scope_block = "\n".join(f"• {item}" for item in scope_items) if scope_items else "• Scope metrics will show after a successful multi-step run."
    
    summary_block = _shorten_text(summary_text, 420) if summary_text else "Summary will populate when the agent returns a dedicated section."
    storage_info = ""
    if metadata and metadata.get("path"):
        storage_info = f"\nSaved to: {metadata['path']}"
    
    table = Table.grid(expand=True)
    table.add_column(ratio=1)
    table.add_column(ratio=1)
    table.add_row(
        f"[bold {_P}]Plan[/]\n{plan_snippet}",
        f"[bold {_P}]Key Findings[/]\n{findings_snippet}",
    )
    table.add_row(
        f"[bold {_P}]Research Scope[/]\n{scope_block}",
        f"[bold {_P}]Summary & Storage[/]\n{summary_block}{storage_info}",
    )

    return Panel(table, title=f"[bold {_A}]Results Preview[/]", border_style=BORDER_PRIMARY, box=BOX_PANEL)

def _format_react_markdown(task: str, final_answer: str, trace: list) -> str:
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

def _run_react_agent(task: str):
    agent = build_elimu_agent()
    final_answer = agent.run(task)
    trace = agent.get_execution_trace()
    return final_answer, trace

# Where users get their API keys
_KEY_URLS = {
    "gemini_api_key": "https://aistudio.google.com/apikey",
    "serper_api_key": "https://serper.dev/api-key",
}
_KEY_LABELS = {
    "gemini_api_key": "Gemini API key",
    "serper_api_key": "Serper API key",
}

def _show_key_status() -> None:
    """Print a key-status panel — used on bare `elimu` invocation."""
    config = get_config()
    keyring_ok = False
    try:
        import keyring as _kr  # noqa: F401
        keyring_ok = True
    except ImportError:
        pass

    rows = []
    all_set = True
    for key, label in _KEY_LABELS.items():
        value = config.get(key)
        if value:
            secure = keyring_ok and config.securely_stored_keys().get(key, False)
            source = "keyring" if secure else ".env"
            rows.append(f"  [{_S}][+][/] [bold]{label}[/]  [{_D}]({source})[/]")
        else:
            all_set = False
            url = _KEY_URLS[key]
            rows.append(f"  [{_E}][x][/] [bold]{label}[/]  [{_D}]not configured[/]  [{_I}]{url}[/]")

    status_body = "\n".join(rows)

    if all_set:
        console.print(Panel(
            status_body,
            title=f"[bold {_S}]API Keys[/]",
            border_style=BORDER_SUCCESS,
            box=BOX_PANEL,
        ))
    else:
        get_url  = f"  [{_I}]https://aistudio.google.com/apikey[/]  [{_D}]Gemini  (free tier)[/]\n"
        get_url += f"  [{_I}]https://serper.dev/api-key[/]          [{_D}]Serper  (2,500 free searches/month)[/]"
        console.print(Panel(
            status_body + f"\n\n[bold {_A}]Get your keys:[/]\n" + get_url +
            f"\n\n[{_D}]Then run:[/]  [bold]elimu config --api-key KEY --serper-key KEY[/]",
            title=f"[bold {_A}]Setup Required[/]",
            border_style=BORDER_WARNING,
            box=BOX_PANEL,
        ))

@click.group()
@click.version_option(__version__, message="%(prog)s version %(version)s")
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging")
@click.option('--no-config', is_flag=True, help="Skip API key checks (commands requiring API keys will fail)")
def cli(verbose, no_config):
    """
    Elimu Research Assistant - An intelligent educational content creation for Kenyan educators.
    
    Create localized, contextual educational materials that bridge the gap between 
    curriculum and students' lived experiences in Kenya.
    
    Features:
    • Generate lesson plans with Kenyan examples
    • Create student handouts using local context  
    • Develop case studies from real Kenyan scenarios
    • Design assessments with culturally relevant content
    • Prioritize credible Kenyan sources (KICD, universities, government)
    
    Example usage:
    \b
      elimu research "Create a Form 3 lesson on M-Pesa's economic impact"
      elimu batch-research lesson_requests.txt
      elimu shell  # Interactive mode
    """
    # Set log level based on verbose flag
    import logging
    
    if verbose:
        set_log_level(logging.INFO)  # Using the non-relative import
    
    # Store no_config flag in a global context so it can be accessed by other commands
    from click import get_current_context
    ctx = get_current_context()
    ctx.obj = ctx.obj or {}
    ctx.obj['no_config'] = no_config
        
    # Show banner + key status only on bare `elimu` (no subcommand)
    if len(sys.argv) == 1 or sys.argv[1] not in ['shell', 'research', 'batch-research', 'config']:
        display_banner()
        display_intro()
        _show_key_status()

def _check_required_keys(agent_initialization=False):
    """
    Check if required API keys are available and prompt for them if needed.
    
    Args:
        agent_initialization (bool): Whether this check is happening during agent initialization
            
    Returns:
        bool: True if all required keys are available (or were just added) or if --no-config was used
    """
    # Check if --no-config flag was set
    from click import get_current_context
    ctx = get_current_context()
    if ctx.obj and ctx.obj.get('no_config', False):
        if agent_initialization:
            console.print(f"[{_W}]Warning: no-config mode — API calls will fail.[/]")
        return True
    
    config = get_config()
    keyring_available = False
    
    try:
        import keyring  # noqa: F401
        keyring_available = True
    except ImportError:
        keyring_available = False
        if agent_initialization:
            console.print(Panel(
                f"[{_W}]Secure credential storage is optional but recommended.[/]\n\n"
                "Install [bold]keyring[/bold] to keep API keys in the Windows credential vault:\n"
                "[bold]pip install keyring[/bold]",
                title=f"[bold {_A}]Security Recommendation[/]",
                border_style=BORDER_WARNING,
                box=BOX_PANEL,
            ))
    
    required_keys = {
        'gemini_api_key': 'Gemini API key',
        'serper_api_key': 'Serper API key'
    }
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    if not missing_keys:
        return True
    
    if agent_initialization:
        console.print(Panel(
            f"[bold {_A}]Two API keys are required:[/]\n\n"
            f"  [bold]Gemini[/]  [{_I}]https://aistudio.google.com/apikey[/]  [{_D}]free tier available[/]\n"
            f"  [bold]Serper[/]  [{_I}]https://serper.dev/api-key[/]          [{_D}]2,500 free searches/month[/]\n\n"
            f"[{_D}]You will be prompted for each key now. "
            f"Keys are stored in the system keyring by default — never written to disk as plaintext.[/]",
            title=f"[bold {_A}]Setup Required[/]",
            border_style=BORDER_WARNING,
            box=BOX_PANEL,
        ))
    
    secure_storage_available = keyring_available and config.get('use_keyring', True)
    
    for key, display_name in required_keys.items():
        if key not in missing_keys:
            continue
            
        value = ""
        url = _KEY_URLS.get(key, "")
        hint = f" ({url})" if url else ""
        while not value:
            value = click.prompt(f"Enter your {display_name}{hint}", hide_input=True).strip()
            if not value:
                console.print(f"[{_E}]API key cannot be empty.[/]")

        stored_securely = False
        if secure_storage_available:
            use_secure = click.confirm(
                f"Store the {display_name} in the system keyring? (recommended)",
                default=True,
                show_default=True,
            )
            if use_secure:
                stored_securely = config.update(key, value, store_in_keyring=True)
                if stored_securely:
                    console.print(f"[bold {_S}][+][/] {display_name} stored securely.")
                else:
                    console.print(f"[{_W}][!]  Keyring unavailable — falling back to .env file.[/]")
        
        if not stored_securely:
            config.update(key, value, store_in_keyring=False)
            _save_to_env_file(key, value)
    
    return True

def _save_to_env_file(key, value):
    """Save a key-value pair to the .env file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Convert config key to environment variable name
    env_var = None
    config = get_config()
    
    # Try different ways to access ENV_MAPPING based on the config object type
    if hasattr(config, 'ENV_MAPPING'):
        # Direct access to ENV_MAPPING attribute
        env_mapping = config.ENV_MAPPING
    elif hasattr(config, '__class__') and hasattr(config.__class__, 'ENV_MAPPING'):
        # Class-level attribute
        env_mapping = config.__class__.ENV_MAPPING
    else:
        # Hard-coded fallback mapping
        env_mapping = {
            "GEMINI_API_KEY": "gemini_api_key",
            "SERPER_API_KEY": "serper_api_key"
        }
    
    # Get the environment variable from the mapping
    for env_name, config_key in env_mapping.items():
        if config_key == key:
            env_var = env_name
            break
    
    # Check if .env file exists and if the key is already in it
    lines = []
    key_found = False
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        # Check if key already exists
        for i, line in enumerate(lines):
            if line.startswith(f"{env_var}="):
                lines[i] = f"{env_var}='{value}'\n"
                key_found = True
                break
    
    # If key not found, add it
    if not key_found:
        lines.append(f"{env_var}='{value}'\n")
    
    # Write back to .env file
    with open(env_path, 'w') as file:
        file.writelines(lines)
    
    console.print(f"[green][+][/green] Saved {env_var} to .env file")

@cli.command()
@click.argument('query', required=True)
@click.option('--output', '-o', default="results", help="Output directory for educational content")
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'html']), default="markdown", 
              help="Output format for educational content")
def research(query, output, format):
    """Create localized educational content for Kenyan educators based on the teaching request.
    
    Examples:
    \b
    elimu research "Create a Form 3 Business Studies lesson on M-Pesa impact"
    elimu research "Generate a handout on Kenya's renewable energy projects"
    elimu research "Develop case study on coastal tourism in Mombasa"
    """
    # Check if keys are configured before doing anything else
    if not _check_required_keys(agent_initialization=True):
        return
        
    os.makedirs(output, exist_ok=True)
    
    console.print(Panel(
        f"[bold {_P}]Query:[/] {query}",
        border_style=BORDER_PRIMARY,
        box=BOX_PANEL,
        title=f"[bold {_A}]Research Task[/]",
    ))

    # Set output format in config
    config = get_config()
    config.update('output_format', format)

    final_answer = ""
    trace = []
    with Progress(
        SpinnerColumn(style=f"bold {_P}"),
        TextColumn(f"[bold {_P}]{{task.description}}"),
        BarColumn(bar_width=None, style=_P, complete_style=_S),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[{_P}]Researching…", total=100)
        
        for i in range(10):
            if i == 0:
                final_answer, trace = _run_react_agent(query)
            progress.update(task, completed=i * 10)
            if i < 9:  # Don't sleep on the last iteration
                time.sleep(0.2)  # Just for visual effect
        
        # Complete the progress
        progress.update(task, completed=100)
    
    # Save result to file with sanitized filename
    filename = f"{output}/result_{_sanitize_filename(query)}.{_get_file_extension(format)}"
    with open(filename, 'w', encoding='utf-8') as f:
        if format == 'html':
            f.write(format_react_html(query, final_answer, trace))
        else:
            f.write(format_react_markdown(query, final_answer, trace))
    
    console.print(Panel(
        f"[bold {_S}][+][/] Saved to [bold {_I}]{filename}[/]",
        border_style=BORDER_SUCCESS,
        box=BOX_PANEL,
    ))

    from rich.markdown import Markdown
    snippet = final_answer.strip()[:1500]
    console.print(Panel(
        Markdown(snippet) if snippet else "[no answer produced]",
        title=f"[bold {_A}]Answer Preview[/]",
        border_style=BORDER_INFO,
        box=BOX_PANEL,
    ))

@cli.command()
@click.argument('file', type=click.Path(exists=True), required=True)
@click.option('--output', '-o', default="results", help="Output directory for educational content")
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'html']), default="markdown",
              help="Output format for educational content")
def batch_research(file, output, format):
    """Create educational content for multiple lesson requests from a file.
    
    The input file should contain one educational request per line.
    
    Examples:
    \b
    Create a lesson plan on photosynthesis for Form 2 Biology
    Generate a handout on Kenya's independence history
    Develop assessment questions for business studies
    """
    os.makedirs(output, exist_ok=True)
    
    # Set output format in config
    config = get_config()
    config.update('output_format', format)
    
    # Use our new task parser
    tasks = parse_tasks_from_file(file)
    
    console.print(Panel(
        f"[bold {_P}]{len(tasks)} tasks[/] from [bold {_I}]{file}[/]",
        title=f"[bold {_A}]Batch Research[/]",
        border_style=BORDER_PRIMARY,
        box=BOX_PANEL,
    ))

    # Create table for results summary
    results_table = Table(show_header=True, header_style=f"bold {_A}", box=BOX_TABLE)
    results_table.add_column("#", style="dim")
    results_table.add_column("Task", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Output File")
    
    # Process each task with a progress display
    for i, task in enumerate(tasks):
        console.print(f"\n[bold {_A}]{i+1}/{len(tasks)}[/] [bold {_P}]{task[:80]}[/]…")

        result_text = "No answer produced."
        status = "[x] Failed"
        with Progress(
            SpinnerColumn(style=f"bold {_P}"),
            TextColumn(f"[{_P}]{{task.description}}"),
            BarColumn(bar_width=None, style=_P, complete_style=_S),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            research_task = progress.add_task(f"[{_P}]Task {i+1}/{len(tasks)}…", total=100)
            for j in range(10):
                if j == 0:
                    try:
                        final_answer, trace = _run_react_agent(task)
                        if format == 'html':
                            result_text = format_react_html(task, final_answer, trace)
                        else:
                            result_text = format_react_markdown(task, final_answer, trace)
                        status = "[+] Complete"
                    except Exception as e:
                        console.print(f"[bold red]Error:[/bold red] {str(e)}")
                        result_text = f"Error: {str(e)}"
                        status = "[x] Failed"
                progress.update(research_task, completed=(j * 10))
                if j < 9:
                    time.sleep(0.1)
            progress.update(research_task, completed=100)
        
        # Save result to file
        task_filename = f"task_{i+1}_{task[:20].replace(' ', '_').replace('?', '').lower()}.{_get_file_extension(format)}"
        output_path = os.path.join(output, task_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
        
        # Add to results table
        results_table.add_row(
            str(i+1), 
            task[:50] + "..." if len(task) > 50 else task,
            status,
            output_path
        )
    
    console.print(f"\n[bold {_S}][+] All {len(tasks)} tasks completed[/]")
    console.print(results_table)

@cli.command()
@click.option('--api-key', '-k', help="Set Gemini API key")
@click.option('--serper-key', '-s', help="Set Serper API key")
@click.option('--timeout', '-t', type=int, help="Set request timeout in seconds")
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'html']), help="Set default output format")
@click.option('--model', help="Set the preferred Gemini model (e.g., gemini-2.0-flash-exp)")
@click.option('--fallback-model', help="Set the fallback Gemini model used when the primary model fails")
@click.option('--use-keyring/--no-keyring', default=None, help="Whether to use system keyring for secure storage")
@click.option('--show', is_flag=True, help="Show current configuration")
def config(api_key, serper_key, timeout, format, model, fallback_model, use_keyring, show):
    """Configure the Elimu Research Assistant."""
    config = get_config()
    secure_storage = False
    
    try:
        import keyring
        secure_storage = True
    except ImportError:
        secure_storage = False
        console.print(Panel(
            f"[{_W}]Install keyring for secure credential storage:[/]\n"
            "[bold]pip install keyring[/bold]\n\n"
            f"[{_D}]Without keyring, API keys are stored in .env[/]",
            title=f"[bold {_A}]Security Recommendation[/]",
            border_style=BORDER_WARNING,
            box=BOX_PANEL,
        ))
    
    if show:
        click.echo("Current configuration:")
        
        # Safely handle different config types
        secure_keys = {}
        if hasattr(config, 'securely_stored_keys') and callable(getattr(config, 'securely_stored_keys', None)):
            try:
                secure_keys = config.securely_stored_keys() 
            except Exception:
                secure_keys = {}
        
        for key, value in config.get_all().items():
            if key.endswith('_api_key') and value:
                value = f"{value[:4]}...{value[-4:]}"
                storage_info = " [stored in system keyring]" if secure_keys.get(key, False) else ""
                click.echo(f"  {key}: {value}{storage_info}")
            else:
                click.echo(f"  {key}: {value}")
        return
    
    # Set keyring preference if specified
    if use_keyring is not None:
        if use_keyring and not secure_storage:
            console.print(f"[{_W}]Warning: keyring unavailable — install with pip install keyring[/]")
        config.update('use_keyring', use_keyring and secure_storage)
        label = "Enabled" if use_keyring else "Disabled"
        console.print(f"[bold {_S}][+][/] {label} secure credential storage")

    # Update API keys with secure storage if possible
    if api_key:
        stored_securely = config.update('gemini_api_key', api_key, store_in_keyring=True) if secure_storage else False
        console.print(f"[bold {_S}][+][/] Gemini API key updated{' (keyring)' if stored_securely else ''}")
        if not stored_securely:
            _save_to_env_file('gemini_api_key', api_key)

    if serper_key:
        stored_securely = config.update('serper_api_key', serper_key, store_in_keyring=True) if secure_storage else False
        console.print(f"[bold {_S}][+][/] Serper API key updated{' (keyring)' if stored_securely else ''}")
        if not stored_securely:
            _save_to_env_file('serper_api_key', serper_key)

    if timeout:
        config.update('timeout', timeout)
        console.print(f"[bold {_S}][+][/] Timeout -> {timeout}s")

    if format:
        config.update('output_format', format)
        console.print(f"[bold {_S}][+][/] Output format -> {format}")

    if model:
        config.update('model_name', model)
        console.print(f"[bold {_S}][+][/] Primary model -> {model}")

    if fallback_model:
        config.update('model_fallback', fallback_model)
        console.print(f"[bold {_S}][+][/] Fallback model -> {fallback_model}")

    # If use_keyring is explicitly set to True but keyring isn't available
    if use_keyring is True and not secure_storage:
        console.print(f"[{_W}]Keyring unavailable — pip install keyring[/]")
        config.update('use_keyring', False)
        console.print(f"[{_E}][x] Keyring storage disabled[/]")
    
    # Only check for missing keys if no specific updates were provided
    if not any([api_key, serper_key, timeout, format, use_keyring is not None]):
        _check_required_keys()

@cli.command()
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging")
def shell(verbose):
    """Start an interactive shell for creating educational content.
    
    In shell mode, you can continuously create educational content by entering
    teaching requests. Type 'exit' or 'quit' to leave the shell.
    
    Examples of requests you can make:
    \b
    • Create a lesson plan on M-Pesa for Form 3 Business Studies
    • Generate a geography handout about Kenya's climate zones
    • Develop a case study on coffee farming in Central Kenya
    """
    # Check if keys are configured before doing anything else
    if not _check_required_keys(agent_initialization=True):
        return
        
    # Set log level based on verbose flag
    import logging
    
    if verbose:
        set_log_level(logging.INFO)  # Using the non-relative import
    
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    
    # Create history file path
    history_file = Path.home() / ".elimu_research_history"
    
    # Create command completer with context-aware suggestions
    commands = WordCompleter([
        'search', 'exit', 'help', 'config', 'clear', 'version',
        'search "Develop a case study on coastal tourism in Kenya"',
        'search "Generate a handout on Kenya\'s independence history"',
        'search "Create a student assessment for Form 2 Mathematics"',
        'search "Design a lesson on renewable energy sources in Kenya"',
        'search "Develop a case study on the history of Swahili culture"',
    ], ignore_case=True)
    
    # Set up proper styling for prompt
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })
    
    # Initialize session with proper styling
    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=commands,
        style=style,
        message="elimu> "
    )
    
    # Display banner (we'll keep this since shell can be called directly)
    display_banner()
    
    console.print(f"\n[bold {_P}]Interactive Shell[/] [grey62]─  type help for commands, exit to quit[/]\n")
    
    while True:
        try:
            user_input = session.prompt("elimu> ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ('exit', 'quit'):
                console.print("[yellow]Exiting Elimu Research Assistant...[/yellow]")
                break
            
            if user_input.lower() == 'clear':
                console.clear()
                display_banner()
                continue
                
            if user_input.lower() == 'version':
                console.print(f"[{_I}]elimu v{__version__}[/]")
                continue
            
            if user_input.lower() == 'help':
                help_table = Table(box=BOX_TABLE, show_header=False)
                help_table.add_column("Command", style=f"bold {_A}", width=22)
                help_table.add_column("Description", style=_D)
                help_table.add_row("search <query>", "Research a topic through the ReAct agent")
                help_table.add_row("config",         "Show current configuration")
                help_table.add_row("clear",          "Clear the screen")
                help_table.add_row("version",        "Show version")
                help_table.add_row("exit / quit",    "Exit the shell")
                console.print(Panel(
                    help_table,
                    title=f"[bold {_P}]Shell Commands[/]",
                    border_style=BORDER_PRIMARY,
                    box=BOX_PANEL,
                ))
                continue
            
            if user_input.lower() == 'config':
                cfg = get_config()
                config_table = Table(box=BOX_TABLE, show_header=False)
                config_table.add_column("Setting", style=f"bold {_I}", width=28)
                config_table.add_column("Value", style=_D)
                for key, value in cfg.get_all().items():
                    if key.endswith('_api_key') and value:
                        display_val = f"{value[:4]}…{value[-4:]}"
                    else:
                        display_val = str(value)
                    config_table.add_row(key, display_val)
                console.print(Panel(
                    config_table,
                    title=f"[bold {_A}]Configuration[/]",
                    border_style=BORDER_INFO,
                    box=BOX_PANEL,
                ))
                continue
            
            # Only research on explicit `search <query>`; everything else is unknown
            if user_input.lower().startswith('search '):
                query = user_input[7:].strip()
                if not query:
                    console.print(f"[{_W}][!] Usage: search <query>[/]")
                    continue
            else:
                inp = user_input.strip()
                _CMDS = ('search', 'config', 'help', 'clear', 'version', 'exit', 'quit')
                suggestions = [c for c in _CMDS if c.startswith(inp.lower())]
                if suggestions:
                    hint = " / ".join(f"[bold {_A}]{s}[/]" for s in suggestions)
                    console.print(f"[{_W}][!][/] Did you mean: {hint}?")
                else:
                    console.print(
                        f"[{_W}][!][/] [{_D}]{inp!r}[/] is not a recognised command. "
                        f"Type [bold {_A}]help[/] for available commands, "
                        f"or [bold {_A}]search <query>[/] to research."
                    )
                continue

            # Strip surrounding quotes from the query
            if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
                filename_query = query[1:-1]
            else:
                filename_query = query

            if query:
                console.print(Panel(
                    f"[bold {_P}]Query:[/] {query}",
                    border_style=BORDER_PRIMARY,
                    box=BOX_PANEL,
                ))
                final_answer = ""
                trace = []

                with Progress(
                    SpinnerColumn(style=f"bold {_P}"),
                    TextColumn(f"[{_P}]{{task.description}}"),
                    BarColumn(bar_width=None, style=_P, complete_style=_S),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(f"[{_P}]Researching…", total=100)
                    for i in range(10):
                        if i == 0:
                            try:
                                final_answer, trace = _run_react_agent(query)
                            except Exception as e:
                                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                                final_answer = ""
                                trace = []
                                break
                        progress.update(task, completed=(i * 10))
                        if i < 9:
                            time.sleep(0.2)
                    if final_answer:
                        progress.update(task, completed=100)
                
                if final_answer:
                    os.makedirs("results", exist_ok=True)
                    filename = f"results/result_{_sanitize_filename(filename_query)}.md"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(_format_react_markdown(query, final_answer, trace))
                    
                    from rich.markdown import Markdown
                    console.print(Panel(
                        Markdown(final_answer),
                        title=f"[bold {_A}]Answer[/]",
                        border_style=BORDER_SUCCESS,
                        box=BOX_PANEL,
                    ))
                    console.print(f"[bold {_S}][+][/] Saved to [{_I}]{filename}[/]")
                else:
                    console.print(f"[bold {_E}][x][/] Research failed — please try again.")
        
        except KeyboardInterrupt:
            console.print(f"\n[{_W}]Cancelled — press Ctrl+D or type exit to quit.[/]")
            continue
        except EOFError:
            console.print(f"\n[{_W}]Exiting…[/]")
            break
        except Exception as e:
            console.print(f"[bold {_E}]Error:[/] {e}")

    console.print(f"[bold {_P}]Goodbye.[/]")

def _get_file_extension(format):
    """Get file extension based on output format."""
    if format == 'json':
        return 'json'
    elif format == 'html':
        return 'html'
    else:
        return 'md'


# ── logs command ─────────────────────────────────────────────────────────────

@cli.command()
@click.option('--lines', '-n', default=40, show_default=True,
              help="Number of recent log lines to display")
@click.option('--level', '-l',
              type=click.Choice(['debug', 'info', 'warning', 'error'], case_sensitive=False),
              default='warning', show_default=True,
              help="Minimum log level to show")
def logs(lines, level):
    """View recent agent log entries."""
    log_file = Path(__file__).parent / "logs" / "agent.log"
    if not log_file.exists():
        console.print(Panel(
            f"[{_D}]No log file found at[/] [{_I}]{log_file}[/]\n"
            "Logs are created after the first research run.",
            title=f"[bold {_A}]Logs[/]",
            border_style=BORDER_INFO,
            box=BOX_PANEL,
        ))
        return

    level_order = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3}
    min_level = level_order[level.lower()]

    level_styles = {
        'DEBUG':   _D,
        'INFO':    _I,
        'WARNING': _W,
        'ERROR':   _E,
    }

    with open(log_file, encoding='utf-8', errors='replace') as f:
        all_lines = f.readlines()

    # Filter by level then take the last N
    filtered = []
    for raw in all_lines:
        for lvl, style in level_styles.items():
            if f' - {lvl} - ' in raw:
                if level_order.get(lvl.lower(), 0) >= min_level:
                    filtered.append((lvl, style, raw.rstrip()))
                break

    filtered = filtered[-lines:]

    if not filtered:
        console.print(f"[{_D}]No entries at level {level.upper()} or above in the last {lines} lines.[/]")
        return

    from rich.table import Table
    t = Table(box=BOX_TABLE, show_header=True, header_style=f"bold {_A}",
              border_style=BORDER_INFO)
    t.add_column("Time", style=_D, width=19, no_wrap=True)
    t.add_column("Level", width=8)
    t.add_column("Message")

    for lvl, style, raw in filtered:
        parts = raw.split(' - ', 3)
        timestamp = parts[0] if len(parts) > 0 else ''
        msg = parts[3] if len(parts) > 3 else raw
        t.add_row(timestamp, f"[{style}]{lvl}[/]", msg)

    console.print(Panel(
        t,
        title=f"[bold {_A}]Agent Logs[/] [{_D}](last {len(filtered)} entries >= {level.upper()})[/]",
        border_style=BORDER_INFO,
        box=BOX_PANEL,
    ))


# ── history command ───────────────────────────────────────────────────────────

@cli.command()
@click.option('--limit', '-n', default=20, show_default=True,
              help="Number of recent queries to show")
def history(limit):
    """View past research queries."""
    history_file = Path.home() / ".elimu_research_history"
    if not history_file.exists():
        console.print(Panel(
            f"[{_D}]No history file found.[/]\n"
            "History is recorded during interactive shell sessions.",
            title=f"[bold {_A}]History[/]",
            border_style=BORDER_INFO,
            box=BOX_PANEL,
        ))
        return

    # prompt_toolkit FileHistory format:
    #   # <timestamp>
    #   +<command>   (may be multi-line with leading space for continuations)
    #   <blank line>
    entries = []
    current_cmd = []
    current_ts = ""
    with open(history_file, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if line.startswith('# '):
                if current_cmd:
                    entries.append((current_ts, ''.join(current_cmd).strip()))
                    current_cmd = []
                current_ts = line[2:]
            elif line.startswith('+'):
                current_cmd.append(line[1:])
            elif line.startswith(' ') and current_cmd:
                current_cmd.append('\n' + line[1:])
        if current_cmd:
            entries.append((current_ts, ''.join(current_cmd).strip()))

    # Most recent first, limited
    entries = [e for e in entries if e[1]]
    entries = list(reversed(entries))[:limit]

    if not entries:
        console.print(f"[{_D}]No queries in history yet.[/]")
        return

    from rich.table import Table
    t = Table(box=BOX_TABLE, show_header=True, header_style=f"bold {_A}",
              border_style=BORDER_INFO)
    t.add_column("#", style=_D, width=4)
    t.add_column("When", style=_D, width=26)
    t.add_column("Query")

    for i, (ts, cmd) in enumerate(entries, 1):
        preview = cmd[:120] + ('...' if len(cmd) > 120 else '')
        t.add_row(str(i), ts, preview)

    console.print(Panel(
        t,
        title=f"[bold {_A}]Research History[/] [{_D}](last {len(entries)})[/]",
        border_style=BORDER_INFO,
        box=BOX_PANEL,
    ))

def main():
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

if __name__ == '__main__':
    main()
