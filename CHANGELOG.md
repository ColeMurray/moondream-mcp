# Changelog

All notable changes to the Moondream FastMCP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-19

### Added

#### Core Features
- **FastMCP Server Implementation**: Complete MCP server using FastMCP framework
- **Moondream2 Integration**: Full integration with Moondream2 vision language model
- **Async Architecture**: Fully asynchronous implementation for optimal performance
- **Type Safety**: Comprehensive type hints and Pydantic models throughout

#### Vision Analysis Tools
- **Image Captioning**: Generate captions with configurable length (short/normal/detailed)
- **Visual Question Answering**: Ask natural language questions about images
- **Object Detection**: Detect and locate specific objects in images
- **Visual Pointing**: Point to specific objects or regions in images
- **Comprehensive Analysis**: Combined analysis tool for multiple operations
- **Batch Processing**: Process multiple images simultaneously (up to 10 images)

#### Configuration & Environment
- **Flexible Configuration**: Environment-based configuration with sensible defaults
- **Device Support**: Auto-detection and support for CPU, CUDA, and Apple Silicon (MPS)
- **Resource Management**: Configurable memory limits, timeouts, and concurrency controls
- **Image Processing**: Automatic image preprocessing, resizing, and format conversion

#### Developer Experience
- **Claude Desktop Integration**: Automated setup script for Claude Desktop
- **Comprehensive Testing**: 52 unit tests with 94%+ coverage
- **Type Checking**: Full mypy compliance with strict type checking
- **Code Quality**: Black formatting, isort import sorting, and comprehensive linting

#### Security & Reliability
- **Input Validation**: Strict validation for all inputs using Pydantic
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Resource Cleanup**: Proper cleanup of models, sessions, and GPU memory
- **Security Scanning**: Bandit security analysis and dependency vulnerability checking

#### Documentation
- **Comprehensive README**: Detailed installation, usage, and configuration guide
- **API Documentation**: Complete tool descriptions with examples
- **Contributing Guide**: Detailed guidelines for contributors
- **Security Policy**: Comprehensive security policy and vulnerability reporting process

#### CI/CD & Distribution
- **Multi-Platform CI**: Testing on Ubuntu, macOS, and Windows
- **Python Version Support**: Python 3.10, 3.11, and 3.12 support
- **Automated Releases**: GitHub Actions for automated building and PyPI publishing
- **Security Scanning**: CodeQL analysis and dependency vulnerability scanning

### Technical Details

#### Dependencies
- **FastMCP**: >=2.0.0 for MCP server framework
- **PyTorch**: >=2.0.0 for model inference
- **Transformers**: >=4.35.0 for Moondream2 model
- **Pillow**: >=10.0.0 for image processing
- **Pydantic**: >=2.0.0 for data validation
- **aiohttp**: >=3.8.0 for async HTTP requests

#### Performance Optimizations
- **Concurrent Processing**: Semaphore-based concurrency control
- **Memory Management**: Automatic GPU memory cleanup and limits
- **Image Optimization**: Automatic resizing and format conversion
- **Async I/O**: Non-blocking file and network operations

#### Error Handling
- **Custom Exceptions**: Specific exception types for different error categories
- **Graceful Degradation**: Fallback mechanisms for various failure scenarios
- **Detailed Logging**: Comprehensive logging with configurable levels
- **User-Friendly Messages**: Clear error messages without exposing sensitive information

### Installation

```bash
# Install from PyPI
pip install moondream-mcp

# Install with development dependencies
pip install moondream-mcp[dev]

# Install from source
git clone https://github.com/ColeMurray/moondream-mcp.git
cd moondream-mcp
pip install -e ".[dev]"
```

### Quick Start

```bash
# Run the MCP server
moondream-mcp

# Set up Claude Desktop integration
setup-claude-desktop

# Configure device (optional)
export MOONDREAM_DEVICE=auto  # or cpu, cuda, mps
```

### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MOONDREAM_DEVICE` | `auto` | Device for inference (auto/cpu/cuda/mps) |
| `MOONDREAM_MODEL_NAME` | `vikhyatk/moondream2` | Hugging Face model name |
| `MOONDREAM_MODEL_REVISION` | `main` | Model revision/branch |
| `MOONDREAM_MAX_IMAGE_SIZE` | `2048` | Maximum image dimension |
| `MOONDREAM_MAX_FILE_SIZE_MB` | `50` | Maximum file size in MB |
| `MOONDREAM_TIMEOUT_SECONDS` | `30` | Processing timeout |
| `MOONDREAM_MAX_CONCURRENT` | `4` | Maximum concurrent requests |

### Supported Platforms

- **Operating Systems**: Linux, macOS, Windows
- **Python Versions**: 3.10, 3.11, 3.12
- **Hardware**: CPU, NVIDIA GPU (CUDA), Apple Silicon (MPS)

### Breaking Changes

This is the initial release, so no breaking changes from previous versions.

### Migration Guide

This is the initial release. For users migrating from other vision analysis tools:

1. Install moondream-mcp: `pip install moondream-mcp`
2. Set up Claude Desktop: `setup-claude-desktop`
3. Configure environment variables as needed
4. Start using the vision analysis tools in Claude

### Known Issues

- Model loading may take 30-60 seconds on first run
- Large images (>10MB) may cause memory issues on systems with limited RAM
- CUDA support requires compatible PyTorch installation

### Contributors

- Initial implementation and architecture
- Comprehensive testing suite
- Documentation and examples
- CI/CD pipeline setup

### Acknowledgments

- [Moondream2](https://huggingface.co/vikhyatk/moondream2) by vikhyatk for the vision language model
- [FastMCP](https://github.com/jlowin/fastmcp) by jlowin for the MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io/) specification

---

## [Unreleased]

### Planned Features
- Streaming response support for real-time caption generation
- Additional vision models (LLaVA, BLIP-2)
- Image generation capabilities
- Video analysis support
- Custom model fine-tuning utilities

---

For more information, see the [README](README.md) and [documentation](https://moondream-mcp.readthedocs.io/).

[1.0.0]: https://github.com/ColeMurray/moondream-mcp/releases/tag/v1.0.0 