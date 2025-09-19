# pr-collector

Collect PR diffs and metadata into markdown files

## Features

- **CLI Application** with Typer framework for easy command-line usage
- **GitHub Integration** via PyGitHub for fetching PR metadata
- **Git Integration** via GitPython for generating diffs
- **Rich terminal output** with colors and formatting
- **Flexible directory targeting** - collect diffs for specific directories or entire repos
- **Filesystem-safe filenames** automatically generated from PR titles
- **GitHub token support** via environment variable or command line
- **Global installation** support via pipx
- **Modern Python tooling** (uv, ruff, black, pyright, pytest)

## Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pr-collector.git
cd pr-collector

# Install dependencies
make install-dev
```

### Global Installation
Install pr_collector globally using pipx (recommended):

```bash
# Build and install globally
make install-package

# Or manually:
make build
pipx install .
```

After installation, you can use the `pr-collector` command from anywhere.

### Uninstall

```bash
make uninstall-package
# Or: pipx uninstall pr_collector
```
## Usage

### Basic Usage

```bash
# Show help
pr-collector --help

# Auto-detect PR from current branch (most common usage)
pr-collector collect

# Collect specific PR #123 from current directory
pr-collector collect 123

# Auto-detect PR with specific repository path
pr-collector collect --repo /path/to/repo

# Collect PR for specific directory only
pr-collector collect --dir src/components

# Specify output directory
pr-collector collect --output /path/to/output

# Use GitHub token for private repos or higher rate limits
pr-collector collect --token ghp_your_token_here
# Or set environment variable
export GITHUB_TOKEN=ghp_your_token_here
pr-collector collect

# Show application info
pr-collector info
```

### Examples

```bash
# Auto-detect current PR for the 'backend' directory, save to 'reviews' folder
pr-collector collect --dir backend --output reviews

# Collect specific PR #456 for the 'backend' directory
pr-collector collect 456 --dir backend --output reviews

# Auto-detect PR from a specific repository
pr-collector collect --repo ~/projects/my-app --output .
```

## Development

### Setup

```bash
# Install development dependencies
make install-dev

# Install pre-commit hooks
uv run pre-commit install
```

### Common Commands

```bash
# Run tests
make test

# Run linting
make lint

# Fix formatting
make tidy

# Run all checks
make check

# Build documentation
make docs

# Build and serve docs locally
make docs-serve

# Build package
make build

# Install globally
make install-package

# Bump version
make version-dev
```

### Testing

```bash
# Run tests with coverage
make test-cov
```

## Documentation

This project uses [Sphinx](https://www.sphinx-doc.org/) for documentation generation.

### Building Documentation

```bash
# Build HTML documentation
make docs

# Build and serve locally (opens in browser at http://localhost:8080)
make docs-serve

# Clean documentation build files
make clean
```

### Editing Documentation

Documentation source files live under `docs/sphinx/`:

- `docs/sphinx/index.rst` - Main documentation page
- `docs/sphinx/installation.rst` - Installation instructions
- `docs/sphinx/usage.rst` - Usage examples and tutorials
- `docs/sphinx/api.rst` - Auto-generated API reference

### GitHub Pages Deployment

Documentation is automatically built and deployed to GitHub Pages when you push to the `main` branch. The docs will be available at:

`https://yourusername.github.io/pr-collector/`

To enable GitHub Pages:
1. Go to your repository Settings → Pages
2. Select "GitHub Actions" as the source
3. Push to main branch to trigger the first build

## Docker

```bash
# Build image
make docker-build

# Run container
make docker-run
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
