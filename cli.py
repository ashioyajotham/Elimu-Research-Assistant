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
from utils.react_output import format_react_markdown
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Import the new parser
from utils.task_parser import parse_tasks_from_file

logger = get_logger(__name__)
console = Console()

# ASCII Art Banner
BANNER = """
[bold blue]
███████╗██╗     ██╗███╗   ███╗██╗   ██╗
██╔════╝██║     ██║████╗ ████║██║   ██║
█████╗  ██║     ██║██╔████╔██║██║   ██║
██╔══╝  ██║     ██║██║╚██╔╝██║██║   ██║
███████╗███████╗██║██║ ╚═╝ ██║╚██████╔╝
╚══════╝╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ 
[/bold blue]
[bold cyan]ELIMU RESEARCH ASSISTANT[/bold cyan]
[bold green]Context-rich lesson intelligence for Kenyan classrooms[/bold green]
"""

# Read version from VERSION file
def _get_version():
    """Get version from VERSION file"""
    try:
        version_file = Path(__file__).parent / "VERSION"
        return version_file.read_text().strip()
    except Exception:
        return "1.1.1"  # Fallback version

__version__ = _get_version()


def display_banner():
    """Display the ASCII art banner."""
    console.print(BANNER)
    console.print(f"\n[dim]Version {__version__}[/dim]")
    console.print("[dim]Developed by [bold magenta]Ashioya Jotham Victor[/bold magenta] – precision research for Kenyan classrooms.[/dim]\n")

