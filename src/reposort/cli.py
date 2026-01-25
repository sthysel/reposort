"""Click CLI for reposort."""

import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from reposort.core import (
    RepoInfo,
    clone_repository,
    collect_repo_info,
    find_git_repos,
    get_git_origin_url,
    get_unique_target_path,
    parse_git_url,
)

CONTEXT_SETTINGS = {"max_content_width": 200}


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Organize git repositories by their origin URL."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(sort)


@cli.command()
@click.option(
    "--source",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    help="Source directory containing git repositories",
)
@click.option(
    "--target",
    type=click.Path(path_type=Path),
    default=Path("~/code"),
    help="Target base directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
def sort(source: Path, target: Path, dry_run: bool) -> None:
    """
    Sort existing repositories by their origin URL.

    \b
    Examples:
      # Show what would be moved
      $ reposort --dry-run

    \b
      # Execute the reorganization
      $ reposort

    \b
      # Use custom source and target directories
      $ reposort --source /path/to/repos --target ~/projects
    """
    source = source.resolve()
    target = target.expanduser().resolve()

    repos = find_git_repos(source)

    if not repos:
        click.echo(f"No git repositories found in {source}")
        return

    click.echo(f"Found {len(repos)} git repositories")
    click.echo()

    moves: list[tuple[Path, Path, str]] = []
    skipped: list[tuple[Path, str]] = []

    for repo in repos:
        origin_url = get_git_origin_url(repo)

        if not origin_url:
            skipped.append((repo, "No origin URL found"))
            continue

        parsed = parse_git_url(origin_url)
        if not parsed:
            skipped.append((repo, f"Could not parse URL: {origin_url}"))
            continue

        host, path = parsed
        # Use the full path to preserve organizational structure
        target_path = target / host / path

        # Check for conflicts and get unique path if needed
        final_target = get_unique_target_path(target_path)

        moves.append((repo, final_target, origin_url))

    # Print plan
    if moves:
        click.echo("Planned moves:")
        click.echo("-" * 80)
        for source_repo, target_repo, url in moves:
            suffix = ""
            if "-copy" in str(target_repo):
                suffix = " [CONFLICT - renamed]"
            click.echo(f"  {source_repo.name}")
            click.echo(f"    Origin: {url}")
            click.echo(f"    -> {target_repo}{suffix}")
            click.echo()

    if skipped:
        click.echo("\nSkipped repositories:")
        click.echo("-" * 80)
        for repo, reason in skipped:
            click.echo(f"  {repo.name}: {reason}")
        click.echo()

    # Execute moves if not dry-run
    if dry_run:
        click.echo("\n[DRY RUN] No changes made. Run without --dry-run to execute.")
    else:
        click.echo()
        if not click.confirm("Proceed with moving repositories?", default=False):
            click.echo("Aborted.")
            return

        click.echo("\nExecuting moves...")
        click.echo("-" * 80)

        for source_repo, target_repo, _url in moves:
            try:
                # Create parent directories
                target_repo.parent.mkdir(parents=True, exist_ok=True)

                # Move the repository
                shutil.move(str(source_repo), str(target_repo))
                click.echo(f"✓ Moved {source_repo.name} -> {target_repo}")
            except Exception as e:
                click.echo(f"✗ Failed to move {source_repo.name}: {e}")

        click.echo("\nDone!")


@cli.command()
@click.argument("url")
@click.option(
    "--target",
    type=click.Path(path_type=Path),
    default=Path("~/code"),
    help="Target base directory",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show where the repository would be cloned without executing",
)
@click.option(
    "--no-fsck",
    is_flag=True,
    help="Disable fsck checks during clone (for repos with malformed objects)",
)
def clone(url: str, target: Path, dry_run: bool, no_fsck: bool) -> None:
    """
    Clone a repository and organize it by its origin URL.

    \b
    Examples:
      # Clones to ~/code/github.com/user/repo
      $ reposort clone git@github.com:user/repo.git

    \b
      # Shows where it would be cloned without executing
      $ reposort clone https://github.com/user/repo.git --dry-run

    \b
      # Clones to ~/projects/github.com/user/repo
      $ reposort clone git@github.com:user/repo.git --target ~/projects
    """
    target = target.expanduser().resolve()

    # Parse the URL to determine target path
    parsed = parse_git_url(url)
    if not parsed:
        click.echo(f"Error: Could not parse git URL: {url}", err=True)
        raise click.Abort()

    host, path = parsed
    target_path = target / host / path

    # Handle path conflicts
    final_target = get_unique_target_path(target_path)

    # Display plan
    click.echo("Clone plan:")
    click.echo("-" * 80)
    click.echo(f"  URL: {url}")
    click.echo(f"  Target: {final_target}")

    if final_target != target_path:
        click.echo(f"  [CONFLICT - target already exists, using {final_target.name}]")
    click.echo()

    # Execute or show dry-run message
    if dry_run:
        click.echo("[DRY RUN] No changes made. Run without --dry-run to execute.")
        return

    # Execute the clone
    click.echo("Cloning...")
    click.echo("-" * 80)

    try:
        # Create parent directories
        final_target.parent.mkdir(parents=True, exist_ok=True)

        # Clone the repository
        clone_repository(url, final_target, no_fsck=no_fsck)

        click.echo(f"✓ Successfully cloned to {final_target}")

    except subprocess.CalledProcessError as e:
        click.echo("✗ Failed to clone repository", err=True)
        if e.stderr:
            click.echo(f"Git error: {e.stderr}", err=True)
        raise click.Abort() from e
    except OSError as e:
        click.echo(f"✗ File system error: {e}", err=True)
        raise click.Abort() from e


@cli.command("list")
@click.option(
    "--target",
    type=click.Path(path_type=Path),
    default=Path("~/code"),
    help="Base directory containing organized repositories",
)
def list_repos(target: Path) -> None:
    """
    List all repositories in a table view.

    Shows host, path, branch, status, and remote URL for each repository.

    \b
    Examples:
      $ reposort list
      $ reposort list --target ~/projects
    """
    target = target.expanduser().resolve()

    if not target.exists():
        click.echo(f"Target directory does not exist: {target}", err=True)
        return

    repos = collect_repo_info(target)

    if not repos:
        click.echo(f"No git repositories found in {target}")
        return

    # Sort repos by host, then by path
    repos.sort(key=lambda r: (r.host, r.repo_path))

    console = Console()
    table = Table(title=f"Repositories in {target}")

    table.add_column("Host", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Branch", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Remote URL", style="dim")

    for repo in repos:
        status = "[red]dirty[/red]" if repo.dirty else "[green]clean[/green]"
        branch = repo.branch or "-"
        remote = repo.remote_url or "-"

        table.add_row(repo.host, repo.repo_path, branch, status, remote)

    console.print(table)


@cli.command("tree")
@click.option(
    "--target",
    type=click.Path(path_type=Path),
    default=Path("~/code"),
    help="Base directory containing organized repositories",
)
def tree_repos(target: Path) -> None:
    """
    Display repositories in a tree view organized by host.

    \b
    Examples:
      $ reposort tree
      $ reposort tree --target ~/projects
    """
    target = target.expanduser().resolve()

    if not target.exists():
        click.echo(f"Target directory does not exist: {target}", err=True)
        return

    repos = collect_repo_info(target)

    if not repos:
        click.echo(f"No git repositories found in {target}")
        return

    # Organize repos by host and path hierarchy
    host_tree: dict[str, dict[str, list[RepoInfo]]] = defaultdict(lambda: defaultdict(list))

    for repo in repos:
        parts = repo.repo_path.split("/")
        if len(parts) >= 2:
            owner = parts[0]
            host_tree[repo.host][owner].append(repo)
        else:
            host_tree[repo.host][""].append(repo)

    console = Console()
    tree = Tree(f"[bold]{target}[/bold]")

    for host in sorted(host_tree.keys()):
        host_branch = tree.add(f"[cyan]{host}/[/cyan]")
        owners = host_tree[host]

        for owner in sorted(owners.keys()):
            owner_branch = host_branch.add(f"[green]{owner}/[/green]") if owner else host_branch

            for repo in sorted(owners[owner], key=lambda r: r.repo_path):
                parts = repo.repo_path.split("/")
                repo_name = parts[-1] if len(parts) > 1 else repo.repo_path
                branch = repo.branch or "?"
                status = "[red]dirty[/red]" if repo.dirty else "[green]clean[/green]"
                owner_branch.add(f"{repo_name} ([yellow]{branch}[/yellow], {status})")

    console.print(tree)


if __name__ == "__main__":
    cli()
