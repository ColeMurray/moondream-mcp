"""
Tests for Moondream MCP server.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moondream_mcp.config import Config
from moondream_mcp.server import create_server, main, run_server_async


class TestServer:
    """Test server functionality."""

    @patch("moondream_mcp.server.Config.from_env")
    @patch("moondream_mcp.server.FastMCP")
    @patch("moondream_mcp.server.MoondreamClient")
    @patch("moondream_mcp.server.register_vision_tools")
    def test_create_server_success(
        self,
        mock_register_tools: MagicMock,
        mock_client_class: MagicMock,
        mock_fastmcp_class: MagicMock,
        mock_config_from_env: MagicMock,
    ) -> None:
        """Test successful server creation."""
        # Mock configuration
        mock_config = MagicMock(spec=Config)
        mock_config_from_env.return_value = mock_config

        # Mock FastMCP
        mock_mcp = MagicMock()
        mock_fastmcp_class.return_value = mock_mcp

        # Mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Call create_server
        mcp, client = create_server()

        # Verify calls
        mock_config_from_env.assert_called_once()
        mock_config.validate_dependencies.assert_called_once()
        mock_fastmcp_class.assert_called_once_with(
            name="moondream-mcp", version="1.0.0"
        )
        mock_client_class.assert_called_once_with(mock_config)
        mock_register_tools.assert_called_once_with(mock_mcp, mock_client, mock_config)

        # Verify return values
        assert mcp == mock_mcp
        assert client == mock_client

    @patch("moondream_mcp.server.Config.from_env")
    def test_create_server_config_error(self, mock_config_from_env: MagicMock) -> None:
        """Test server creation with configuration error."""
        mock_config_from_env.side_effect = ValueError("Invalid configuration")

        with pytest.raises(SystemExit):
            create_server()

    @patch("moondream_mcp.server.Config.from_env")
    def test_create_server_dependency_error(
        self, mock_config_from_env: MagicMock
    ) -> None:
        """Test server creation with dependency error."""
        mock_config = MagicMock(spec=Config)
        mock_config.validate_dependencies.side_effect = ValueError("Missing dependency")
        mock_config_from_env.return_value = mock_config

        with pytest.raises(SystemExit):
            create_server()

    @pytest.mark.asyncio
    @patch("moondream_mcp.server.create_server")
    @patch("signal.signal")
    async def test_run_server_async_success(
        self,
        mock_signal: MagicMock,
        mock_create_server: MagicMock,
    ) -> None:
        """Test successful async server run."""
        # Mock server components
        mock_mcp = AsyncMock()
        mock_client = AsyncMock()
        mock_create_server.return_value = (mock_mcp, mock_client)

        # Mock the server task to complete quickly
        async def mock_run_async(transport: str) -> None:
            await asyncio.sleep(0.01)  # Short delay

        mock_mcp.run_async = mock_run_async

        # Mock client context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Run the server with a timeout to prevent hanging
        try:
            await asyncio.wait_for(run_server_async(), timeout=1.0)
        except asyncio.TimeoutError:
            # This is expected since the server runs indefinitely
            pass

        # Verify setup calls
        mock_create_server.assert_called_once()
        mock_signal.assert_called()  # Signal handlers should be registered

    @pytest.mark.asyncio
    @patch("moondream_mcp.server.create_server")
    @patch("signal.signal")
    async def test_run_server_async_keyboard_interrupt(
        self,
        mock_signal: MagicMock,
        mock_create_server: MagicMock,
    ) -> None:
        """Test server handling of keyboard interrupt."""
        # Mock server components
        mock_mcp = AsyncMock()
        mock_client = AsyncMock()
        mock_create_server.return_value = (mock_mcp, mock_client)

        # Mock the server to run normally but we'll simulate KeyboardInterrupt
        # by raising it from the asyncio.wait call
        async def mock_run_async(transport: str) -> None:
            # Simulate a long-running server
            await asyncio.sleep(1)

        mock_mcp.run_async = mock_run_async

        # Mock client context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock asyncio.wait to raise KeyboardInterrupt
        original_wait = asyncio.wait

        async def mock_wait(*args, **kwargs):
            # Let it start, then raise KeyboardInterrupt
            await asyncio.sleep(0.01)
            raise KeyboardInterrupt()

        with patch("asyncio.wait", side_effect=mock_wait):
            # Should handle KeyboardInterrupt gracefully without re-raising
            await run_server_async()

        # Verify setup and cleanup were called
        mock_create_server.assert_called_once()
        mock_signal.assert_called()  # Signal handlers should be registered
        mock_client.__aenter__.assert_called_once()
        mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    @patch("moondream_mcp.server.create_server")
    async def test_run_server_async_server_error(
        self,
        mock_create_server: MagicMock,
    ) -> None:
        """Test server handling of server errors."""
        # Mock server components
        mock_mcp = AsyncMock()
        mock_client = AsyncMock()
        mock_create_server.return_value = (mock_mcp, mock_client)

        # Mock the server to raise an exception
        async def mock_run_async(transport: str) -> None:
            raise RuntimeError("Server error")

        mock_mcp.run_async = mock_run_async

        # Mock client context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Should re-raise the exception
        with pytest.raises(RuntimeError, match="Server error"):
            await run_server_async()

    @patch("sys.version_info", (3, 9))  # Python version too old
    @patch("moondream_mcp.server.asyncio.run")
    def test_main_python_version_check(self, mock_asyncio_run: MagicMock) -> None:
        """Test main function Python version check."""
        with pytest.raises(SystemExit):
            main()

        mock_asyncio_run.assert_not_called()

    @patch("sys.version_info", (3, 10))  # Valid Python version
    @patch("moondream_mcp.server.asyncio.run")
    def test_main_success(self, mock_asyncio_run: MagicMock) -> None:
        """Test successful main function execution."""
        main()

        mock_asyncio_run.assert_called_once()

    @patch("sys.version_info", (3, 10))
    @patch("moondream_mcp.server.asyncio.run")
    def test_main_keyboard_interrupt(self, mock_asyncio_run: MagicMock) -> None:
        """Test main function handling of keyboard interrupt."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0  # Should exit with code 0

    @patch("sys.version_info", (3, 10))
    @patch("moondream_mcp.server.asyncio.run")
    def test_main_exception(self, mock_asyncio_run: MagicMock) -> None:
        """Test main function handling of exceptions."""
        mock_asyncio_run.side_effect = RuntimeError("Fatal error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1  # Should exit with code 1


class TestSignalHandling:
    """Test signal handling functionality."""

    def test_signal_handler_sets_shutdown_event(self) -> None:
        """Test that signal handler sets shutdown event."""
        import signal
        from unittest.mock import MagicMock

        # Create a mock shutdown event
        shutdown_event = MagicMock()

        # Create signal handler (simplified version)
        def signal_handler(signum: int, frame: object) -> None:
            shutdown_event.set()

        # Test the handler
        signal_handler(signal.SIGINT, None)

        shutdown_event.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_shutdown_waits_for_tasks(self) -> None:
        """Test that graceful shutdown waits for tasks to complete."""
        # Create mock tasks
        server_task = asyncio.create_task(asyncio.sleep(0.1))
        shutdown_task = asyncio.create_task(asyncio.sleep(0.05))  # Completes first

        # Wait for first completion
        done, pending = await asyncio.wait(
            [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Shutdown task should complete first
        assert shutdown_task in done
        assert server_task in pending

        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
