# Branch Protection Settings for main branch

## Apply these settings in GitHub repo settings -> Branches -> Add rule

## Branch name pattern: main

### Protect matching branches

- [x] Restrict pushes that create files larger than 100MB
- [x] Require a pull request before merging
  - [x] Require approvals: 1
  - [x] Dismiss stale reviews when new commits are pushed
  - [x] Require review from code owners (if CODEOWNERS file exists)
- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date before merging
  - Required status checks:
    - test (3.10)
    - test (3.11)
    - test (3.12)
    - package-test
- [x] Require conversation resolution before merging
- [x] Restrict pushes that create files larger than 100MB
- [ ] Allow force pushes (keep unchecked for safety)
- [ ] Allow deletions (keep unchecked for safety)

### Additional recommendations

- Consider requiring signed commits
- Consider requiring administrators to follow these rules
- Set up CODEOWNERS file for automatic review assignments
