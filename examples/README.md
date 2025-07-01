# Moondream MCP Examples

This directory contains example clients and usage demonstrations for the Moondream MCP server.

## OpenAI Agents SDK Agent

The `agent.py` file provides an interactive OpenAI Agents SDK client that connects to the Moondream MCP server for intelligent vision analysis.

### Features

- **Natural Language Interface**: Ask questions about images in plain English
- **Intelligent Tool Selection**: AI automatically chooses the best vision analysis tool
- **Rich Output Formatting**: Beautiful tables, markdown, and structured results
- **Multiple Transport Options**: Stdio (default) or HTTP connection
- **Comprehensive Vision Analysis**: All Moondream tools available through natural language

### Prerequisites

1. **Python 3.10+**
2. **OpenAI API Key** - Required for the AI agent
3. **Moondream MCP Server** - Either installed or running

### Installation

1. Install the agent dependencies:
   ```bash
   cd examples
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

3. (Optional) Configure Moondream settings:
   ```bash
   export MOONDREAM_DEVICE="auto"  # auto, cpu, cuda, mps
   export MOONDREAM_MAX_IMAGE_SIZE="2048"
   export MOONDREAM_TIMEOUT_SECONDS="30"
   ```

### Usage

#### Basic Usage (Stdio Transport)

Start the agent with the default stdio transport:

```bash
python agent.py
```

This will automatically start the Moondream MCP server as a subprocess and connect to it.

#### HTTP Transport

If you have a Moondream MCP server running on HTTP:

```bash
# Start the MCP server separately
moondream-mcp --transport http --port 8000

# Connect the agent to the HTTP server
python agent.py --transport http --host 127.0.0.1 --port 8000
```

### Example Interactions

Once the agent is running, you can interact with it using natural language:

#### Image Captioning
```
moondream> What's in this image? /path/to/photo.jpg
moondream> Describe this scene in detail: https://example.com/landscape.png
moondream> Caption this image: ./vacation_photo.jpg
```

#### Visual Question Answering
```
moondream> How many people are in /path/to/crowd.jpg?
moondream> What color is the car in this image? ~/car.png
moondream> Is there a dog in https://example.com/pets.jpg?
```

#### Object Detection
```
moondream> Find all the cars in /path/to/street.jpg
moondream> Detect people in this image: ./group_photo.png
moondream> What objects are in https://example.com/room.jpg?
```

#### Visual Pointing
```
moondream> Point to the red building in /path/to/city.jpg
moondream> Where is the dog in this image? ./pets.png
moondream> Show me the tallest tree: https://example.com/forest.jpg
```

#### Comprehensive Analysis
```
moondream> Analyze this image completely: /path/to/complex_scene.jpg
moondream> Give me a full breakdown of ./artwork.png
```

#### Batch Processing
```
moondream> Analyze these images: /path/to/img1.jpg /path/to/img2.png
moondream> Process this batch: ./photo1.jpg ./photo2.jpg ./photo3.png
```

### Commands

- `help` - Show help information
- `examples` - Show example commands
- `quit` or `exit` - Exit the agent

### Supported Image Formats

- **Local Files**: `/path/to/image.jpg`, `./photo.png`, `~/pictures/scene.gif`
- **URLs**: `https://example.com/image.jpg`, `http://site.com/photo.png`
- **Formats**: JPG, JPEG, PNG, GIF, BMP, WebP, TIFF

### How It Works

1. **Natural Language Processing**: The OpenAI agent (GPT-4o-mini) processes your natural language request
2. **Tool Selection**: The AI automatically determines which Moondream vision tool to use
3. **MCP Communication**: The agent calls the appropriate MCP tool through the server connection
4. **Result Formatting**: Results are formatted and displayed with rich console output

### Configuration Options

The agent supports various command-line options:

```bash
python agent.py --help
```

Options:
- `--transport`: Transport type (stdio or http)
- `--host`: Host for HTTP transport
- `--port`: Port for HTTP transport  
- `--server-command`: Command to run MCP server (for stdio)
- `--server-args`: Arguments for server command
- `--timeout`: Processing timeout in seconds (default: 180)

### Timeout Configuration

Vision processing can take time, especially on first run when loading the model. You can configure timeouts:

```bash
# Use default 3-minute timeout
python agent.py

# Increase timeout to 5 minutes for slower systems
python agent.py --timeout 300

# Shorter timeout for faster systems
python agent.py --timeout 120
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *Required* | OpenAI API key for the agent |
| `MOONDREAM_DEVICE` | `auto` | Device for inference |
| `MOONDREAM_MODEL_NAME` | `vikhyatk/moondream2` | Hugging Face model |
| `MOONDREAM_MAX_IMAGE_SIZE` | `2048` | Maximum image dimension |
| `MOONDREAM_TIMEOUT_SECONDS` | `30` | Processing timeout |

### Troubleshooting

#### Common Issues

1. **"OPENAI_API_KEY environment variable is required"**
   - Set your OpenAI API key: `export OPENAI_API_KEY="your-key"`

2. **"cannot load library 'libvips.42.dylib'" (macOS) or "No module named 'pyvips'"**
   - Install the system library: `brew install vips`
   - The Python package `pyvips` is automatically installed, but requires the system `vips` library

3. **"Connection error"**
   - Ensure the MCP server is running
   - Check that all dependencies are installed
   - Verify environment variables are set

4. **"File not found" or "Invalid image format"**
   - Check that image paths are correct
   - Ensure image format is supported
   - For URLs, verify they're accessible

5. **Slow processing**
   - First model load can take 30-60 seconds
   - Large images may take longer to process
   - Consider using smaller images or adjusting `MOONDREAM_MAX_IMAGE_SIZE`

6. **Timeout errors**
   - Increase the timeout: `python agent.py --timeout 300` (5 minutes)
   - First run takes longer due to model loading
   - Subsequent runs should be much faster

#### Debug Mode

For debugging, you can run with verbose output:

```bash
python agent.py --transport stdio --server-args "--log-level DEBUG"
```

### Performance Tips

1. **Image Size**: Resize large images to 2048px or smaller for faster processing
2. **Batch Processing**: Use batch analysis for multiple images to improve efficiency
3. **Device Selection**: Use GPU (`cuda` or `mps`) for faster inference if available
4. **Persistent Server**: For multiple sessions, run the MCP server separately via HTTP

### Example Session

```
$ python agent.py
🔵 Starting Moondream MCP server: moondream-mcp 
✅ Connected to Moondream MCP server!

┌─────────────────────────────────────────────────────────────┐
│                Moondream Vision OpenAI Agents SDK Agent     │
│ AI Model: GPT-4o-mini                                       │
│ Vision Model: Moondream2                                     │
│                                                             │
│ Type help for commands, examples for examples, or quit to   │
│ exit.                                                       │
│ Provide image paths or URLs with your vision requests!      │
└─────────────────────────────────────────────────────────────┘

moondream> What's in this image? ./examples/sample_images/street.jpg
🤖 Processing with AI vision agent...
📝 Caption: A busy city street with cars, pedestrians, and tall buildings lining both sides of the road.
Processing time: 2.34s
Image size: 1920x1080

moondream> How many cars can you see in that image?
🤖 Processing with AI vision agent...
💬 Answer: I can see approximately 8-10 cars in the street scene, including sedans and SUVs parked and driving along the road.
Processing time: 1.87s

moondream> quit
Goodbye! 👋
```

This example demonstrates the natural conversation flow and intelligent tool selection that makes the agent easy and intuitive to use. 