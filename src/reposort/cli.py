"""Click CLI for reposort."""

import shutil
import subprocess
from pathlib import Path

import click

from reposort.core import (
    clone_repository,
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
def clone(url: str, target: Path, dry_run: bool) -> None:
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
        clone_repository(url, final_target)

        click.echo(f"✓ Successfully cloned to {final_target}")

    except subprocess.CalledProcessError as e:
        click.echo("✗ Failed to clone repository", err=True)
        if e.stderr:
            click.echo(f"Git error: {e.stderr}", err=True)
        raise click.Abort() from e
    except OSError as e:
        click.echo(f"✗ File system error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
