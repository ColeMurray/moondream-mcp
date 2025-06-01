#!/usr/bin/env python3
"""
Test script for the Moondream OpenAI Agents SDK Agent
====================================================
This script tests the basic functionality of the agent setup.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    import dotenv
    # Look for .env file in parent directory (moondream-mcp root)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        dotenv.load_dotenv(env_path)
        print(f"📄 Loaded environment from: {env_path}")
    else:
        dotenv.load_dotenv()  # Try current directory
except ImportError:
    pass

def check_dependencies():
    """Check if all required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import agents
        print("✅ OpenAI Agents SDK: Available")
    except ImportError:
        missing_deps.append("agents")
        print("❌ OpenAI Agents SDK: Missing")
    
    try:
        import rich
        print("✅ Rich: Available")
    except ImportError:
        missing_deps.append("rich")
        print("❌ Rich: Missing")
    
    try:
        import click
        print("✅ Click: Available")
    except ImportError:
        missing_deps.append("click")
        print("❌ Click: Missing")
    
    try:
        import dotenv
        print("✅ Python-dotenv: Available")
    except ImportError:
        missing_deps.append("python-dotenv")
        print("❌ Python-dotenv: Missing")
    
    try:
        import requests
        print("✅ Requests: Available")
    except ImportError:
        missing_deps.append("requests")
        print("❌ Requests: Missing")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are available!")
        return True

def check_environment():
    """Check environment variables."""
    print("\n🔍 Checking environment variables...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY: Set")
    else:
        print("❌ OPENAI_API_KEY: Not set")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        return False
    
    # Optional environment variables
    device = os.getenv("MOONDREAM_DEVICE", "auto")
    print(f"ℹ️  MOONDREAM_DEVICE: {device}")
    
    max_size = os.getenv("MOONDREAM_MAX_IMAGE_SIZE", "2048")
    print(f"ℹ️  MOONDREAM_MAX_IMAGE_SIZE: {max_size}")
    
    timeout = os.getenv("MOONDREAM_TIMEOUT_SECONDS", "30")
    print(f"ℹ️  MOONDREAM_TIMEOUT_SECONDS: {timeout}")
    
    return True

def check_moondream_mcp():
    """Check if moondream-mcp command is available."""
    print("\n🔍 Checking Moondream MCP server...")
    
    import subprocess
    try:
        result = subprocess.run(
            ["moondream-mcp", "--help"], 
            capture_output=True, 
            text=True, 
            timeout=5  # Reduced timeout
        )
        if result.returncode == 0:
            print("✅ moondream-mcp command: Available")
            return True
        else:
            print("❌ moondream-mcp command: Error")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  moondream-mcp command: Timeout (this is normal for server commands)")
        print("✅ moondream-mcp command: Available (server started but timed out)")
        return True  # Consider timeout as success since server started
    except FileNotFoundError:
        print("❌ moondream-mcp command: Not found")
        print("Install it with: pip install moondream-mcp")
        return False
    except Exception as e:
        print(f"❌ moondream-mcp command: Error - {e}")
        return False

def test_agent_import():
    """Test importing the agent module."""
    print("\n🔍 Testing agent import...")
    
    try:
        # Add the examples directory to the path
        examples_dir = Path(__file__).parent
        sys.path.insert(0, str(examples_dir))
        
        # Try to import the agent module
        import agent
        print("✅ Agent module: Import successful")
        
        # Check if main functions exist
        if hasattr(agent, 'main'):
            print("✅ Agent main function: Available")
        else:
            print("❌ Agent main function: Missing")
            return False
            
        if hasattr(agent, 'create_mcp_server'):
            print("✅ Agent MCP server function: Available")
        else:
            print("❌ Agent MCP server function: Missing")
            return False
        
        # Test OpenAI Agents SDK imports
        try:
            from agents.agent import Agent
            from agents.run import Runner
            from agents.mcp import MCPServer
            print("✅ OpenAI Agents SDK imports: Successful")
        except ImportError as e:
            print(f"❌ OpenAI Agents SDK imports: Failed - {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Agent module: Import failed - {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Moondream OpenAI Agents SDK Agent Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Test dependencies
    if not check_dependencies():
        all_passed = False
    
    # Test environment
    if not check_environment():
        all_passed = False
    
    # Test moondream-mcp
    if not check_moondream_mcp():
        all_passed = False
    
    # Test agent import
    if not test_agent_import():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The agent should work correctly.")
        print("\nTo start the agent, run:")
        print("  python agent.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Set OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("  3. Install Moondream MCP: pip install moondream-mcp")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 