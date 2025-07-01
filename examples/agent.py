#!/usr/bin/env python3
"""
Moondream Vision OpenAI Agents SDK Agent
========================================
An interactive Python client that connects to the Moondream MCP server using OpenAI Agents SDK.
This agent provides a simple, intelligent interface for vision analysis tasks including image
captioning, visual question answering, object detection, and more through natural language.

Prerequisites
-------------
* Python ≥ 3.10
* `pip install -r requirements.txt`
* OpenAI API key for the agent
* Moondream MCP server running

Quick Start
-----------
1. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export MOONDREAM_DEVICE="auto"  # Optional: auto, cpu, cuda, mps
   ```

2. Run the agent:
   ```bash
   python agent.py
   ```

3. Interact with images:
   ```text
   moondream> What's in this image? /path/to/image.jpg
   moondream> Describe the scene in detail: https://example.com/image.png
   moondream> Find all the cars in /path/to/street.jpg
   moondream> Point to the dog in the image /path/to/pets.jpg
   moondream> quit
   ```

Environment Variables
--------------------
Required:
* OPENAI_API_KEY: OpenAI API key for the agent

Optional:
* MOONDREAM_DEVICE: Device for inference (auto/cpu/cuda/mps)
* MOONDREAM_MODEL_NAME: Hugging Face model name
* MOONDREAM_MAX_IMAGE_SIZE: Maximum image dimension
* MOONDREAM_TIMEOUT_SECONDS: Processing timeout

How It Works
------------
The agent uses OpenAI's Agents SDK to intelligently process natural language queries
about images and execute them against the Moondream MCP server. The agent automatically
determines the best vision analysis approach for each query.

Transport Options
-----------------
* Stdio (default): Direct process communication with MCP server
* HTTP: Connect to running HTTP MCP server

Examples:
```bash
# Stdio transport (default)
python agent.py

# HTTP transport
python agent.py --transport http --host 127.0.0.1 --port 8000
```
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# OpenAI Agents SDK imports
from agents.agent import Agent
from agents.run import Runner, trace
from agents.mcp import MCPServer, MCPServerStdio, MCPServerStreamableHttp
from agents.model_settings import ModelSettings

import dotenv

dotenv.load_dotenv()

console = Console()


def display_vision_result(content: str):
    """Display vision analysis results with proper formatting."""
    try:
        resp = json.loads(content)
    except json.JSONDecodeError:
        console.print(f"[yellow]› {content}[/yellow]")
        return
    
    if "error" in resp:
        error = resp["error"]
        console.print(f"[red]❌ Error: {error}[/red]")
        return
    
    # Handle different types of vision results
    if "caption" in resp:
        console.print(f"[green]📝 Caption:[/green] {resp['caption']}")
    
    if "answer" in resp:
        console.print(f"[blue]💬 Answer:[/blue] {resp['answer']}")
    
    if "objects" in resp:
        objects = resp["objects"]
        if objects:
            console.print(f"[cyan]🔍 Detected Objects:[/cyan]")
            table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
            table.add_column("Object", style="green")
            table.add_column("Confidence", style="yellow")
            table.add_column("Location", style="blue")
            
            for obj in objects:
                confidence = f"{obj.get('confidence', 0):.2f}" if 'confidence' in obj else "N/A"
                location = f"({obj.get('x', 0)}, {obj.get('y', 0)})" if 'x' in obj and 'y' in obj else "N/A"
                table.add_row(obj.get('name', 'Unknown'), confidence, location)
            
            console.print(table)
        else:
            console.print("[yellow]› No objects detected.[/yellow]")
    
    if "points" in resp:
        points = resp["points"]
        if points:
            console.print(f"[magenta]📍 Pointing Results:[/magenta]")
            table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
            table.add_column("Description", style="green")
            table.add_column("Coordinates", style="blue")
            table.add_column("Confidence", style="yellow")
            
            for point in points:
                coords = f"({point.get('x', 0)}, {point.get('y', 0)})"
                confidence = f"{point.get('confidence', 0):.2f}" if 'confidence' in point else "N/A"
                table.add_row(point.get('description', 'Point'), coords, confidence)
            
            console.print(table)
        else:
            console.print("[yellow]› No points found.[/yellow]")
    
    if "analysis" in resp:
        analysis = resp["analysis"]
        console.print(f"[purple]🔬 Analysis:[/purple]")
        console.print(Markdown(analysis))
    
    if "results" in resp:
        # Batch processing results
        results = resp["results"]
        console.print(f"[cyan]📊 Batch Results ({len(results)} images):[/cyan]")
        for i, result in enumerate(results, 1):
            console.print(f"[bold]Image {i}:[/bold]")
            display_vision_result(json.dumps(result))
            if i < len(results):
                console.print()
    
    # Display metadata if available
    if "processing_time" in resp:
        console.print(f"[dim]Processing time: {resp['processing_time']:.2f}s[/dim]")
    
    if "image_size" in resp:
        size = resp["image_size"]
        console.print(f"[dim]Image size: {size.get('width', 0)}x{size.get('height', 0)}[/dim]")


async def create_mcp_server(transport: str, host: str, port: int, server_command: str, server_args: str, timeout: int) -> MCPServer:
    """Create and return the appropriate MCP server based on transport type."""
    if transport == "http":
        url = f"http://{host}:{port}/mcp"
        console.print(f"[blue]Connecting to Moondream MCP server at {url}...[/blue]")
        return MCPServerStreamableHttp(
            name="Moondream MCP Server",
            params={
                "url": url,
                "timeout": float(timeout),  # Use the provided timeout
                "sse_read_timeout": float(timeout + 120),  # Add 2 minutes buffer for SSE
                "connect_timeout": 30.0
            },
            client_session_timeout_seconds=float(timeout)  # This controls MCP tool call timeout
        )
    else:
        console.print(f"[blue]Starting Moondream MCP server: {server_command} {server_args}[/blue]")
        return MCPServerStdio(
            name="Moondream MCP Server",
            params={
                "command": server_command,
                "args": server_args.split() if server_args else [],
            },
            client_session_timeout_seconds=float(timeout)  # This controls MCP tool call timeout
        )


def validate_image_path(image_path: str) -> bool:
    """Validate if the image path exists and is a valid image file."""
    if image_path.startswith(('http://', 'https://')):
        return True  # Assume URLs are valid, will be validated by the server
    
    path = Path(image_path)
    if not path.exists():
        console.print(f"[red]❌ File not found: {image_path}[/red]")
        return False
    
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    if path.suffix.lower() not in valid_extensions:
        console.print(f"[red]❌ Invalid image format: {path.suffix}[/red]")
        console.print(f"[yellow]Supported formats: {', '.join(valid_extensions)}[/yellow]")
        return False
    
    return True


async def run_interactive_session(mcp_server: MCPServer, timeout: int):
    """Run the interactive Moondream vision session using OpenAI Agents SDK."""
    
    # Create the agent with instructions for vision analysis
    agent = Agent(
        name="Moondream Vision Assistant",
        model="gpt-4o-mini",
        instructions="""You are a Moondream vision analysis assistant. Your role is to help users analyze images using various computer vision tools through natural language interaction.

