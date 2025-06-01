#!/usr/bin/env python3
"""
Setup script for Claude Desktop integration with Moondream MCP.

This script helps users configure Claude Desktop to use the Moondream MCP server.
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def get_claude_desktop_config_path() -> Path:
    """
    Get the Claude Desktop configuration file path for the current platform.

    Returns:
        Path to Claude Desktop config file

    Raises:
        RuntimeError: If platform is not supported
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    elif system == "Windows":
        return (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Claude"
            / "claude_desktop_config.json"
        )
    elif system == "Linux":
        # Try XDG config directory first, fallback to .config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "Claude" / "claude_desktop_config.json"
        else:
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def find_moondream_mcp_executable() -> Optional[str]:
    """
    Find the moondream-mcp executable in the current environment.

    Returns:
        Path to executable or None if not found
    """
    # Check if it's in PATH
    executable = shutil.which("moondream-mcp")
    if executable:
        return executable

    # Check if we're in a virtual environment
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        if platform.system() == "Windows":
            venv_executable = Path(venv_path) / "Scripts" / "moondream-mcp.exe"
        else:
            venv_executable = Path(venv_path) / "bin" / "moondream-mcp"

        if venv_executable.exists():
            return str(venv_executable)

    # Check current Python environment
    try:
        import moondream_mcp

        python_executable = sys.executable
        return f"{python_executable} -m moondream_mcp.server"
    except ImportError:
        pass

    return None


def create_moondream_mcp_config(
    executable_path: str, environment_vars: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create MCP server configuration for Moondream.

    Args:
        executable_path: Path to moondream-mcp executable
        environment_vars: Optional environment variables

    Returns:
        MCP server configuration dictionary
    """
    env_dict: Dict[str, str] = environment_vars or {}
    config = {"command": executable_path, "args": [], "env": env_dict}

    # Add default environment variables if not specified
    if "MOONDREAM_DEVICE" not in env_dict:
        # Auto-detect best device
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            env_dict["MOONDREAM_DEVICE"] = "mps"  # Apple Silicon
        else:
            env_dict["MOONDREAM_DEVICE"] = "auto"

    return config


def load_existing_config(config_path: Path) -> Dict[str, Any]:
    """
    Load existing Claude Desktop configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Existing configuration or empty dict
    """
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                result = json.load(f)
                if isinstance(result, dict):
                    return result
                else:
                    print("Warning: Config file does not contain a JSON object")
                    return {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read existing config: {e}")
            return {}
    return {}


def save_config(config_path: Path, config: Dict[str, Any]) -> None:
    """
    Save configuration to Claude Desktop config file.

    Args:
        config_path: Path to configuration file
        config: Configuration to save
    """
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Create backup if file exists
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        shutil.copy2(config_path, backup_path)
        print(f"Created backup: {backup_path}")

    # Save new configuration
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Configuration saved to: {config_path}")


def setup_claude_desktop(
    force: bool = False, environment_vars: Optional[Dict[str, str]] = None
) -> bool:
    """
    Set up Claude Desktop integration for Moondream MCP.

    Args:
        force: Whether to overwrite existing configuration
        environment_vars: Optional environment variables

    Returns:
        True if setup was successful
    """
    try:
        # Find configuration path
        config_path = get_claude_desktop_config_path()
        print(f"Claude Desktop config path: {config_path}")

        # Find executable
        executable = find_moondream_mcp_executable()
        if not executable:
            print("Error: Could not find moondream-mcp executable.")
            print("Please ensure moondream-mcp is installed and in your PATH.")
            print("Try: pip install moondream-mcp")
            return False

        print(f"Found moondream-mcp: {executable}")

        # Load existing configuration
        config = load_existing_config(config_path)

        # Initialize mcpServers if it doesn't exist
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Check if moondream-mcp is already configured
        if "moondream-mcp" in config["mcpServers"] and not force:
            print("Moondream MCP is already configured in Claude Desktop.")
            print("Use --force to overwrite existing configuration.")
            return True

        # Create Moondream MCP configuration
        mcp_config = create_moondream_mcp_config(executable, environment_vars)
        config["mcpServers"]["moondream-mcp"] = mcp_config

        # Save configuration
        save_config(config_path, config)

        print("\n✅ Claude Desktop integration setup complete!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop if it's running")
        print("2. The Moondream MCP tools should now be available in Claude")
        print("3. Try asking Claude to analyze an image!")

        return True

    except Exception as e:
        print(f"Error setting up Claude Desktop integration: {e}")
        return False


def main() -> None:
    """Main entry point for the setup script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Set up Claude Desktop integration for Moondream MCP"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration"
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use for inference",
    )
    parser.add_argument(
        "--max-image-size", type=int, help="Maximum image size (pixels)"
    )
    parser.add_argument("--timeout", type=int, help="Processing timeout (seconds)")

    args = parser.parse_args()

    # Build environment variables
    env_vars = {}
    if args.device:
        env_vars["MOONDREAM_DEVICE"] = args.device
    if args.max_image_size:
        env_vars["MOONDREAM_MAX_IMAGE_SIZE"] = str(args.max_image_size)
    if args.timeout:
        env_vars["MOONDREAM_TIMEOUT_SECONDS"] = str(args.timeout)

    # Run setup
    success = setup_claude_desktop(
        force=args.force, environment_vars=env_vars if env_vars else None
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
