# PyPI Publishing Setup

This repository is configured to automatically publish releases to PyPI when PRs are merged to the `main` branch.

## Required Secrets

To enable PyPI publishing, you need to set up the following GitHub repository secret:

### 1. PyPI API Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Create a new API token with scope limited to this project
3. Copy the token (starts with `pypi-`)
4. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**
5. Create a new repository secret:
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Your PyPI API token

## Release Process

### Automatic Releases (Recommended)

When a PR is merged to `main`:

1. **Tests run** on Python 3.10, 3.11, and 3.12
2. **Version is auto-bumped** based on commit messages:
   - `patch` (0.1.0 → 0.1.1): Default for most commits
   - `minor` (0.1.0 → 0.2.0): Commits containing "feat", "feature", or "minor"
   - `major` (0.1.0 → 1.0.0): Commits containing "breaking" or "major"
3. **Git tag is created** (e.g., `v0.1.1`)
4. **GitHub Release is created** with auto-generated changelog
5. **Package is built and published** to PyPI

### Manual Releases

You can also trigger a release manually:

1. Go to **Actions** → **Release** workflow
2. Click **Run workflow**
3. Choose the version bump type (`patch`, `minor`, or `major`)
4. Click **Run workflow**

## Version Bump Rules

The automatic version bumping follows these rules based on commit messages:

- **Major** (breaking changes): Commit messages containing "breaking" or "major"
- **Minor** (new features): Commit messages containing "feat", "feature", or "minor"  
- **Patch** (bug fixes): All other commits (default)

### Examples

```bash
# These will trigger a PATCH release (0.1.0 → 0.1.1)
git commit -m "Fix validation bug"
git commit -m "Update documentation"
git commit -m "Refactor upload logic"

# These will trigger a MINOR release (0.1.0 → 0.2.0)
git commit -m "Add feature: YAML support"
git commit -m "feat: new download format"
git commit -m "minor: improve CLI interface"

# These will trigger a MAJOR release (0.1.0 → 1.0.0)
git commit -m "breaking: change API interface"
git commit -m "major: remove deprecated functions"
```

## Package Information

- **PyPI Package**: [`aif-workflow-helper`](https://pypi.org/project/aif-workflow-helper/)
- **Installation**: `pip install aif-workflow-helper`
- **CLI Command**: `aif-workflow-helper`

## Workflow Files

- **CI/CD**: `.github/workflows/ci.yml` - Tests on PRs
- **Release**: `.github/workflows/release.yml` - Automated releases
- **Version Config**: `.bumpversion.cfg` - Version bump configuration