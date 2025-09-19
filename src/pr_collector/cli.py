"""Command-line interface for pr-collector."""

import os

import typer
from rich.console import Console
from rich.panel import Panel

from .app import collect_pr_data, get_application_info, list_open_prs
from .config import (
    ensure_config_exists,
    get_config_file,
    get_github_token,
    load_config,
    set_default_output_dir,
    set_github_token,
)

app = typer.Typer(
    name="pr-collector",
    help="Collect PR diffs and metadata into markdown files",
    add_completion=False,
)
console = Console()


@app.command()
def collect(
    pr_number: int = typer.Argument(
        None, help="PR number to collect (auto-detects from current branch if not provided)"
    ),
    repo_path: str = typer.Option(
        ".", "--repo", "-r", help="Path to git repository (default: current directory)"
    ),
    target_dir: str = typer.Option(
        None, "--dir", "-d", help="Target directory to collect diffs for (relative to repo root)"
    ),
    output_path: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path or directory (if not specified, only prints to stdout)",
    ),
    silent: bool = typer.Option(
        False, "--silent", "-s", help="Don't print markdown to stdout (only save to file)"
    ),
    token: str = typer.Option(
        None, "--token", "-t", help="GitHub token (or set GITHUB_TOKEN env var)"
    ),
) -> None:
    """Collect PR diff and metadata into a markdown file."""

    try:
        # Get token from CLI, environment, or config (in that order)
        github_token = token or get_github_token()

        # Handle output path
        final_output_path = None
        if output_path:
            # If output path is specified, resolve it
            final_output_path = os.path.abspath(output_path)

        # Resolve repo path
        repo_path = os.path.abspath(repo_path)

        if pr_number is None:
            console.print(f"[blue]Auto-detecting PR from current branch in {repo_path}[/blue]")
        else:
            console.print(f"[blue]Collecting PR #{pr_number} from {repo_path}[/blue]")

        if target_dir:
            console.print(f"[dim]Target directory: {target_dir}[/dim]")

        if not github_token:
            console.print(
                "[dim]No GitHub token found - only public repositories will be accessible[/dim]"
            )
            console.print("[dim]Set token with: pr-collector config set-token <your_token>[/dim]")

        # Collect PR data
        output_file, markdown_content = collect_pr_data(
            repo_path=repo_path,
            pr_number=pr_number,
            output_path=final_output_path,
            target_dir=target_dir,
            token=github_token,
        )

        # Handle output - stdout is default unless silent mode
        if not silent:
            console.print(markdown_content)

        if output_file:
            console.print(
                Panel.fit(
                    f"✅ PR data collected successfully!\n[bold]File:[/bold] {output_file}",
                    style="green",
                )
            )
        elif silent:
            # If silent mode but no file output, that's an error
            console.print(
                Panel.fit("❌ Error: Silent mode requires --output to be specified", style="red")
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(Panel.fit(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


@app.command()
def info() -> None:
    """Show information about pr-collector."""

    metadata = get_application_info()
    info_text = (
        f"[bold blue]{metadata['name']}[/bold blue]\n\n"
        f"[bold]Version:[/bold] {metadata['version']}\n"
        f"[bold]Description:[/bold] {metadata['description']}\n\n"
        "[dim]Use 'pr-collector collect --help' to get started![/dim]"
    )
    console.print(Panel(info_text, title="📋 Application Info", expand=False))


@app.command("config")
def config_cmd(
    action: str = typer.Argument(..., help="Action: show, set-token, set-output-dir, init"),
    value: str = typer.Argument(None, help="Value for set actions"),
) -> None:
    """Manage configuration settings."""

    try:
        if action == "show":
            ensure_config_exists()
            config = load_config()
            config_file = get_config_file()

            # Mask token for security
            display_config = config.copy()
            if display_config.get("github_token"):
                token = display_config["github_token"]
                display_config["github_token"] = f"{token[:8]}..." if len(token) > 8 else "***"

            config_text = (
                f"[bold]Configuration File:[/bold] {config_file}\n\n[bold]Settings:[/bold]\n"
            )

            for key, val in display_config.items():
                config_text += f"  {key}: {val}\n"

            console.print(Panel(config_text, title="⚙️  Configuration", expand=False))

        elif action == "set-token":
            if not value:
                console.print(Panel.fit("❌ Error: Token value required", style="red"))
                raise typer.Exit(1)

            set_github_token(value)
            console.print(Panel.fit("✅ GitHub token saved successfully!", style="green"))

        elif action == "set-output-dir":
            if not value:
                console.print(Panel.fit("❌ Error: Output directory value required", style="red"))
                raise typer.Exit(1)

            # Expand user path
            expanded_path = os.path.expanduser(value)
            set_default_output_dir(expanded_path)
            console.print(
                Panel.fit(f"✅ Default output directory set to: {expanded_path}", style="green")
            )

        elif action == "init":
            ensure_config_exists()
            config_file = get_config_file()
            console.print(
                Panel.fit(f"✅ Configuration initialized at: {config_file}", style="green")
            )

        else:
            console.print(
                Panel.fit(
                    f"❌ Error: Unknown action '{action}'. Use: show, set-token, set-output-dir, init",
                    style="red",
                )
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(Panel.fit(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


@app.command("list-prs")
def list_prs_cmd(
    repo_path: str = typer.Option(
        ".", "--repo", "-r", help="Path to git repository (default: current directory)"
    ),
    token: str = typer.Option(
        None, "--token", "-t", help="GitHub token (or set GITHUB_TOKEN env var)"
    ),
) -> None:
    """List all open PRs for the repository."""

    try:
        # Get token from CLI, environment, or config
        github_token = token or get_github_token()

        # Resolve path
        repo_path = os.path.abspath(repo_path)

        console.print(f"[blue]Listing open PRs for {repo_path}[/blue]")

        if not github_token:
            console.print(
                "[dim]No GitHub token found - only public repositories will be accessible[/dim]"
            )
            console.print("[dim]Set token with: pr-collector config set-token <your_token>[/dim]")

        # List PRs
        pr_list = list_open_prs(repo_path=repo_path, token=github_token)

        if not pr_list:
            console.print(Panel.fit("No open PRs found for this repository.", style="yellow"))
            return

        # Display PRs in a nice table format
        from rich.table import Table

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("PR #", style="cyan", width=6)
        table.add_column("Title", style="white")
        table.add_column("Branch", style="green")
        table.add_column("Author", style="blue")
        table.add_column("Created", style="dim")

        for pr in pr_list:
            table.add_row(
                f"#{pr['number']}", pr["title"], pr["branch"], pr["author"], pr["created"]
            )

        console.print(table)

    except Exception as e:
        console.print(Panel.fit(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI application."""

    app()


if __name__ == "__main__":
    main()
