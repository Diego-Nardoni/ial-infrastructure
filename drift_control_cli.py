#!/usr/bin/env python3
"""
IAL Drift Control CLI
Command-line interface for managing drift detection flags
"""

import typer
import json
import sys
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from core.drift_flag import DriftFlag, DriftState, parse_duration
from core.decision_ledger import DecisionLedger

app = typer.Typer(help="IAL Drift Control Management")
console = Console()

# Initialize components
drift_flag = DriftFlag()
decision_ledger = DecisionLedger()

@app.command()
def pause(
    scope: str = typer.Argument(..., help="Scope to pause drift for (e.g., 'project-x', 'global')"),
    duration: str = typer.Option("3h", "--duration", "-d", help="Duration to pause (e.g., '3h', '30m', '2d')"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for pausing drift detection"),
    ticket: str = typer.Option("", "--ticket", "-t", help="Ticket/incident number"),
    approver: List[str] = typer.Option([], "--approver", "-a", help="Approver(s) for this action")
):
    """Pause drift detection for specified duration"""
    
    try:
        # Validate inputs
        if not reason.strip():
            rprint("[red]❌ Reason is required for pausing drift detection[/red]")
            raise typer.Exit(1)
        
        if not approver:
            rprint("[yellow]⚠️  No approver specified - this may not comply with governance policies[/yellow]")
        
        # Parse duration
        duration_hours = parse_duration(duration)
        if duration_hours <= 0:
            rprint(f"[red]❌ Invalid duration: {duration}[/red]")
            raise typer.Exit(1)
        
        # Set flag
        result = drift_flag.pause_drift(scope, duration_hours, reason, ticket, approver)
        
        # Log to decision ledger
        decision_ledger.log(
            phase="drift-control",
            mcp="drift-flag-cli",
            tool="pause",
            rationale=f"Paused drift for {scope}: {reason} (ticket: {ticket})",
            status="PAUSED",
            metadata={
                "scope": scope,
                "duration_hours": duration_hours,
                "ticket": ticket,
                "approvers": approver
            }
        )
        
        rprint(f"[green]✅ Drift detection paused for {scope}[/green]")
        rprint(f"[blue]Duration:[/blue] {duration} ({duration_hours} hours)")
        rprint(f"[blue]Reason:[/blue] {reason}")
        if ticket:
            rprint(f"[blue]Ticket:[/blue] {ticket}")
        if approver:
            rprint(f"[blue]Approved by:[/blue] {', '.join(approver)}")
        
        if result.get("expire_at"):
            import datetime
            expire_time = datetime.datetime.fromtimestamp(result["expire_at"])
            rprint(f"[yellow]⏰ Auto-resume at:[/yellow] {expire_time}")
        
    except Exception as e:
        rprint(f"[red]❌ Failed to pause drift: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def resume(
    scope: str = typer.Argument(..., help="Scope to resume drift for"),
    reason: str = typer.Option("manual_resume", "--reason", "-r", help="Reason for resuming")
):
    """Resume drift detection (set to ENABLED)"""
    
    try:
        result = drift_flag.resume_drift(scope, reason)
        
        # Log to decision ledger
        decision_ledger.log(
            phase="drift-control",
            mcp="drift-flag-cli", 
            tool="resume",
            rationale=f"Resumed drift for {scope}: {reason}",
            status="ENABLED"
        )
        
        rprint(f"[green]✅ Drift detection resumed for {scope}[/green]")
        rprint(f"[blue]Reason:[/blue] {reason}")
        
    except Exception as e:
        rprint(f"[red]❌ Failed to resume drift: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def disable(
    scope: str = typer.Argument(..., help="Scope to disable drift for"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for disabling drift detection"),
    approver: List[str] = typer.Option([], "--approver", "-a", help="Approver(s) for this action")
):
    """Disable drift detection completely"""
    
    try:
        if not reason.strip():
            rprint("[red]❌ Reason is required for disabling drift detection[/red]")
            raise typer.Exit(1)
        
        if not approver:
            rprint("[red]❌ Approver is required for disabling drift detection[/red]")
            raise typer.Exit(1)
        
        result = drift_flag.disable_drift(scope, reason, approver)
        
        # Log to decision ledger
        decision_ledger.log(
            phase="drift-control",
            mcp="drift-flag-cli",
            tool="disable", 
            rationale=f"Disabled drift for {scope}: {reason}",
            status="DISABLED",
            metadata={"approvers": approver}
        )
        
        rprint(f"[red]🚫 Drift detection disabled for {scope}[/red]")
        rprint(f"[blue]Reason:[/blue] {reason}")
        rprint(f"[blue]Approved by:[/blue] {', '.join(approver)}")
        
    except Exception as e:
        rprint(f"[red]❌ Failed to disable drift: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def status(
    scope: Optional[str] = typer.Argument(None, help="Scope to check status for (optional)")
):
    """Show drift control status"""
    
    try:
        if scope:
            # Show status for specific scope
            flag = drift_flag.get_flag(scope)
            
            table = Table(title=f"Drift Control Status: {scope}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            # Status color coding
            state = flag["state"]
            if state == "ENABLED":
                state_display = "[green]ENABLED[/green]"
            elif state == "PAUSED":
                state_display = "[yellow]PAUSED[/yellow]"
            else:
                state_display = "[red]DISABLED[/red]"
            
            table.add_row("State", state_display)
            table.add_row("Reason", flag.get("reason", "N/A"))
            table.add_row("Ticket", flag.get("ticket", "N/A"))
            
            if flag.get("approved_by"):
                table.add_row("Approved By", ", ".join(flag["approved_by"]))
            
            if flag.get("created_at"):
                table.add_row("Created", flag["created_at"])
            
            if flag.get("expire_at"):
                import datetime
                expire_time = datetime.datetime.fromtimestamp(flag["expire_at"])
                table.add_row("Expires", str(expire_time))
            
            console.print(table)
            
        else:
            # Show status for all scopes
            flags = drift_flag.list_flags()
            
            if not flags:
                rprint("[yellow]No drift control flags found[/yellow]")
                return
            
            table = Table(title="All Drift Control Flags")
            table.add_column("Scope", style="cyan")
            table.add_column("State", style="white")
            table.add_column("Reason", style="white")
            table.add_column("Ticket", style="white")
            table.add_column("Created", style="white")
            
            for flag in flags:
                state = flag["state"]
                if state == "ENABLED":
                    state_display = "[green]ENABLED[/green]"
                elif state == "PAUSED":
                    state_display = "[yellow]PAUSED[/yellow]"
                else:
                    state_display = "[red]DISABLED[/red]"
                
                table.add_row(
                    flag["scope"],
                    state_display,
                    flag.get("reason", "N/A")[:30],
                    flag.get("ticket", "N/A"),
                    flag.get("created_at", "N/A")[:19]
                )
            
            console.print(table)
            
    except Exception as e:
        rprint(f"[red]❌ Failed to get status: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def list_paused():
    """List all currently paused scopes"""
    
    try:
        flags = drift_flag.list_flags(DriftState.PAUSED)
        
        if not flags:
            rprint("[green]No scopes are currently paused[/green]")
            return
        
        table = Table(title="Paused Drift Control Scopes")
        table.add_column("Scope", style="cyan")
        table.add_column("Reason", style="white")
        table.add_column("Ticket", style="white")
        table.add_column("Expires", style="yellow")
        
        for flag in flags:
            expire_display = "Never"
            if flag.get("expire_at"):
                import datetime
                expire_time = datetime.datetime.fromtimestamp(flag["expire_at"])
                expire_display = str(expire_time)
            
            table.add_row(
                flag["scope"],
                flag.get("reason", "N/A")[:40],
                flag.get("ticket", "N/A"),
                expire_display
            )
        
        console.print(table)
        
    except Exception as e:
        rprint(f"[red]❌ Failed to list paused scopes: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
