"""
Moondream MCP Server.

FastMCP server for Moondream AI vision language model integration.
"""

import asyncio
import os
import signal
import sys
from typing import Optional

from fastmcp import FastMCP

from .config import Config
from .moondream import MoondreamClient
from .tools import register_vision_tools


def create_server() -> tuple[FastMCP, MoondreamClient]:
    """Create and configure the Moondream MCP server."""

    # Load configuration
    try:
        config = Config.from_env()
        print(f"✅ Configuration loaded: {config}", file=sys.stderr)
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate dependencies
    try:
        config.validate_dependencies()
        print("✅ Dependencies validated", file=sys.stderr)
    except ValueError as e:
        print(f"❌ Dependency error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create MCP server
    mcp: FastMCP = FastMCP(name="moondream-mcp", version="1.0.0")

    # Create Moondream client
    moondream_client = MoondreamClient(config)

    # Register tools with config
    register_vision_tools(mcp, moondream_client, config)

    print("✅ MCP server created with tools:")
    print("   • caption_image - Generate image captions")
    print("   • query_image - Visual question answering")
    print("   • detect_objects - Object detection with bounding boxes")
    print("   • point_objects - Object localization with coordinates")
    print("   • analyze_image - Multi-purpose image analysis")
    print("   • batch_analyze_images - Batch image processing")

    return mcp, moondream_client


async def run_server_async() -> None:
    """Run the server asynchronously with proper cleanup."""
    mcp, moondream_client = create_server()

    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    force_shutdown_count = 0

    def signal_handler(signum: int, frame: Optional[object]) -> None:
        nonlocal force_shutdown_count
        force_shutdown_count += 1

        if force_shutdown_count == 1:
            print(
                f"\n🛑 Received signal {signum}, shutting down gracefully...",
                file=sys.stderr,
            )
            shutdown_event.set()
        elif force_shutdown_count == 2:
            print("\n⚠️  Press Ctrl+C again to force shutdown", file=sys.stderr)
        else:
            print("\n💥 Force shutdown!", file=sys.stderr)
            os._exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Use the moondream client as an async context manager
        async with moondream_client:
            print("🚀 Starting Moondream MCP Server...", file=sys.stderr)
            print(
                f"📱 Device: {moondream_client.config.get_device_info()}",
                file=sys.stderr,
            )
            print("📡 Running MCP server with stdio transport", file=sys.stderr)

            # Create a task for the server
            server_task = asyncio.create_task(mcp.run_async(transport="stdio"))

            # Create a task for shutdown monitoring
            shutdown_task = asyncio.create_task(shutdown_event.wait())

            # Wait for either the server to complete or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
            )

            # If shutdown was triggered, cancel the server task
            if shutdown_task in done:
                print("🛑 Shutdown signal received, stopping server...", file=sys.stderr)
                server_task.cancel()
                try:
                    # Give the server task a chance to clean up
                    await asyncio.wait_for(server_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # Cancel any remaining pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if server task completed with an exception
            if server_task in done:
                try:
                    await server_task
                except Exception as e:
                    print(f"❌ Server error: {e}", file=sys.stderr)
                    raise

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        raise
    finally:
        print("🧹 Cleaning up resources...", file=sys.stderr)
        # Cleanup is handled by the async context manager
        print("✅ Shutdown complete", file=sys.stderr)


def main() -> None:
    """Main entry point for the server."""
    try:
        # Check Python version
        if sys.version_info < (3, 10):
            print("❌ Python 3.10 or higher is required", file=sys.stderr)
            sys.exit(1)

        # Run the async server
        asyncio.run(run_server_async())

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
