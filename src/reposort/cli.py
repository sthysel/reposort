"""Click CLI for reposort."""

import shutil
from pathlib import Path

import click

from reposort.core import find_git_repos, get_git_origin_url, get_unique_target_path, parse_git_url


@click.command()
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
def main(source: Path, target: Path, dry_run: bool) -> None:
    """
    Organize git repositories by their origin URL.

    Examples:
      reposort --dry-run
        Show what would be moved without making changes

      reposort
        Execute the repository reorganization

      reposort --source /path/to/repos --target ~/projects
        Organize repos from custom source to custom target
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


if __name__ == "__main__":
    main()
