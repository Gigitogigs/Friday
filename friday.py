#!/usr/bin/env python3
"""
Friday - Offline Personal Assistant

Main entry point for the Friday CLI application.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional

from core import PermissionManager, PermissionLevel, OllamaClient, AuditLogger


console = Console()


def get_permission_manager() -> PermissionManager:
    """Get a configured permission manager instance."""
    return PermissionManager(config_path="config.yaml")


def get_ollama_client() -> OllamaClient:
    """Get a configured Ollama client instance."""
    return OllamaClient()


@click.group()
@click.version_option(version="0.1.0", prog_name="Friday")
def friday():
    """
    Friday - Your Offline Personal Assistant

    A privacy-first, local AI assistant that helps with tasks,
    file organization, and productivity.
    """
    pass


@friday.command()
def status():
    """Show Friday's current status."""
    console.print(Panel.fit(
        "[bold blue]Friday - Offline Personal Assistant[/bold blue]\n"
        "[dim]Version 0.1.0[/dim]",
        title="🤖 Status"
    ))
    
    # Check Ollama
    client = get_ollama_client()
    if client.is_available():
        models = client.list_models()
        console.print(f"\n✅ [green]Ollama is running[/green]")
        console.print(f"   Models available: {len(models)}")
        if models:
            console.print(f"   Current model: {client.model}")
    else:
        console.print(f"\n❌ [red]Ollama is not running[/red]")
        console.print("   Run 'ollama serve' to start Ollama")
    
    # Show permission config
    pm = get_permission_manager()
    console.print(f"\n🔒 Permission Settings:")
    console.print(f"   Auto-approve patterns: {len(pm.auto_approve)}")
    console.print(f"   Blacklisted patterns: {len(pm.blacklist)}")


@friday.command()
@click.argument("prompt", nargs=-1, required=True)
def ask(prompt):
    """Ask Friday a question."""
    prompt_text = " ".join(prompt)
    
    console.print(f"\n[dim]You:[/dim] {prompt_text}\n")
    
    client = get_ollama_client()
    
    if not client.is_available():
        console.print("[red]Error: Ollama is not running.[/red]")
        console.print("Start Ollama with: ollama serve")
        return
    
    with console.status("[bold green]Thinking..."):
        response = client.generate(
            prompt_text,
            system_prompt="You are Friday, a helpful offline personal assistant. Be concise and practical."
        )
    
    console.print(f"[bold blue]Friday:[/bold blue] {response}")


@friday.command()
def audit():
    """View the audit log."""
    logger = AuditLogger()
    entries = logger.get_recent(limit=20)
    
    if not entries:
        console.print("[dim]No audit entries found.[/dim]")
        return
    
    table = Table(title="Recent Audit Log")
    table.add_column("Time", style="dim")
    table.add_column("Action")
    table.add_column("Status")
    table.add_column("Approved")
    
    for entry in entries:
        # Format timestamp
        time_str = entry.timestamp.split("T")[1].split(".")[0] if "T" in entry.timestamp else entry.timestamp
        
        # Status color
        status_str = entry.status
        if entry.status == "approved":
            status_str = f"[green]{entry.status}[/green]"
        elif entry.status == "denied":
            status_str = f"[red]{entry.status}[/red]"
        
        # Approved indicator
        approved_str = "✅" if entry.user_approved else "❌" if entry.user_approved is False else "—"
        
        table.add_row(
            time_str,
            entry.action_description[:50] + "..." if len(entry.action_description) > 50 else entry.action_description,
            status_str,
            approved_str
        )
    
    console.print(table)


@friday.group()
def permission():
    """Manage permissions and security settings."""
    pass


@permission.command("list")
def permission_list():
    """List current permission settings."""
    pm = get_permission_manager()
    
    console.print("\n[bold]Auto-Approved Actions:[/bold]")
    for pattern in pm.auto_approve:
        console.print(f"  ✅ {pattern}")
    
    console.print("\n[bold]Blacklisted Actions:[/bold]")
    for pattern in pm.blacklist:
        console.print(f"  🚫 {pattern}")


@permission.command("blacklist")
@click.argument("pattern")
def permission_blacklist(pattern: str):
    """Add a pattern to the blacklist."""
    pm = get_permission_manager()
    pm.add_to_blacklist(pattern)
    pm.save_config()
    console.print(f"[green]Added to blacklist:[/green] {pattern}")


@permission.command("whitelist")
@click.argument("pattern")
def permission_whitelist(pattern: str):
    """Add a pattern to auto-approve list."""
    pm = get_permission_manager()
    pm.add_to_whitelist(pattern, PermissionLevel.SAFE_WRITE)
    pm.save_config()
    console.print(f"[green]Added to whitelist:[/green] {pattern}")


@friday.command()
def models():
    """List available Ollama models."""
    client = get_ollama_client()
    
    if not client.is_available():
        console.print("[red]Error: Ollama is not running.[/red]")
        return
    
    models = client.list_models()
    
    if not models:
        console.print("[dim]No models found.[/dim]")
        console.print("Pull a model with: ollama pull <model-name>")
        return
    
    console.print("\n[bold]Available Models:[/bold]")
    for model in models:
        indicator = "→" if model == client.model else " "
        console.print(f"  {indicator} {model}")


@friday.command()
@click.argument("model_name")
def use(model_name: str):
    """Switch to a different model."""
    client = get_ollama_client()
    
    if client.switch_model(model_name):
        console.print(f"[green]Switched to model:[/green] {model_name}")
    else:
        console.print(f"[red]Model not found:[/red] {model_name}")
        console.print("Run 'friday models' to see available models.")


@friday.command()
def chat():
    """Start an interactive chat session."""
    console.print(Panel.fit(
        "[bold blue]Friday Chat[/bold blue]\n"
        "[dim]Type 'exit' or 'quit' to end the session[/dim]",
        title="💬 Interactive Mode"
    ))
    
    client = get_ollama_client()
    
    if not client.is_available():
        console.print("[red]Error: Ollama is not running.[/red]")
        return
    
    system_prompt = """You are Friday, a helpful offline personal assistant. 
You help with tasks, file organization, and productivity.
Be concise, practical, and safety-conscious.
Never suggest actions that could harm the user's system without explicit warnings."""
    
    while True:
        try:
            user_input = console.input("\n[bold green]You>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("exit", "quit", "bye"):
            console.print("[dim]Goodbye![/dim]")
            break
        
        # Add to history
        client.add_to_history("user", user_input)
        
        # Get response
        with console.status("[bold green]Thinking..."):
            response = client.chat(
                messages=client.get_history(),
                system_prompt=system_prompt
            )
        
        # Add response to history
        client.add_to_history("assistant", response.content)
        
        console.print(f"\n[bold blue]Friday>[/bold blue] {response.content}")


if __name__ == "__main__":
    friday()
