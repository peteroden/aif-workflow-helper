# Testing the Release Pipeline

This document outlines how to safely test the entire release pipeline before pushing anything to production PyPI.

## Testing Strategies

### 1. Test PyPI (Recommended)

We've created a dedicated `test-release.yml` workflow that publishes to Test PyPI first.

**Setup:**

1. Create a Test PyPI account at <https://test.pypi.org/>
2. Generate an API token at <https://test.pypi.org/manage/account/token/>
3. Add the token as `TEST_PYPI_API_TOKEN` in GitHub repository secrets

**To test:**

1. Go to Actions tab in GitHub
2. Run "Test Release" workflow manually
3. Choose version bump type (patch/minor/major)
4. Monitor the workflow execution

**What it tests:**

- Full test suite execution
- Package building and validation
- Local package installation and CLI testing
- Publishing to Test PyPI
- Installation from Test PyPI

### 2. Local Testing

Test the package building and CLI locally before any releases:

```bash
# Install build dependencies
pip install build twine bump2version

# Test version bumping (dry run)
bump2version --dry-run --verbose patch

# Build the package
python -m build

# Check package integrity
twine check dist/*

# Test local installation
pip install dist/*.whl
aif-workflow-helper --help

# Clean up
rm -rf dist/
pip uninstall aif-workflow-helper
```

### 3. Branch-based Testing

Create a test branch to verify the workflows work:

```bash
# Create test branch
git checkout -b test-release-pipeline

# Make a small change (like updating README)
echo "Testing release pipeline" >> README.md
git add README.md
git commit -m "Test: trigger release pipeline"

# Push to test branch
git push origin test-release-pipeline

# Create PR to see CI workflow in action
# Merge PR to see if release workflow would trigger
```

### 4. Dry Run with Real Workflow

Modify the release workflow temporarily for testing:

1. Comment out the PyPI publishing step
2. Add `dry-run` flags to git operations
3. Run the workflow to see what would happen

### 5. Version Validation

Test the version bumping logic:

```bash
# Check current version
python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])"

# Test different bump types
bump2version --dry-run patch    # 0.1.0 -> 0.1.1
bump2version --dry-run minor    # 0.1.0 -> 0.2.0  
bump2version --dry-run major    # 0.1.0 -> 1.0.0
```

## Pre-Production Checklist

Before enabling the production release workflow:

- [ ] Test PyPI publishing works successfully
- [ ] Package installs correctly from Test PyPI
- [ ] CLI functions properly after installation
- [ ] Version bumping works as expected
- [ ] GitHub releases are created correctly
- [ ] All tests pass in CI pipeline
- [ ] CODEOWNERS file is properly configured
- [ ] Branch protection rules are in place

## Production Deployment

Once testing is complete:

1. Set up production PyPI API token in GitHub secrets as `PYPI_API_TOKEN`
2. Merge your changes to main branch
3. Monitor the first automated release carefully
4. Verify the package appears on PyPI
5. Test installation from production PyPI

## Rollback Plan

If something goes wrong:

1. Delete the problematic release from GitHub
2. Delete the package version from PyPI (if possible)
3. Fix the issue in a new commit
4. Re-run the release process

## Monitoring

Monitor these during releases:

- GitHub Actions workflow logs
- PyPI package page updates
- Download statistics
- User feedback on installation issues

## Tips

- Start with patch versions for testing
- Use Test PyPI extensively before production
- Keep release notes comprehensive
- Monitor for any breaking changes
- Have a rollback plan ready