AVAILABLE VISION TOOLS:
1. **caption_image**: Generate descriptive captions for images
   - Supports different caption lengths: short, normal, detailed
   - Use for: "Describe this image", "What's in this picture?", "Caption this image"

2. **query_image**: Answer specific questions about images
   - Use for: "What color is the car?", "How many people are in the image?", "Is there a dog?"

3. **detect_objects**: Find and locate specific objects in images
   - Use for: "Find all cars", "Detect people", "What objects are in this image?"

4. **point_objects**: Point to specific objects or regions in images
   - Use for: "Point to the dog", "Where is the red car?", "Show me the building"

5. **analyze_image**: Comprehensive analysis combining multiple operations
   - Use for: "Analyze this image completely", "Give me a full breakdown"

6. **batch_analyze_images**: Process multiple images at once (up to 10)
   - Use for: "Analyze these images", "Process this batch of photos"

INTERACTION PATTERNS:
- When user provides an image path/URL, determine the best tool based on their request
- For general questions like "What's in this image?", use caption_image with detailed length
- For specific questions, use query_image with the user's question
- For object detection requests, use detect_objects with the specified object type
- For pointing/location requests, use point_objects
- Always validate image paths before processing

INPUT HANDLING:
- Accept both local file paths and URLs
- Support common image formats: jpg, jpeg, png, gif, bmp, webp, tiff
- Handle batch processing for multiple images
- Provide helpful error messages for invalid inputs

RESPONSE FORMATTING:
- Present results in a clear, structured format
- Include relevant metadata (processing time, image dimensions)
- For object detection, show results in tables when appropriate
- For batch processing, organize results by image

