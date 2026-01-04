#!/usr/bin/env python3
"""
CLI monitoring tool for Nexus Ray workflows.

Provides real-time monitoring and health checks.
"""

import click
import time
from datetime import datetime
from tabulate import tabulate
from src.observability.metrics import get_metrics_collector
from src.observability.llm_insights import get_llm_tracker
from src.observability.activity_feed import get_activity_feed


@click.group()
def cli():
    """Nexus Ray Monitoring CLI"""
    pass


@cli.command()
def metrics():
    """Display current metrics"""
    collector = get_metrics_collector()
    summary = collector.get_summary()
    
    click.echo("\n📊 Metrics Summary")
    click.echo("=" * 50)
    click.echo(f"Total Metrics: {summary['total_metrics']}")
    click.echo(f"Counters: {summary['counters']}")
    click.echo(f"Gauges: {summary['gauges']}")
    click.echo(f"Histograms: {summary['histograms']}")
    click.echo()
    
    # Display key metrics
    table_data = []
    for name, metric in summary['metrics'].items():
        table_data.append([
            name,
            metric['type'],
            metric['value'],
            str(metric.get('labels', {}))
        ])
    
    if table_data:
        click.echo(tabulate(
            table_data,
            headers=["Metric", "Type", "Value", "Labels"],
            tablefmt="grid"
        ))


@cli.command()
def llm():
    """Display LLM analytics"""
    tracker = get_llm_tracker()
    analytics = tracker.get_global_analytics()
    
    click.echo("\n🤖 LLM Analytics")
    click.echo("=" * 50)
    click.echo(f"Total Calls: {analytics['total_calls']}")
    click.echo(f"Total Tokens: {analytics['total_tokens']:,}")
    click.echo(f"Estimated Cost: ${analytics['estimated_cost_usd']:.4f}")
    click.echo(f"Reasoning Traces: {analytics['total_reasoning_traces']}")
    click.echo()
    
    # Model stats
    if analytics.get('model_stats'):
        click.echo("Model Performance:")
        table_data = []
        for model, stats in analytics['model_stats'].items():
            table_data.append([
                model,
                stats['calls'],
                f"{stats['tokens']:,}",
                f"{stats['avg_duration_ms']:.0f}ms",
                stats['errors']
            ])
        
        click.echo(tabulate(
            table_data,
            headers=["Model", "Calls", "Tokens", "Avg Duration", "Errors"],
            tablefmt="grid"
        ))


@cli.command()
@click.option('--limit', default=20, help='Number of activities to show')
def activity(limit):
    """Display recent activity feed"""
    feed = get_activity_feed()
    activities = feed.get_recent(limit)
    
    click.echo(f"\n📋 Recent Activity (last {limit})")
    click.echo("=" * 80)
    
    if not activities:
        click.echo("No activities recorded")
        return
    
    for act in activities:
        timestamp = act.timestamp.strftime("%H:%M:%S")
        severity_icon = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌"
        }.get(act.severity, "•")
        
        click.echo(f"{timestamp} {severity_icon} {act.title}")
        if act.description:
            click.echo(f"           {act.description}")
        click.echo()


@cli.command()
def health():
    """System health check"""
    collector = get_metrics_collector()
    tracker = get_llm_tracker()
    feed = get_activity_feed()
    
    click.echo("\n🏥 System Health Check")
    click.echo("=" * 50)
    
    # Check metrics
    metrics_summary = collector.get_summary()
    click.echo(f"✓ Metrics Collector: {metrics_summary['total_metrics']} metrics tracked")
    
    # Check LLM tracker
    llm_analytics = tracker.get_global_analytics()
    click.echo(f"✓ LLM Tracker: {llm_analytics['total_calls']} calls recorded")
    
    # Check activity feed
    recent = feed.get_recent(10)
    errors = feed.get_errors(10)
    click.echo(f"✓ Activity Feed: {len(recent)} recent activities, {len(errors)} errors")
    
    click.echo("\n✅ All systems operational")


@cli.command()
@click.option('--interval', default=5, help='Update interval in seconds')
def watch(interval):
    """Watch metrics in real-time"""
    click.echo("📡 Real-time Monitoring (Ctrl+C to stop)\n")
    
    try:
        while True:
            click.clear()
            
            # Header
            click.echo(f"Nexus Ray Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 80)
            
            # Metrics
            collector = get_metrics_collector()
            summary = collector.get_summary()
            
            click.echo("\n📊 Metrics:")
            for name in ['workflows_started_total', 'workflows_completed_total', 'workflows_failed_total']:
                metric = summary['metrics'].get(name, {})
                click.echo(f"  {name}: {metric.get('value', 0)}")
            
            # LLM Stats
            tracker = get_llm_tracker()
            llm_stats = tracker.get_global_analytics()
            
            click.echo(f"\n🤖 LLM:")
            click.echo(f"  Calls: {llm_stats['total_calls']}")
            click.echo(f"  Tokens: {llm_stats['total_tokens']:,}")
            click.echo(f"  Cost: ${llm_stats['estimated_cost_usd']:.4f}")
            
            # Recent Activity
            feed = get_activity_feed()
            recent = feed.get_recent(5)
            
            click.echo(f"\n📋 Recent Activity:")
            for act in recent[:5]:
                timestamp = act.timestamp.strftime("%H:%M:%S")
                click.echo(f"  {timestamp} - {act.title}")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        click.echo("\n\n👋 Monitoring stopped")


@cli.command()
@click.argument('workflow_id')
def workflow(workflow_id):
    """Show detailed workflow info"""
    tracker = get_llm_tracker()
    feed = get_activity_feed()
    
    click.echo(f"\n🔄 Workflow: {workflow_id}")
    click.echo("=" * 80)
    
    # LLM Analytics
    llm_analytics = tracker.get_workflow_analytics(workflow_id)
    
    if 'error' not in llm_analytics:
        click.echo("\n🤖 LLM Performance:")
        click.echo(f"  Total Calls: {llm_analytics['total_calls']}")
        click.echo(f"  Total Tokens: {llm_analytics['total_tokens']:,}")
        click.echo(f"  Input Tokens: {llm_analytics['input_tokens']:,}")
        click.echo(f"  Output Tokens: {llm_analytics['output_tokens']:,}")
        click.echo(f"  Avg Duration: {llm_analytics['avg_duration_ms']:.0f}ms")
        click.echo(f"  Models: {', '.join(llm_analytics['models_used'].keys())}")
    
    # Activity Timeline
    activities = feed.get_for_workflow(workflow_id)
    
    click.echo(f"\n📋 Activity Timeline ({len(activities)} events):")
    for act in activities[:20]:
        timestamp = act.timestamp.strftime("%H:%M:%S")
        click.echo(f"  {timestamp} - {act.title}")


if __name__ == '__main__':
    cli()
