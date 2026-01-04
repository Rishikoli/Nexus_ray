"""
Enhanced TUI Dashboard for Nexus Ray using Textual.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Button, Log
from textual.reactive import reactive
from datetime import datetime
import asyncio

# Import Nexus Ray components
from src.collaboration import get_agent_registry
from src.guardrails import ContentFilter


class MetricsPanel(Static):
    """Display system metrics"""
    
    total_workflows = reactive(0)
    active_workflows = reactive(0)
    total_agents = reactive(0)
    
    def render(self) -> str:
        return f"""
[bold cyan]System Metrics[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Workflows: {self.total_workflows}
Active Workflows: {self.active_workflows}
Total Agents: {self.total_agents}
Available Agents: {self.total_agents}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class AgentTable(Static):
    """Display agent registry"""
    
    def compose(self) -> ComposeResult:
        yield DataTable()
    
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Agent ID", "Name", "Status", "Tasks")
        
        # Get agents
        registry = get_agent_registry()
        agents = registry.list_all_agents()
        
        for agent in agents:
            table.add_row(
                agent.agent_id[:10],
                agent.name,
                agent.status.value,
                f"{agent.current_tasks}/{agent.max_concurrent_tasks}"
            )


class ActivityLog(Static):
    """Display activity feed"""
    
    def compose(self) -> ComposeResult:
        yield Log()
    
    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line("[green]✓[/green] System started")
        log.write_line(f"[blue]ℹ[/blue] {datetime.now().strftime('%H:%M:%S')} - Dashboard initialized")


class NexusRayDashboard(App):
    """Nexus Ray TUI Dashboard"""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 3;
        grid-gutter: 1;
    }
    
    #metrics {
        column-span: 2;
        height: 10;
        border: solid green;
    }
    
    #agents {
        row-span: 2;
        border: solid cyan;
    }
    
    #activity {
        row-span: 2;
        border: solid yellow;
    }
    
    Button {
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("d", "dark", "Toggle Dark Mode"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header()
        yield MetricsPanel(id="metrics")
        yield AgentTable(id="agents")
        yield ActivityLog(id="activity")
        yield Footer()
    
    def action_refresh(self) -> None:
        """Refresh data"""
        metrics = self.query_one("#metrics", MetricsPanel)
        registry = get_agent_registry()
        stats = registry.get_statistics()
        
        metrics.total_agents = stats["total_agents"]
        metrics.active_workflows = 0
        
        log = self.query_one(ActivityLog).query_one(Log)
        log.write_line(f"[green]✓[/green] Refreshed at {datetime.now().strftime('%H:%M:%S')}")
    
    def action_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark


def run_dashboard():
    """Run the TUI dashboard"""
    app = NexusRayDashboard()
    app.run()


if __name__ == "__main__":
    run_dashboard()
