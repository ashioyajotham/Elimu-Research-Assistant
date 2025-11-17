import argparse
import os

from elimu_react import build_elimu_agent
from utils.console_ui import (
    console,
    configure_logging,
    display_title,
    display_task_header,
    create_progress_context,
    display_completion_message,
)
from utils.logger import get_logger
from utils.task_parser import parse_tasks_from_file
from utils.react_output import format_react_markdown

logger = get_logger(__name__)


def _run_task(task: str):
    agent = build_elimu_agent()
    final_answer = agent.run(task)
    trace = agent.get_execution_trace()
    return final_answer, trace


def process_tasks(task_file_path, output_dir="results"):
    """Process educational tasks from a file and write results to output directory."""
    configure_logging()
    os.makedirs(output_dir, exist_ok=True)

    display_title("Elimu Research Assistant")
    tasks = parse_tasks_from_file(task_file_path)
    console.print(f"[bold]Loaded {len(tasks)} educational tasks from {task_file_path}[/]")

    for i, task in enumerate(tasks):
        display_task_header(i + 1, len(tasks), task)

        final_answer = ""
        trace = []
        with create_progress_context() as progress:
            progress_task = progress.add_task("Reasoning...", total=100)
            for step in range(10):
                if step == 0:
                    final_answer, trace = _run_task(task)
                progress.update(progress_task, completed=step * 10)
                if step < 9:
                    progress.refresh()
            progress.update(progress_task, completed=100)

        formatted = format_react_markdown(task, final_answer, trace)
        output_file = os.path.join(output_dir, f"task_{i+1}_result.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted)

        display_completion_message(task, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elimu Research Assistant")
    parser.add_argument("task_file", help="Path to text file containing tasks")
    parser.add_argument("--output", default="results", help="Output directory for results")
    args = parser.parse_args()

    process_tasks(args.task_file, args.output)
