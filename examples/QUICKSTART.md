# Quick Start Guide - Moondream OpenAI Agent

Get up and running with the Moondream vision analysis agent in 5 minutes!

## ✅ Prerequisites Check

Run the test script to verify everything is set up correctly:

```bash
cd examples
python test_agent.py
```

You should see: `🎉 All tests passed! The agent should work correctly.`

## 🚀 Start the Agent

```bash
python agent.py
```

For slower systems or first-time use, you may want to increase the timeout:

```bash
# Increase timeout to 5 minutes for first run
python agent.py --timeout 300
```

## 💬 Example Conversation

Once the agent starts, you can interact with it naturally:

```
moondream> help
# Shows available commands and features

moondream> examples  
# Shows example commands you can try

moondream> What's in this image? /path/to/your/image.jpg
# Analyzes and describes the image

moondream> How many people are in /path/to/group_photo.jpg?
# Answers specific questions about images

moondream> Find all the cars in /path/to/street_scene.jpg
# Detects and locates specific objects

moondream> quit
# Exits the agent
```

## 🔧 Configuration

The agent uses these environment variables (already set in your `.env` file):

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `MOONDREAM_DEVICE` - Device for inference (auto/cpu/cuda/mps)
- `MOONDREAM_MAX_IMAGE_SIZE` - Maximum image size (default: 2048)

## 📁 Supported Image Formats

- **Local files**: `./image.jpg`, `/full/path/to/image.png`, `~/Pictures/photo.gif`
- **URLs**: `https://example.com/image.jpg`
- **Formats**: JPG, PNG, GIF, BMP, WebP, TIFF

## 🎯 What the Agent Can Do

1. **Image Captioning** - "Describe this image"
2. **Visual Q&A** - "How many cars are in this image?"
3. **Object Detection** - "Find all the people in this photo"
4. **Visual Pointing** - "Point to the red car"
5. **Comprehensive Analysis** - "Analyze this image completely"
6. **Batch Processing** - "Analyze these images: img1.jpg img2.jpg"

## 🚨 Troubleshooting

If you encounter issues:

1. **Check the test**: `python test_agent.py`
2. **Verify .env file**: Make sure `OPENAI_API_KEY` is set
3. **Check image paths**: Ensure images exist and are in supported formats
4. **First run**: Model loading takes 30-60 seconds on first use

### Common Error Messages

- **"cannot load library 'libvips.42.dylib'" (macOS) or "No module named 'pyvips'"**: Install the system library with `brew install vips`
- **"OPENAI_API_KEY environment variable is required"**: Set your API key in `.env`
- **"Connection error"**: Ensure the MCP server is running
- **"File not found"**: Check image paths are correct and files exist
- **"Processing timed out"**: Increase timeout with `python agent.py --timeout 300` (5 minutes)

### macOS Setup

On macOS, you need both the Python package and the system library:

```bash
# Install the system library
brew install vips

# Install the Python package (should already be installed)
pip install pyvips
```

## 🎉 You're Ready!

The agent intelligently determines which vision analysis tool to use based on your natural language requests. Just describe what you want to do with your images, and the AI will handle the rest!

For more detailed information, see the full [README.md](README.md). 