EXAMPLE INTERACTIONS:
User: "What's in this image? /path/to/photo.jpg"
→ Use caption_image with detailed length

User: "How many cars are in the parking lot? https://example.com/parking.jpg"
→ Use query_image with the specific question

User: "Find all the people in /path/to/crowd.jpg"
→ Use detect_objects with object_type="person"

User: "Point to the red building in the cityscape.png"
→ Use point_objects with query="red building"

User: "Analyze this image completely: /path/to/scene.jpg"
→ Use analyze_image for comprehensive analysis

Available commands for users:
- Natural language requests with image paths/URLs
- "help" - show help information
- "examples" - show example commands
- "quit" or "exit" - exit the session

Always be helpful, provide clear responses, and explain what analysis you're performing.""",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(
            tool_choice="auto"
        ),
    )
    
    console.print(f"[bold green]✅ Connected to Moondream MCP server![/bold green]")
    
    # Show welcome message
    console.print(Panel.fit(
        f"[bold cyan]Moondream Vision OpenAI Agents SDK Agent[/bold cyan]\n"
        f"AI Model: [yellow]GPT-4o-mini[/yellow]\n"
        f"Vision Model: [yellow]Moondream2[/yellow]\n\n"
        f"Type [bold]help[/bold] for commands, [bold]examples[/bold] for examples, or [bold]quit[/bold] to exit.\n"
        f"Provide image paths or URLs with your vision requests!",
        border_style="cyan"
    ))
    
    # Interactive loop
    conversation_id = uuid.uuid4().hex[:16]
    input_items = []
    
    while True:
        try:
            user_input = Prompt.ask(f"[bold cyan]moondream>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not user_input.strip():
            continue

        # Handle basic commands
        if user_input.strip().lower() in {"quit", "exit"}:
            break
        elif user_input.strip().lower() == "help":
            console.print(Panel("""
[bold]Moondream Vision OpenAI Agents SDK Agent[/bold]

Ask questions about images in natural language - the AI agent will handle the analysis!

[bold]Vision Analysis Tools[/bold]
  [green]Image Captioning[/green] - Describe what's in an image
  [green]Visual Q&A[/green] - Answer specific questions about images  
  [green]Object Detection[/green] - Find and locate objects in images
  [green]Visual Pointing[/green] - Point to specific objects or regions
  [green]Comprehensive Analysis[/green] - Complete image analysis
  [green]Batch Processing[/green] - Analyze multiple images at once

[bold]Supported Formats[/bold]
  [cyan]Local files[/cyan]: /path/to/image.jpg, ./photo.png, ~/pictures/scene.gif
  [cyan]URLs[/cyan]: https://example.com/image.jpg, http://site.com/photo.png
  [cyan]Formats[/cyan]: JPG, PNG, GIF, BMP, WebP, TIFF

[bold]Commands[/bold]
  [cyan]help[/cyan]       – Show this help message
  [cyan]examples[/cyan]   – Show example commands
  [cyan]quit / exit[/cyan] – Leave the agent

[bold]How it works[/bold]
The AI agent automatically determines the best vision analysis approach based on your
natural language request and the image(s) you provide.
            """, title="Help", border_style="blue"))
            continue
        elif user_input.strip().lower() == "examples":
            console.print(Panel("""
[bold]Example Commands[/bold]

[bold cyan]Image Captioning[/bold cyan]
  [green]What's in this image? /path/to/photo.jpg[/green]
  [green]Describe this scene in detail: https://example.com/landscape.png[/green]
  [green]Caption this image: ./vacation_photo.jpg[/green]

[bold cyan]Visual Question Answering[/bold cyan]
  [green]How many people are in /path/to/crowd.jpg?[/green]
  [green]What color is the car in this image? ~/car.png[/green]
  [green]Is there a dog in https://example.com/pets.jpg?[/green]

[bold cyan]Object Detection[/bold cyan]
  [green]Find all the cars in /path/to/street.jpg[/green]
  [green]Detect people in this image: ./group_photo.png[/green]
  [green]What objects are in https://example.com/room.jpg?[/green]

[bold cyan]Visual Pointing[/bold cyan]
  [green]Point to the red building in /path/to/city.jpg[/green]
  [green]Where is the dog in this image? ./pets.png[/green]
  [green]Show me the tallest tree: https://example.com/forest.jpg[/green]

[bold cyan]Comprehensive Analysis[/bold cyan]
  [green]Analyze this image completely: /path/to/complex_scene.jpg[/green]
  [green]Give me a full breakdown of ./artwork.png[/green]

[bold cyan]Batch Processing[/bold cyan]
  [green]Analyze these images: /path/to/img1.jpg /path/to/img2.png[/green]
  [green]Process this batch: ./photo1.jpg ./photo2.jpg ./photo3.png[/green]
            """, title="Examples", border_style="green"))
            continue

        # Process the user input with the AI agent
        try:
            with trace("Vision Analysis", group_id=conversation_id):
                input_items.append({"content": user_input, "role": "user"})
                
                console.print("[green]🤖 Processing with AI vision agent...[/green]")
                console.print("[dim]Note: First-time model loading may take 30-60 seconds[/dim]")
                
                # Add timeout wrapper for the runner
                try:
                    result = await asyncio.wait_for(
                        Runner.run(agent, input_items),
                        timeout=timeout  # Use the provided timeout
                    )
                except asyncio.TimeoutError:
                    console.print(f"[red]❌ Processing timed out after {timeout} seconds[/red]")
                    console.print("[yellow]This may happen on first run when loading the model.[/yellow]")
                    console.print("[yellow]Please try again - subsequent runs should be faster.[/yellow]")
                    console.print(f"[dim]You can increase the timeout with --timeout {timeout * 2}[/dim]")
                    continue
                
                # Display the agent's response
                if result.final_output:
                    # Check if the output looks like JSON (tool result)
                    if result.final_output.strip().startswith('{'):
                        display_vision_result(result.final_output)
                    else:
                        console.print(f"[blue]🤖 Agent:[/blue] {result.final_output}")
                else:
                    console.print("[yellow]› No response from agent.[/yellow]")
                
                # Update input items for next iteration
                input_items = result.to_input_list()
                
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                console.print(f"[red]❌ Timeout Error:[/red] {e}")
                console.print("[yellow]Vision processing can take time, especially on first run.[/yellow]")
                console.print("[yellow]Try again - the model should be loaded and faster now.[/yellow]")
            else:
                console.print(f"[red]❌ Error:[/red] {e}")
            # Continue the conversation even if there's an error


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--transport", default="stdio", type=click.Choice(["stdio", "http"]),
              help="Transport type to use (stdio or http)")
