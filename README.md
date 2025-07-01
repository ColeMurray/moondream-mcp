# Moondream MCP Server

A FastMCP server for [Moondream](https://github.com/vikhyat/moondream), an AI vision language model. This server provides image analysis capabilities including captioning, visual question answering, object detection, and visual pointing through the Model Context Protocol (MCP).

## Features

- 🖼️ **Image Captioning**: Generate short, normal, or detailed captions for images
- ❓ **Visual Question Answering**: Ask natural language questions about images
- 🔍 **Object Detection**: Detect and locate specific objects with bounding boxes
- 📍 **Visual Pointing**: Get precise coordinates of objects in images
- 🔗 **URL Support**: Process images from both local files and remote URLs
- ⚡ **Batch Processing**: Analyze multiple images efficiently
- 🚀 **Device Optimization**: Automatic detection and optimization for CPU, CUDA, and MPS (Apple Silicon)

## Installation

### Prerequisites

- Python 3.10 or higher
- PyTorch 2.0+ (with appropriate device support)

### Using uvx (Recommended for Claude Desktop)

```bash
# Run without installation
uvx moondream-mcp

# Or specify a specific version
uvx moondream-mcp==1.0.0
```

### Install from PyPI

```bash
pip install moondream-mcp
```

### Install from Source

```bash
git clone https://github.com/ColeMurray/moondream-mcp.git
cd moondream-mcp
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/ColeMurray/moondream-mcp.git
cd moondream-mcp
pip install -e ".[dev]"
```

## Quick Start

### Running the Server

```bash
# Using uvx (no installation needed)
uvx moondream-mcp

# Using pip-installed command
moondream-mcp

# Or run directly with Python
python -m moondream_mcp.server
```

### Claude Desktop Integration

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Using uvx (Recommended)

```json
{
  "mcpServers": {
    "moondream": {
      "command": "uvx",
      "args": ["moondream-mcp"],
      "env": {
        "MOONDREAM_DEVICE": "auto"
      }
    }
  }
}
```

#### Using pip-installed command

```json
{
  "mcpServers": {
    "moondream": {
      "command": "moondream-mcp",
      "env": {
        "MOONDREAM_DEVICE": "auto"
      }
    }
  }
}
```

## Configuration

The server can be configured using environment variables:

### Model Settings

- `MOONDREAM_MODEL_NAME`: Model name (default: `vikhyatk/moondream2`)
- `MOONDREAM_MODEL_REVISION`: Model revision (default: `2025-01-09`)
- `MOONDREAM_TRUST_REMOTE_CODE`: Trust remote code (default: `true`)

### Device Settings

- `MOONDREAM_DEVICE`: Force specific device (`cpu`, `cuda`, `mps`, or `auto`)

### Image Processing

- `MOONDREAM_MAX_IMAGE_SIZE`: Maximum image dimensions (default: `2048x2048`)
- `MOONDREAM_MAX_FILE_SIZE_MB`: Maximum file size in MB (default: `50`)

### Performance

- `MOONDREAM_TIMEOUT_SECONDS`: Processing timeout (default: `120`)
- `MOONDREAM_MAX_CONCURRENT_REQUESTS`: Max concurrent requests (default: `5`)
- `MOONDREAM_ENABLE_STREAMING`: Enable streaming for captions (default: `true`)
- `MOONDREAM_MAX_BATCH_SIZE`: Maximum batch size for batch operations (default: `10`)
- `MOONDREAM_BATCH_CONCURRENCY`: Concurrent batch processing limit (default: `3`)
- `MOONDREAM_ENABLE_BATCH_PROGRESS`: Enable progress reporting for batch operations (default: `true`)

### Network (for URLs)

- `MOONDREAM_REQUEST_TIMEOUT_SECONDS`: HTTP request timeout (default: `30`)
- `MOONDREAM_MAX_REDIRECTS`: Maximum HTTP redirects (default: `5`)
- `MOONDREAM_USER_AGENT`: HTTP User-Agent header

## Available Tools

### 1. `caption_image`

Generate captions for images.

**Parameters:**
- `image_path` (string): Path to image file or URL
- `length` (string): Caption length - `"short"`, `"normal"`, or `"detailed"`
- `stream` (boolean): Whether to stream caption generation

**Example:**
```json
{
  "image_path": "https://example.com/image.jpg",
  "length": "detailed",
  "stream": false
}
```

### 2. `query_image`

Ask questions about images.

**Parameters:**
- `image_path` (string): Path to image file or URL
- `question` (string): Question to ask about the image

**Example:**
```json
{
  "image_path": "/path/to/image.jpg",
  "question": "How many people are in this image?"
}
```

### 3. `detect_objects`

Detect specific objects in images.

**Parameters:**
- `image_path` (string): Path to image file or URL
- `object_name` (string): Name of object to detect

**Example:**
```json
{
  "image_path": "https://example.com/photo.jpg",
  "object_name": "person"
}
```

### 4. `point_objects`

Get coordinates of objects in images.

**Parameters:**
- `image_path` (string): Path to image file or URL
- `object_name` (string): Name of object to locate

**Example:**
```json
{
  "image_path": "/path/to/image.jpg",
  "object_name": "car"
}
```

### 5. `analyze_image`

Multi-purpose image analysis tool.

**Parameters:**
- `image_path` (string): Path to image file or URL
- `operation` (string): Operation type (`"caption"`, `"query"`, `"detect"`, `"point"`)
- `parameters` (string): JSON string with operation-specific parameters

**Example:**
```json
{
  "image_path": "https://example.com/image.jpg",
  "operation": "query",
  "parameters": "{\"question\": \"What is the weather like?\"}"
}
```

### 6. `batch_analyze_images`

Process multiple images in batch.

**Parameters:**
- `image_paths` (string): JSON array of image paths
- `operation` (string): Operation to perform on all images
- `parameters` (string): JSON string with operation-specific parameters

**Example:**
```json
{
  "image_paths": "[\"image1.jpg\", \"image2.jpg\"]",
  "operation": "caption",
  "parameters": "{\"length\": \"short\"}"
}
```

## Usage Examples

### Basic Image Captioning

```python
# Using the caption_image tool
result = await caption_image(
    image_path="https://example.com/sunset.jpg",
    length="detailed"
)
```

### Visual Question Answering

```python
# Ask about image content
result = await query_image(
    image_path="/path/to/family_photo.jpg",
    question="How many children are in this photo?"
)
```

### Object Detection

```python
# Detect faces in an image
result = await detect_objects(
    image_path="https://example.com/group_photo.jpg",
    object_name="face"
)
```

### Batch Processing

```python
# Process multiple images
result = await batch_analyze_images(
    image_paths='["img1.jpg", "img2.jpg", "img3.jpg"]',
    operation="caption",
    parameters='{"length": "normal"}'
)
```

## Device Support

The server automatically detects and optimizes for available hardware:

### Apple Silicon (MPS)
- Optimal performance on M1/M2/M3 Macs
- Automatic memory management
- Native acceleration

### NVIDIA CUDA
- GPU acceleration for NVIDIA cards
- Automatic CUDA memory management
- Mixed precision support

### CPU Fallback
- Works on any system
- Optimized for multi-core processing
- Lower memory requirements

## Error Handling

The server provides detailed error information:

```json
{
  "success": false,
  "error_message": "Image file not found: /path/to/missing.jpg",
  "error_code": "IMAGE_PROCESSING_ERROR",
  "processing_time_ms": 15.2
}
```

Common error codes:
- `MODEL_LOAD_ERROR`: Issues loading the Moondream model
- `IMAGE_PROCESSING_ERROR`: Problems with image files or URLs
- `INFERENCE_ERROR`: Model inference failures
- `INVALID_REQUEST`: Invalid parameters or requests

## Performance Tips

1. **Use appropriate image sizes**: Resize large images before processing
2. **Batch processing**: Use `batch_analyze_images` for multiple images
3. **Device optimization**: Let the server auto-detect the best device
4. **Concurrent requests**: Adjust `MOONDREAM_MAX_CONCURRENT_REQUESTS` based on your hardware
5. **Memory management**: Monitor memory usage, especially with large images

## Troubleshooting

### Model Loading Issues

```bash
# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Check device availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, MPS: {torch.backends.mps.is_available()}')"
```

### Memory Issues

- Reduce `MOONDREAM_MAX_IMAGE_SIZE`
- Lower `MOONDREAM_MAX_CONCURRENT_REQUESTS`
- Use CPU instead of GPU for large images

### Network Issues

- Check firewall settings for URL access
- Increase `MOONDREAM_REQUEST_TIMEOUT_SECONDS`
- Verify SSL certificates for HTTPS URLs

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Moondream](https://github.com/vikhyat/moondream) - The amazing vision language model
- [FastMCP](https://github.com/jlowin/fastmcp) - The MCP server framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification

## Support

- 📖 [Documentation](https://github.com/ColeMurray/moondream-mcp#readme)
- 🐛 [Issue Tracker](https://github.com/ColeMurray/moondream-mcp/issues)
- 💬 [Discussions](https://github.com/ColeMurray/moondream-mcp/discussions)

---

**Note**: This server requires downloading the Moondream model on first use, which may take some time depending on your internet connection. 