"""Core functionality for organizing git repositories."""

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def get_git_origin_url(repo_path: Path) -> str | None:
    """Get the origin URL of a git repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def clone_repository(url: str, target_path: Path) -> subprocess.CompletedProcess:
    """
    Clone a git repository to the specified path.

    Args:
        url: Git repository URL to clone
        target_path: Destination path for the cloned repository

    Returns:
        subprocess.CompletedProcess with result of git clone

    Raises:
        subprocess.CalledProcessError: If git clone fails
    """
    return subprocess.run(
        ["git", "clone", url, str(target_path)],
        capture_output=True,
        text=True,
        check=True,
    )


def parse_git_url(url: str) -> tuple[str, str] | None:
    """
    Parse a git URL and extract host and path.
    Handles SSH, HTTPS, and ssh:// URL formats.
    Returns (host, repo_path) or None if parsing fails.
    """
    if not url:
        return None

    # ssh:// format: ssh://git@host:port/path/to/repo.git
    # Check this FIRST before other patterns
    if url.startswith("ssh://"):
        # Remove ssh:// prefix
        url_without_prefix = url[6:]
        # Remove user@ if present
        if "@" in url_without_prefix:
            url_without_prefix = url_without_prefix.split("@", 1)[1]
        # Split host:port from path
        if "/" in url_without_prefix:
            host_part, path = url_without_prefix.split("/", 1)
            # Remove port if present
            host = host_part.split(":")[0]
            # Remove .git extension
            if path.endswith(".git"):
                path = path[:-4]
            path = path.rstrip("/")
            return (host, path)

    # HTTPS/HTTP format: https://github.com/user/repo.git
    # Also handles URLs with embedded usernames like https://user@host/path
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        # Use hostname to strip username from URLs like https://user@host/path
        host = parsed.hostname or parsed.netloc
        path = parsed.path.lstrip("/")
        # Remove .git extension
        if path.endswith(".git"):
            path = path[:-4]
        path = path.rstrip("/")
        return (host, path)

    # SSH format: git@github.com:user/repo.git or github.com:user/repo.git
    ssh_pattern = r"^(?:[\w\-]+@)?([^:]+):(.+?)(?:\.git)?$"
    ssh_match = re.match(ssh_pattern, url)
    if ssh_match:
        host = ssh_match.group(1)
        path = ssh_match.group(2)
        # Strip leading slashes to handle malformed URLs like git@host:/path
        path = path.lstrip("/")
        # Remove trailing slashes
        path = path.rstrip("/")
        return (host, path)

    return None


def find_git_repos(base_path: Path) -> list[Path]:
    """Find all git repositories recursively in the given path."""
    repos = []

    # Recursively find all .git directories
    for git_dir in base_path.rglob(".git"):
        if git_dir.is_dir():
            # The parent of .git is the repository root
            repo_path = git_dir.parent
            repos.append(repo_path)

    return repos


def get_unique_target_path(base_target: Path) -> Path:
    """
    Get a unique target path by appending -copy1, -copy2, etc. if needed.
    """
    if not base_target.exists():
        return base_target

    counter = 1
    while True:
        new_target = Path(f"{base_target}-copy{counter}")
        if not new_target.exists():
            return new_target
        counter += 1
