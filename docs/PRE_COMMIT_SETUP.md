# Pre-Commit Hooks Setup

## Overview

Pre-commit hooks automatically check your code before each commit, catching issues early and maintaining code quality.

## Installation

### 1. Install Pre-Commit

```bash
# Using Poetry (recommended)
poetry add --group dev pre-commit black isort flake8 bandit detect-secrets

# Or using pip
pip install pre-commit black isort flake8 bandit detect-secrets
```

### 2. Install Git Hooks

```bash
pre-commit install
```

This installs hooks into `.git/hooks/pre-commit`

### 3. (Optional) Install Commit Message Hook

```bash
pre-commit install --hook-type commit-msg
```

## What Gets Checked

### Code Quality

- ✅ **Trailing whitespace** - Removes trailing spaces
- ✅ **End of file** - Ensures files end with newline
- ✅ **YAML/JSON/TOML** - Validates configuration files
- ✅ **Large files** - Warns about files > 1MB
- ✅ **Merge conflicts** - Detects unresolved conflicts
- ✅ **Private keys** - Prevents committing secrets

### Python Code

- ✅ **Black** - Auto-formats Python code
- ✅ **isort** - Sorts imports automatically
- ✅ **Flake8** - Lints Python code
- ✅ **Bandit** - Security vulnerability scanner

### Security

- ✅ **Detect Secrets** - Finds hardcoded secrets/credentials
- ✅ **Private Key Detection** - Prevents committing SSH keys

### Configuration

- ✅ **Poetry Lock** - Ensures `poetry.lock` is up to date
- ✅ **Dockerfile** - Lints Dockerfile syntax
- ✅ **YAML** - Validates YAML files
- ✅ **Markdown** - Lints markdown files

### Commit Messages

- ✅ **Commitizen** - Enforces conventional commit format

## Usage

### Automatic (Recommended)

Hooks run automatically when you commit:

```bash
git add .
git commit -m "feat: Add new feature"
# Pre-commit hooks run automatically
```

### Manual Run

Run hooks on all files:

```bash
pre-commit run --all-files
```

Run specific hook:

```bash
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

### Skip Hooks (Not Recommended)

```bash
git commit --no-verify -m "message"
```

## Common Issues & Fixes

### Issue: Black reformats code

**Solution**: Let Black format it automatically. It ensures consistent style.

```bash
# Black will auto-format on commit
# Or run manually:
black src/
```

### Issue: isort reorders imports

**Solution**: This is expected. isort ensures consistent import order.

```bash
# Run manually to see changes:
isort src/ --check --diff
```

### Issue: Flake8 finds errors

**Solution**: Fix the errors or add exceptions:

```python
# Ignore specific line
print("test")  # noqa: E501

# Ignore entire file
# flake8: noqa
```

### Issue: Poetry lock out of date

**Solution**: Update poetry.lock:

```bash
poetry lock
git add poetry.lock
git commit -m "chore: Update poetry.lock"
```

### Issue: Secrets detected

**Solution**: Remove secrets or add to `.secrets.baseline`:

```bash
# Update baseline after reviewing
detect-secrets scan --update .secrets.baseline
```

## Configuration

### Customize Hooks

Edit `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/psf/black
  rev: 24.1.1
  hooks:
    - id: black
      args: [--line-length=120]  # Custom line length
```

### Skip Specific Files

Add to `.pre-commit-config.yaml`:

```yaml
- id: black
  exclude: ^(migrations/|legacy/)
```

### Disable Hook Temporarily

Comment out in `.pre-commit-config.yaml`:

```yaml
# - id: flake8  # Temporarily disabled
```

## Update Hooks

Update to latest versions:

```bash
pre-commit autoupdate
```

## CI/CD Integration

Pre-commit hooks also run in CI/CD pipeline:

```yaml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

## Best Practices

1. **Always run hooks** - Don't skip unless absolutely necessary
2. **Fix issues immediately** - Don't accumulate technical debt
3. **Update hooks regularly** - Keep tools up to date
4. **Customize for your needs** - Adjust configuration as needed
5. **Review auto-fixes** - Check what Black/isort changed

## Commit Message Format

Pre-commit enforces conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```bash
git commit -m "feat: Add user authentication"
git commit -m "fix: Resolve CORS parsing issue"
git commit -m "docs: Update API documentation"
```

## Troubleshooting

### Hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Slow hooks

```bash
# Run only on changed files (default)
# Or skip specific slow hooks temporarily
```

### Hook conflicts

```bash
# Update all hooks
pre-commit autoupdate

# Clear cache
pre-commit clean
```

---

**Pre-commit hooks help maintain code quality and catch issues early! 🛡️**
