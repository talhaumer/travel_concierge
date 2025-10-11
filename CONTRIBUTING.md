# Contributing to Travel Concierge

First off, thank you for considering contributing to Travel Concierge! It's people like you that make this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project and everyone participating in it is governed by respect and professionalism. By participating, you are expected to uphold this standard.

## Getting Started

- Make sure you have Python 3.11+ installed
- Fork the repository on GitHub
- Clone your fork locally
- Set up the development environment

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

1. **Bug Reports**: Found a bug? Let us know!
2. **Feature Requests**: Have an idea? Share it with us!
3. **Code Contributions**: Want to fix a bug or add a feature? Submit a PR!
4. **Documentation**: Help improve our docs
5. **Testing**: Add or improve test coverage
6. **Reviews**: Review pull requests

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/travel_concierge.git
   cd travel_concierge
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://github.com/psf/black) for code formatting
- Use [flake8](https://flake8.pycqa.org/) for linting
- Use type hints where appropriate

### Code Formatting

Before submitting, format your code:

```bash
black src/ tests/
flake8 src/ tests/
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `UserInputAgent`)
- **Functions/Methods**: snake_case (e.g., `process_user_input`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)
- **Private methods**: Prefix with underscore (e.g., `_internal_method`)

### Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style docstrings
- Update README.md if adding new features
- Update CHANGELOG.md with your changes

Example docstring:
```python
def search_places(query: str, location: str = None, limit: int = 10) -> List[PlaceDetails]:
    """Search for places using OpenStreetMap Nominatim API.
    
    Args:
        query: Search query string
        location: Location to search in (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of PlaceDetails objects
        
    Raises:
        ValueError: If query is empty
        requests.RequestException: If API call fails
    """
```

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, readable code
   - Add tests if applicable
   - Update documentation

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting, etc.)
   - `refactor:` Code refactoring
   - `test:` Adding or updating tests
   - `chore:` Maintenance tasks

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template
   - Link any related issues

### PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New code is covered by tests (if applicable)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains what and why

## Reporting Bugs

### Before Submitting a Bug Report

- Check the [Issues](https://github.com/yourusername/travel_concierge/issues) to see if it's already reported
- Make sure you're using the latest version
- Try to reproduce the bug in isolation

### How to Submit a Bug Report

Create an issue with:

1. **Title**: Clear, descriptive title
2. **Description**: What happened vs. what you expected
3. **Steps to reproduce**: Detailed steps
4. **Environment**: OS, Python version, package versions
5. **Screenshots**: If applicable
6. **Error messages**: Full stack trace

Example:
```markdown
**Bug Description**
The system crashes when planning a trip to an unknown location.

**Steps to Reproduce**
1. Initialize TravelGraph
2. Call invoke() with "Plan a trip to Atlantis"
3. System crashes with KeyError

**Expected Behavior**
Should gracefully handle unknown locations with fallback

**Environment**
- OS: Windows 11
- Python: 3.11.5
- LangGraph: 0.2.0

**Stack Trace**
```
[paste full error here]
```
```

## Suggesting Enhancements

### Before Submitting an Enhancement

- Check if it's already been suggested
- Consider if it fits the project's scope
- Think about how it benefits users

### How to Suggest an Enhancement

Create an issue with:

1. **Title**: Clear feature request title
2. **Motivation**: Why is this needed?
3. **Proposed Solution**: How would it work?
4. **Alternatives**: Other approaches considered
5. **Additional Context**: Screenshots, examples, etc.

## Testing

### Running Tests

```bash
pytest tests/
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Test both success and failure cases

Example:
```python
def test_search_places_returns_results():
    """Test that search_places returns valid results for Paris."""
    results = search_places("tourist attractions", "Paris", limit=5)
    assert len(results) > 0
    assert all(isinstance(place, PlaceDetails) for place in results)
```

## Questions?

If you have questions:

1. Check the [README.md](README.md)
2. Search existing [Issues](https://github.com/yourusername/travel_concierge/issues)
3. Open a new issue with the "question" label

## Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute! 🎉

