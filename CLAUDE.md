# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`reposort` is a Python utility that organizes git repositories by their origin URL. It scans a directory for git repositories and moves them to `~/code/` organized by host and path structure.

Example transformations:
- `git@github.com:user/repo.git` → `~/code/github.com/user/repo`
- `ssh://git@host:7999/team/project.git` → `~/code/host/team/project`
- `https://github.com/user/repo.git` → `~/code/github.com/user/repo`

## Development Setup

This project uses `uv` for dependency management:

```bash
# Install the package in editable mode with dev dependencies
uv sync

# Set up pre-commit hooks (runs ruff and ty automatically)
pre-commit install
```

## Running the Tool

```bash
# Dry-run to preview changes
reposort --dry-run

# Execute the reorganization (default: searches current dir, targets ~/code)
reposort

# Custom source and target directories
reposort --source /path/to/repos --target ~/projects

# Can also run as a module
python -m reposort --dry-run
```

## Code Quality Commands

The project includes a `justfile` for running common tasks:

```bash
# Recommended: Use just commands
just check           # Run type checking + linting
just typecheck       # Run ty
just lint            # Run ruff linter
just format          # Format code with ruff
just fix             # Auto-fix linting issues
just pre-commit      # Run all pre-commit hooks
just setup           # Install deps + setup pre-commit

# Manual commands (if not using just)
ty check src/reposort
ruff check src/reposort
ruff format src/reposort
pre-commit run --all-files
```

## Architecture

Package structure:
- `src/reposort/core.py` - Core business logic (pure functions)
- `src/reposort/cli.py` - Click CLI interface
- `src/reposort/__main__.py` - Entry point for `python -m reposort`

Four core functions in `core.py`:

1. **`parse_git_url(url)`** - Parses git URLs into (host, path) tuples. Handles three URL formats:
   - `ssh://` format (checked FIRST - order matters for correct parsing)
   - HTTPS/HTTP format (handles embedded usernames via urlparse)
   - SSH shorthand format (git@host:path)

2. **`find_git_repos(base_path)`** - Recursively finds all `.git` directories using Path.rglob()

3. **`get_unique_target_path(base_target)`** - Handles path conflicts by appending `-copy1`, `-copy2`, etc.

The CLI (`cli.py`) orchestrates these functions:
- Finds all repos using `find_git_repos()`
- Gets origin URLs via `get_git_origin_url()`
- Parses URLs using `parse_git_url()` to determine target paths
- Uses `get_unique_target_path()` to handle conflicts
- Prints plan with conflicts marked
- Executes moves (unless dry-run) using `shutil.move()`

## Key Implementation Details

- **Type hints**: Fully typed codebase using Python 3.13+ syntax (`str | None` instead of `Optional[str]`)
- **URL parsing order is critical**: `ssh://` URLs must be checked before SSH shorthand to avoid misparse (see `parse_git_url()` in core.py:44)
- **Conflict handling**: Uses numerical suffixes (`-copy1`, `-copy2`) rather than overwriting existing directories
- **Error handling**: Repos without origin URLs or unparseable URLs are skipped and reported
- **Pre-commit hooks**: Automatically runs ruff (formatting + linting) and ty (type checking) on commit
