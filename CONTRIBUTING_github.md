---
noteId: "96130da019ed11f09071fbd8dcae28ef"
tags: []

---

# Contributing to AWS Cost Explorer MCP Server

Thank you for your interest in contributing to the AWS Cost Explorer MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Screenshots (if applicable)
6. Environment details (OS, Python version, etc.)

### Suggesting Enhancements

For feature requests or enhancements:

1. Create an issue with a clear title and detailed description
2. Explain why this enhancement would be useful
3. Suggest an implementation approach if possible

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Submit a pull request

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/jamon8888/aws-cost-explorer-mcp.git
   cd aws-cost-explorer-mcp
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

3. Run tests
   ```bash
   pytest
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Write unit tests for new functionality

## Testing

- Add tests for new features or bug fixes
- Ensure all tests pass before submitting a pull request
- Run the comprehensive test suite:
  ```bash
  python comprehensive_test.py
  ```

## Documentation

- Update documentation for any changes to the API or functionality
- Include examples for new features

## Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers when applicable

## Versioning

This project follows [Semantic Versioning](https://semver.org/).

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
