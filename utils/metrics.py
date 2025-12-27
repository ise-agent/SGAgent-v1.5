from prometheus_client import Counter, generate_latest
from typing import Dict, Any
from datetime import datetime
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Counter to track tool usage by tool name
tool_usage_counter = Counter(
    'tool_usage_total',
    'Total count of tool usage by tool name',
    ['tool_name']
)

# Counter to track agent runs
agent_runs_counter = Counter(
    'agent_runs_total',
    'Total count of agent runs',
    ['agent_name']
)

def increment_tool_usage(tool_name: str) -> None:
    """Increment the tool usage counter for a given tool name."""
    tool_usage_counter.labels(tool_name=tool_name).inc()

def increment_agent_run(agent_name: str) -> None:
    """Increment the agent run counter for a given agent name."""
    agent_runs_counter.labels(agent_name=agent_name).inc()

def get_tool_usage_stats() -> Dict[str, Any]:
    """Get current tool usage statistics."""
    # Generate latest metrics
    metrics_text = generate_latest().decode('utf-8')

    # Parse the metrics to extract tool usage
    stats = {}
    for line in metrics_text.split('\n'):
        if 'tool_usage_total' in line and line.startswith('tool_usage_total'):
            # Parse the metric line to extract tool name and count
            if 'tool_name=' in line:
                try:
                    # Extract tool name from labels
                    start = line.find('tool_name="') + len('tool_name="')
                    end = line.find('"', start)
                    tool_name = line[start:end]

                    # Extract count
                    count_str = line.split(' ') [-1]
                    count = float(count_str) if count_str else 0

                    stats[tool_name] = int(count)
                except (ValueError, IndexError):
                    continue

    return stats

def format_tool_usage_stats() -> str:
    """Format tool usage statistics in a beautified way using Rich."""
    stats = get_tool_usage_stats()

    console = Console()

    if not stats:
        return "No tool usage statistics available yet."

    # Sort by count (descending)
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

    # Create a rich table
    table = Table(title="📊 Tool Usage Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan", width=40)
    table.add_column("Count", style="green", justify="right")

    for tool_name, count in sorted_stats:
        table.add_row(tool_name, str(count))

    # Create summary information
    total_unique = len(stats)
    total_invocations = sum(stats.values())

    summary_text = Text(f"\nTotal unique tools used: {total_unique}\n")
    summary_text.append(f"Total tool invocations: {total_invocations}\n")
    summary_text.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create a panel with the table and summary
    panel = Panel(
        table,
        title="Tool Usage Statistics",
        subtitle=summary_text,
        border_style="blue",
        expand=False
    )

    # Capture the output to return as string
    from io import StringIO

    # Capture the console output
    string_output = StringIO()
    console = Console(file=string_output)
    console.print(panel)

    return string_output.getvalue()


def print_tool_usage_stats():
    """Print tool usage statistics using Rich formatting."""
    stats = get_tool_usage_stats()

    console = Console()

    if not stats:
        console.print("[yellow]No tool usage statistics available yet.[/yellow]")
        return

    # Sort by count (descending)
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

    # Create a rich table
    table = Table(title="", show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan", width=40)
    table.add_column("Count", style="green", justify="right")

    for tool_name, count in sorted_stats:
        table.add_row(tool_name, str(count))

    # Create summary information
    total_unique = len(stats)
    total_invocations = sum(stats.values())

    summary_text = Text(f"\nTotal unique tools used: {total_unique}\n")
    summary_text.append(f"Total tool invocations: {total_invocations}\n")
    summary_text.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Print the panel with the table and summary
    panel = Panel(
        table,
        title="Tool Usage Statistics",
        subtitle=summary_text,
        border_style="blue",
        expand=False
    )

    console.print(panel)