@click.option("--host", default="127.0.0.1", 
              help="Host for HTTP transport")
@click.option("--port", default=8000, type=int,
              help="Port for HTTP transport")
@click.option("--server-command", default="moondream-mcp",
              help="Command to run the MCP server (for stdio transport)")
@click.option("--server-args", default="",
              help="Arguments for the server command (for stdio transport)")
@click.option("--timeout", default=180, type=int,
              help="Processing timeout in seconds (default: 180)")
def main(transport: str, host: str, port: int, server_command: str, server_args: str, timeout: int):
    """Start an interactive Moondream vision CLI powered by OpenAI Agents SDK."""
    asyncio.run(async_main(transport, host, port, server_command, server_args, timeout))


async def async_main(transport: str, host: str, port: int, server_command: str, server_args: str, timeout: int):
    """Async main function."""
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]❌ Error: OPENAI_API_KEY environment variable is required[/red]")
        console.print("[yellow]Please set your OpenAI API key: export OPENAI_API_KEY='your-key'[/yellow]")
        return
    
    # Create MCP server
    mcp_server = await create_mcp_server(transport, host, port, server_command, server_args, timeout)
    
    # For HTTP transport, we might need to start the server process
    process = None
    if transport == "http":
        # Check if we need to start the server (for demo purposes)
        try:
            import requests
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
        except:
            # Server not running, try to start it
            console.print(f"[yellow]Starting HTTP server at {host}:{port}...[/yellow]")
            try:
                process = subprocess.Popen([server_command] + server_args.split())
                time.sleep(3)  # Give it time to start
            except Exception as e:
                console.print(f"[red]❌ Failed to start server: {e}[/red]")
                return
    
    try:
        # Run the interactive session
        async with mcp_server:
            await run_interactive_session(mcp_server, timeout)
    except Exception as e:
        console.print(f"[red]❌ Connection error:[/red] {e}")
        console.print("[yellow]Make sure the MCP server is running and environment variables are set.[/yellow]")
    finally:
        if process:
            process.terminate()
        console.print("[bold]Goodbye! 👋[/bold]")


if __name__ == "__main__":
    main() 