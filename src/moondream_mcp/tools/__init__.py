"""
Tools package for Moondream MCP Server.

Contains modular tool registration functions for vision analysis capabilities.
"""

from .vision import register_vision_tools

__all__ = ["register_vision_tools"]
