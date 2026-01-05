# reposort v0.1.8

Organize git repositories by their origin URL.

## Why?

If you work with many git repositories, you've probably had these self-inflicted
problems:

- **Scattered repositories**: Repos cloned into random directories (`~/workspace`, `~/stufs`, `~/tmp/test123`)
- **Hard to find projects**: No consistent structure makes it difficult to locate specific repositories
- **Duplicate clones**: Multiple copies of the same repo in different locations
- **Mixed sources**: Repos from GitHub, GitLab, BitBucket, and private servers all jumbled together
- **Lost context**: Directory names don't reflect the organization or team that owns the repo

`reposort` solves this by automatically organizing all your git repositories
based on their remote origin URL, creating a predictable, hierarchical structure
that mirrors the source hosting:

```
~/code/
├── github.com/
│   ├── torvalds/linux
│   └── youruser/yourproject
├── gitlab.com/
│   └── yourteam/backend
└── git.company.com/
    ├── platform/api
    └── platform/frontend
```

This structure makes it easy to:
- Find a repository in context
- Understand where a project comes from at a glance
- Avoid duplicate clones
- Navigate related projects from the same organization
- Script operations across repositories by host or team

**Tip**: While this organization provides a clean canonical structure, you can
maintain a "linkfarm" of symbolic links to frequently used repositories or
project groups for quick access:

```bash
~/active/
├── current-project -> ~/code/github.com/mycompany/api
├── monitoring -> ~/code/github.com/mycompany/monitoring
└── dotfiles -> ~/code/github.com/me/dotfiles
```

This gives you both: a well-organized source of truth and convenient shortcuts for active work.

## Installation

### For Users

Install as a tool using uv:

```bash
# Install globally as a tool
uv tool install reposort

# Or run directly without installation
uvx reposort --dry-run
```

Using `uvx` is convenient for one-off runs or trying the tool without installing it. The tool will be downloaded and cached automatically.

### For Development

Clone the repository and install in editable mode:

```bash
uv sync
```

This will create a virtual environment, install the package in editable mode, and install all dependencies (including dev dependencies from the lockfile).

## Usage

```bash
# Dry-run to preview changes
reposort --dry-run

# Execute the reorganization (default: searches current dir, targets ~/code)
reposort

# Custom source and target directories
reposort --source /path/to/repos --target ~/projects
```

## Examples

Transforms repositories like:
- `git@github.com:user/repo.git` → `~/code/github.com/user/repo`
- `ssh://git@host:7999/team/project.git` → `~/code/host/team/project`
- `https://github.com/user/repo.git` → `~/code/github.com/user/repo`

## Development

### Quick Start with just

This project includes a `justfile` for common development tasks:

```bash
# Set up dev environment (install deps + pre-commit hooks)
just setup

# Run type checking
just typecheck

# Run linting
just lint

# Auto-fix linting issues
just fix

# Format code
just format

# Run all checks
just check

# Run pre-commit hooks on all files
just pre-commit

# Clean build artifacts
just clean

# See all available commands
just --list
```

### Manual Commands

Install dependencies:

```bash
uv sync
```

Set up pre-commit hooks:

```bash
pre-commit install
```

Run type checking:

```bash
ty check src/reposort
```

Run formatting and linting:

```bash
ruff check src/reposort
ruff format src/reposort
```
