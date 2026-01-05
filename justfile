set shell := ["bash", "-c"]
set export

[doc("Show available commands")]
help:
    @just --list

[doc("Install package with dev dependencies")]
install:
    uv sync

[doc("Set up pre-commit hooks")]
setup: install
    pre-commit install

[doc("Run type checking with ty")]
typecheck:
    ty check src/reposort

[doc("Run ruff linter")]
lint:
    ruff check src/reposort

[doc("Run ruff formatter")]
format:
    ruff format src/reposort

[doc("Fix linting issues automatically")]
fix:
    ruff check --fix src/reposort

[doc("Run all checks (type checking + linting)")]
check: typecheck lint

[doc("Run all pre-commit hooks on all files")]
pre-commit:
    pre-commit run --all-files

[doc("Update pre-commit hook versions")]
pre-commit-update:
    pre-commit autoupdate

[doc("Run the tool in dry-run mode")]
dry-run:
    reposort --dry-run

[doc("Run the tool")]
run *ARGS:
    reposort {{ARGS}}

[doc("Clean up build artifacts and cache")]
clean:
    rm -rf build/ dist/ *.egg-info .mypy_cache/ .ruff_cache/ .pytest_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +

[doc("Clean and rebuild")]
rebuild: clean build

[doc("Bump patch version (0.0.X)")]
bump-patch:
    bump-my-version bump patch

[doc("Bump minor version (0.X.0)")]
bump-minor:
    bump-my-version bump minor

[doc("Bump major version (X.0.0)")]
bump-major:
    bump-my-version bump major

[doc("Build wheel and sdist")]
build:
    uv build

[doc("Publish to PyPI")]
publish:
    uv publish

[doc("Publish to TestPyPI")]
publish-test:
    uv publish --publish-url https://test.pypi.org/legacy/