def display_intro():
    """Display introduction info for Elimu Research Assistant."""
    table = Table(box=box.ROUNDED, show_header=False, border_style="blue")
    table.add_column(justify="center", style="bold cyan")
    table.add_row("[bold green]Available commands:[/bold green]")
    table.add_row("research [query] - Create localized educational content")
    table.add_row("batch-research [file] - Process multiple lesson requests")
    table.add_row("config - Configure API keys and educational settings")
    table.add_row("shell - Start interactive educational content creation mode")
    
    console.print(Panel(table, border_style="blue", title="Elimu Research Assistant · Context-Rich Lessons"))

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
        return Panel("Preview unavailable – no content returned.", border_style="red", title="Results Preview")
    
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
    table.add_row(f"[bold cyan]Plan[/bold cyan]\n{plan_snippet}", f"[bold cyan]Key Findings[/bold cyan]\n{findings_snippet}")
    table.add_row(
        f"[bold cyan]Research Scope[/bold cyan]\n{scope_block}",
        f"[bold cyan]Summary & Storage[/bold cyan]\n{summary_block}{storage_info}"
    )
    
    return Panel(table, title="Results Preview", border_style="cyan")

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
        
    # We'll keep the banner display only for the main CLI, but skip it for subcommands
    if len(sys.argv) == 1 or sys.argv[1] not in ['shell', 'research', 'batch-research', 'config']:
        display_banner()

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
            console.print("[yellow]Warning: Running in no-config mode. API calls will fail.[/yellow]")
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
                "[bold yellow]Secure credential storage is optional but recommended.[/bold yellow]\n\n"
                "Install [bold]keyring[/bold] to keep API keys in the Windows credential vault:\n"
                "[bold]pip install keyring[/bold]",
                title="Security Recommendation",
                border_style="yellow"
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
            "[bold yellow]API keys required[/bold yellow]\n\n"
            "Elimu uses Google Gemini for comprehension and Serper.dev for search.\n"
            "You'll be prompted for both keys now.",
            title="Configuration Needed",
            border_style="yellow"
        ))
    
    secure_storage_available = keyring_available and config.get('use_keyring', True)
    
    for key, display_name in required_keys.items():
        if key not in missing_keys:
            continue
            
        value = ""
        while not value:
            value = click.prompt(f"Enter your {display_name}", hide_input=True).strip()
            if not value:
                console.print("[red]API key cannot be empty.[/red]")
        
        stored_securely = False
        if secure_storage_available:
            use_secure = click.confirm(
                f"Store the {display_name} in your system keyring? (Recommended)",
                default=True,
                show_default=True
            )
            if use_secure:
                stored_securely = config.update(key, value, store_in_keyring=True)
                if stored_securely:
                    console.print(f"[green]✓[/green] {display_name} stored securely.")
                else:
                    console.print(f"[yellow]⚠[/yellow] Could not access the keyring. We'll fall back to the .env file.")
        
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
    
    console.print(f"[green]✓[/green] Saved {env_var} to .env file")

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
    
    console.print(Panel(f"[bold cyan]Creating Educational Content:[/bold cyan] {query}", border_style="blue"))
    
    # Set output format in config
    config = get_config()
    config.update('output_format', format)
    
    final_answer = ""
    trace = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Researching...", total=100)
        
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
        f.write(format_react_markdown(query, final_answer, trace))
    
    console.print(Panel(f"[bold green]✓[/bold green] Research complete! Results saved to [bold cyan]{filename}[/bold cyan]", 
                        border_style="green"))
    
    # Show a preview of the results
    snippet = final_answer.strip()[:1500]
    console.print(Panel(snippet if snippet else "[no answer produced]", title="Final Answer Preview", border_style="cyan"))

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
    
    console.print(Panel(f"[bold cyan]Processing {len(tasks)} lesson requests from {file}[/bold cyan]", border_style="blue"))
    
    # Create table for results summary
    results_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    results_table.add_column("#", style="dim")
    results_table.add_column("Task", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Output File")
    
    # Process each task with a progress display
    for i, task in enumerate(tasks):
        console.print(f"\n[bold blue]Task {i+1}/{len(tasks)}:[/bold blue] {task[:80]}...")
        
        result_text = "No answer produced."
        status = "✗ Failed"
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            research_task = progress.add_task(f"[cyan]Researching task {i+1}/{len(tasks)}...", total=100)
            for j in range(10):
                if j == 0:
                    try:
                        final_answer, trace = _run_react_agent(task)
                        result_text = format_react_markdown(task, final_answer, trace)
                        status = "✓ Complete"
                    except Exception as e:
                        console.print(f"[bold red]Error:[/bold red] {str(e)}")
                        result_text = f"Error: {str(e)}"
                        status = "✗ Failed"
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
    
    console.print("\n[bold green]✓ All tasks completed![/bold green]")
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
            "[bold yellow]Security Recommendation[/bold yellow]\n\n"
            "For secure credential storage, install the keyring package:\n"
            "[bold]pip install keyring[/bold]\n\n"
            "Without keyring, API keys will be stored in a .env file.",
            border_style="yellow"
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
        
        for key, value in (config.items() if hasattr(config, 'items') else config.get_all().items()):
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
            console.print("[yellow]Warning: System keyring support not available. Install the 'keyring' package.[/yellow]")
        config.update('use_keyring', use_keyring and secure_storage)
        console.print(f"{'✅' if use_keyring else '❌'} {'Enabled' if use_keyring else 'Disabled'} secure credential storage")
    
    # Update API keys with secure storage if possible
    if api_key:
        stored_securely = config.update('gemini_api_key', api_key, store_in_keyring=True) if secure_storage else False
        console.print(f"✅ Updated Gemini API key{' (stored securely)' if stored_securely else ''}")
        if not stored_securely:
            _save_to_env_file('gemini_api_key', api_key)
    
    if serper_key:
        stored_securely = config.update('serper_api_key', serper_key, store_in_keyring=True) if secure_storage else False
        console.print(f"✅ Updated Serper API key{' (stored securely)' if stored_securely else ''}")
        if not stored_securely:
            _save_to_env_file('serper_api_key', serper_key)
    
    # Other config updates
    if timeout:
        config.update('timeout', timeout)
        console.print(f"✅ Updated request timeout to {timeout} seconds")
    
    if format:
        config.update('output_format', format)
        console.print(f"✅ Updated default output format to {format}")
    
    if model:
        config.update('model_name', model)
        console.print(f"✅ Preferred Gemini model set to {model}")
    
    if fallback_model:
        config.update('model_fallback', fallback_model)
        console.print(f"✅ Fallback Gemini model set to {fallback_model}")
    
    # If use_keyring is explicitly set to True but keyring isn't available
    if use_keyring is True and not secure_storage:
        console.print("[yellow]Warning: System keyring support not available. Install the 'keyring' package.[/yellow]")
        console.print("[bold]pip install keyring[/bold]")
        config.update('use_keyring', False)
        console.print("[yellow]❌ Keyring storage disabled - unavailable on this system[/yellow]")
    
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
    
    console.print("\n[bold cyan]Interactive Shell Started[/bold cyan]")
    console.print("[dim]Type commands to interact with the agent. Try 'help' for assistance.[/dim]\n")
    
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
                console.print(f"[cyan]Elimu Research Assistant v{__version__}[/cyan]")
                continue
            
            if user_input.lower() == 'help':
                help_table = Table(box=box.ROUNDED)
                help_table.add_column("Command", style="cyan")
                help_table.add_column("Description", style="green")
                
                help_table.add_row("search <query>", "Research a topic")
                help_table.add_row("config", "Show/modify configuration")
                help_table.add_row("clear", "Clear the screen")
                help_table.add_row("version", "Show version")
                help_table.add_row("exit/quit", "Exit the shell")
                
                console.print(Panel(help_table, title="Help", border_style="blue"))
                continue
            
            if user_input.lower() == 'config':
                # Show configuration
                config = get_config()
                config_table = Table(box=box.ROUNDED)
                config_table.add_column("Setting", style="cyan")
                config_table.add_column("Value", style="green")
                
                for key, value in config.items():
                    if key.endswith('_api_key') and value:
                        masked_value = f"{value[:4]}...{value[-4:]}"
                        config_table.add_row(key, masked_value)
                    else:
                        config_table.add_row(key, str(value))
                
                console.print(Panel(config_table, title="Configuration", border_style="blue"))
                continue
            
            # Default to search if no command specified
            if not user_input.lower().startswith('search '):
                query = user_input
            else:
                query = user_input[7:]
            
            # Strip surrounding quotes from the query
            if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
                # Only strip quotes for filename, leave original query for searching
                filename_query = query[1:-1]
            else:
                filename_query = query

            if query:
                console.print(Panel(f"[bold cyan]Researching:[/bold cyan] {query}", border_style="blue"))
                final_answer = ""
                trace = []
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Researching...", total=100)
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
                    
                        console.print("\n[bold green]Answer:[/bold green]", style="bold")
                    console.print(Panel(final_answer, border_style="green", expand=False, title="Direct Answer"))
                    console.print(f"[bold green]✓[/bold green] Research complete! Results saved to [cyan]{filename}[/cyan]")
                else:
                    console.print("[bold red]✗[/bold red] Research failed. Please try again.")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled. Press Ctrl+D or type 'exit' to quit.[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Exiting Elimu Research Assistant...[/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    console.print("[bold green]Goodbye![/bold green]")

def _get_file_extension(format):
    """Get file extension based on output format."""
    if format == 'json':
        return 'json'
    elif format == 'html':
        return 'html'
    else:
        return 'md'

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
