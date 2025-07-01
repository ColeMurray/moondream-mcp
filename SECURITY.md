# Security Policy

## Supported Versions

We provide security updates for the following versions of Moondream FastMCP:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Moondream FastMCP seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Create a Public Issue

Please **do not** create a public GitHub issue for security vulnerabilities. This could put users at risk.

### 2. Report Privately

Please report security vulnerabilities via GitHub Security Advisories at: https://github.com/ColeMurray/moondream-mcp/security/advisories/new

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (if you have them)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity (see below)

### 4. Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, privilege escalation | 24-48 hours |
| **High** | Data exposure, authentication bypass | 3-7 days |
| **Medium** | Limited data exposure, DoS | 1-2 weeks |
| **Low** | Information disclosure, minor issues | 2-4 weeks |

## Security Measures

### Code Security

- **Static Analysis**: We use Bandit for security scanning
- **Dependency Scanning**: Regular checks with Safety
- **Code Review**: All changes require review
- **Type Safety**: Comprehensive type hints with mypy

### Input Validation

- **Image Validation**: File type, size, and content validation
- **URL Validation**: Proper URL parsing and validation
- **Parameter Validation**: Pydantic models for all inputs
- **Path Traversal Protection**: Secure file path handling

### Network Security

- **HTTPS Only**: All external requests use HTTPS
- **Timeout Limits**: Configurable timeouts for all operations
- **Rate Limiting**: Built-in concurrency controls
- **Content Validation**: Strict content-type checking

### Resource Management

- **Memory Limits**: Configurable memory usage limits
- **File Size Limits**: Maximum file size enforcement
- **Process Isolation**: Proper resource cleanup
- **Error Handling**: No sensitive data in error messages

### Authentication & Authorization

- **No Default Credentials**: No hardcoded credentials
- **Environment Variables**: Secure configuration management
- **Minimal Permissions**: Principle of least privilege
- **Session Management**: Proper session handling

## Security Best Practices for Users

### Installation

```bash
# Always install from official sources
pip install moondream-mcp

# Verify package integrity
pip install --require-hashes moondream-mcp
```

### Configuration

```bash
# Use environment variables for sensitive configuration
export MOONDREAM_DEVICE=cpu
export MOONDREAM_MAX_IMAGE_SIZE=2048

# Avoid hardcoding sensitive values
# ❌ Don't do this
MOONDREAM_API_KEY="secret-key-here"

# ✅ Do this instead
export MOONDREAM_API_KEY="your-secret-key"
```

### Network Security

```bash
# Use HTTPS for remote images
# ✅ Secure
https://example.com/image.jpg

# ❌ Insecure
http://example.com/image.jpg
```

### File Handling

```python
# Validate file paths
import os
from pathlib import Path

def safe_path(user_path: str) -> Path:
    """Safely resolve user-provided paths."""
    path = Path(user_path).resolve()
    
    # Ensure path is within allowed directory
    if not str(path).startswith("/allowed/directory/"):
        raise ValueError("Path not allowed")
    
    return path
```

## Known Security Considerations

### Model Security

- **Model Weights**: Downloaded from Hugging Face Hub
- **Trust Remote Code**: Disabled by default
- **Model Validation**: Checksum verification recommended

### Image Processing

- **File Types**: Limited to safe image formats
- **Size Limits**: Configurable maximum file sizes
- **Memory Usage**: Automatic cleanup and limits

### Network Requests

- **URL Validation**: Strict URL parsing
- **Redirect Limits**: Maximum redirect count
- **Timeout Enforcement**: Configurable timeouts

## Security Updates

### Notification

Security updates will be announced through:
- GitHub Security Advisories
- Release notes in CHANGELOG.md
- PyPI package updates

### Update Process

```bash
# Check for updates regularly
pip list --outdated

# Update to latest version
pip install --upgrade moondream-mcp

# Verify installation
python -c "import moondream_mcp; print(moondream_mcp.__version__)"
```

## Vulnerability Disclosure Policy

### Coordinated Disclosure

We follow responsible disclosure practices:

1. **Private Reporting**: Initial report through secure channels
2. **Investigation**: We investigate and develop fixes
3. **Coordination**: We work with reporters on disclosure timeline
4. **Public Disclosure**: After fixes are available and deployed

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Credited in security advisories (with permission)
- Listed in our security acknowledgments
- Eligible for our bug bounty program (if applicable)

## Security Checklist for Developers

### Before Committing

- [ ] No hardcoded secrets or credentials
- [ ] Input validation for all user inputs
- [ ] Proper error handling without information leakage
- [ ] Resource cleanup in all code paths
- [ ] Security tests for new features

### Before Releasing

- [ ] Security scan with Bandit passes
- [ ] Dependency scan with Safety passes
- [ ] All tests pass including security tests
- [ ] Documentation updated for security considerations
- [ ] Security review completed

## Contact Information

For security-related questions or concerns:

- **Security Reports**: GitHub Security Advisories at https://github.com/ColeMurray/moondream-mcp/security/advisories/new
- **General Issues**: GitHub Issues (for non-security bugs)
- **Documentation**: GitHub Discussions

## Legal

This security policy is subject to our terms of service and privacy policy. By reporting security vulnerabilities, you agree to our coordinated disclosure process.

---

**Last Updated**: [Current Date]
**Version**: 1.0 