# Contributing to Moondream FastMCP

Thank you for your interest in contributing to the Moondream FastMCP server! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of FastMCP and Model Context Protocol
- Familiarity with async Python programming

### Types of Contributions

We welcome several types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Implement features or fix bugs
- **Documentation**: Improve or add documentation
- **Testing**: Add or improve test coverage
- **Performance**: Optimize existing code

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/ColeMurray/moondream-mcp.git
cd moondream-mcp
```

### 2. Set Up Development Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### 3. Verify Setup

```bash
# Run tests to ensure everything works
pytest tests/

# Run linting
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

## Contributing Process

### 1. Create an Issue

Before starting work, create an issue to discuss:
- Bug reports with reproduction steps
- Feature requests with use cases
- Questions about implementation

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 3. Make Changes

- Follow the coding standards below
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new vision analysis tool

- Implement semantic segmentation capability
- Add comprehensive tests
- Update documentation
- Closes #123"
```

#### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

#### Pull Request Guidelines

- Use a clear, descriptive title
- Reference related issues
- Provide a detailed description of changes
- Include screenshots for UI changes
- Ensure all CI checks pass

## Coding Standards

### Python Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **Bandit**: Security analysis

### Code Quality Rules

1. **Type Hints**: All functions must have type hints
2. **Docstrings**: All public functions and classes must have docstrings
3. **Error Handling**: Use appropriate exception types and error messages
4. **Async/Await**: Use async/await for I/O operations
5. **Resource Management**: Use context managers for resource cleanup

### Example Code Style

```python
"""
Module for image processing utilities.
"""

import asyncio
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from moondream_mcp.models import ProcessingResult


async def process_image(
    image_path: Union[str, Path],
    max_size: Optional[tuple[int, int]] = None,
) -> ProcessingResult:
    """
    Process an image with optional resizing.
    
    Args:
        image_path: Path to the image file
        max_size: Optional maximum dimensions (width, height)
        
    Returns:
        ProcessingResult with success status and processed image
        
    Raises:
        ImageProcessingError: If image cannot be processed
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        raise ImageProcessingError(f"Failed to process image: {e}") from e
```

### File Organization

- Keep modules focused and cohesive
- Use clear, descriptive names
- Organize imports: standard library, third-party, local
- Limit line length to 88 characters (Black default)

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_config.py          # Configuration tests
├── test_moondream.py       # Client tests
├── test_server.py          # Server tests
└── test_tools/
    ├── __init__.py
    └── test_vision.py      # Tool tests
```

### Writing Tests

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **Mock External Dependencies**: Use mocks for PyTorch, HTTP requests
4. **Test Error Conditions**: Include negative test cases
5. **Use Fixtures**: Create reusable test data

### Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch

from moondream_mcp.moondream import MoondreamClient
from moondream_mcp.models import CaptionResult


class TestMoondreamClient:
    @pytest.fixture
    def client(self) -> MoondreamClient:
        """Create test client."""
        config = Config()
        return MoondreamClient(config)

    @pytest.mark.asyncio
    async def test_caption_image_success(self, client: MoondreamClient) -> None:
        """Test successful image captioning."""
        with patch.object(client, '_load_image') as mock_load:
            mock_load.return_value = Mock()
            
            result = await client.caption_image("test.jpg")
            
            assert result.success is True
            assert result.caption is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/moondream_mcp

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and type hints
2. **API Documentation**: Tool descriptions and examples
3. **User Documentation**: Installation and usage guides
4. **Developer Documentation**: Architecture and contributing guides

### Documentation Standards

- Use clear, concise language
- Provide examples for complex concepts
- Keep documentation up-to-date with code changes
- Use proper Markdown formatting

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation (if using Sphinx)
cd docs/
make html
```

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update Version**: Update version in `pyproject.toml`
2. **Update Changelog**: Add release notes to `CHANGELOG.md`
3. **Create Tag**: `git tag v1.0.0`
4. **Push Tag**: `git push origin v1.0.0`
5. **GitHub Actions**: Automatically builds and publishes to PyPI

### Pre-release Testing

Before releasing:

1. Run full test suite
2. Test installation from built package
3. Verify documentation is current
4. Check all CI/CD pipelines pass

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Request Reviews**: Code-specific discussions

### Resources

- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Moondream Model Documentation](https://huggingface.co/vikhyatk/moondream2)
- [Python Async Programming Guide](https://docs.python.org/3/library/asyncio.html)

## Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- GitHub contributor graphs

Thank you for contributing to Moondream FastMCP! 🚀 