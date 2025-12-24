# reposort

Organize git repositories by their origin URL.

## Installation

Using uv:

```bash
uv pip install -e .
```

Or install with development dependencies:

```bash
uv pip install -e ".[dev]"
```

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

Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

Set up pre-commit hooks:

```bash
pre-commit install
```

Run type checking:

```bash
mypy src/reposort
```

Run formatting and linting:

```bash
ruff check src/reposort
ruff format src/reposort
```
