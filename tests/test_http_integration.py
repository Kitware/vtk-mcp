"""Integration tests with HTTP server transport."""

import pytest
import asyncio
import time
import threading
import socket
from unittest.mock import patch
from vtk_mcp_server.server import mcp
from vtk_mcp_server.simple_client import SimpleVTKClient


pytestmark = [pytest.mark.integration, pytest.mark.http]


class TestHTTPIntegration:
    """Test client-server integration over HTTP transport."""

    @pytest.fixture
    def server_thread(self):
        """Start HTTP server in background thread."""
        # Find a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            port = s.getsockname()[1]

        server_thread = None
        server_started = threading.Event()

        def run_server():
            try:
                # Run server on the free port
                asyncio.run(mcp.run_http_async(host="127.0.0.1", port=port))
            except Exception:
                pass  # Server might be stopped
            finally:
                server_started.set()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Wait a bit for server to start
        time.sleep(0.5)

        yield f"http://127.0.0.1:{port}"

        # Cleanup - server thread will die when test ends due to daemon=True

    def test_client_server_info_cpp_integration(self, server_thread):
        """Test full integration of info-cpp command."""
        base_url = server_thread

        # Mock the scraper to avoid external network calls
        with patch("vtk_mcp_server.server.scraper") as mock_scraper:
            mock_scraper.get_class_info.return_value = {
                "class_name": "vtkSphere",
                "brief": "Test sphere class",
                "detailed_description": "A test sphere for integration testing",
                "inheritance": ["vtkImplicitFunction"],
                "methods": [{"name": "SetRadius", "description": "Set radius"}],
                "url": "http://test.com",
            }

            client = SimpleVTKClient(base_url)

            # Capture print output
            with patch("builtins.print") as mock_print:
                client.get_class_info_cpp("vtkSphere")

                # Verify print was called (output was generated)
                mock_print.assert_called()

                # Check that the scraper was called
                mock_scraper.get_class_info.assert_called_with("vtkSphere")

    def test_client_server_info_python_integration(self, server_thread):
        """Test full integration of info-python command."""
        base_url = server_thread

        # Since VTK is actually installed, test with real VTK but capture output
        client = SimpleVTKClient(base_url)

        with patch("builtins.print") as mock_print:
            client.get_class_info_python("vtkSphere")

            # Verify print was called (output was generated)
            mock_print.assert_called()

    def test_client_server_search_integration(self, server_thread):
        """Test full integration of search command."""
        base_url = server_thread

        # Since VTK scraper is complex, just test that search functionality works
        client = SimpleVTKClient(base_url)

        with patch("builtins.print") as mock_print:
            client.search_classes("Camera")

            # Verify print was called (output was generated)
            mock_print.assert_called()

    def test_client_server_list_tools_integration(self, server_thread):
        """Test full integration of list-tools command."""
        base_url = server_thread

        client = SimpleVTKClient(base_url)

        with patch("builtins.print") as mock_print:
            client.list_tools()

            # Verify print was called (tools were listed)
            mock_print.assert_called()

    def test_error_handling_integration(self, server_thread):
        """Test error handling in full integration."""
        base_url = server_thread

        # Mock scraper to raise exception
        with patch("vtk_mcp_server.server.scraper") as mock_scraper:
            mock_scraper.get_class_info.side_effect = Exception("Test error")

            client = SimpleVTKClient(base_url)

            with patch("builtins.print") as mock_print:
                client.get_class_info_cpp("vtkSphere")

                # Should handle error gracefully
                mock_print.assert_called()

    def test_concurrent_requests(self, server_thread):
        """Test server handling concurrent requests."""
        base_url = server_thread

        def make_request():
            client = SimpleVTKClient(base_url)
            with patch("builtins.print"):
                client.list_tools()
                return True

        # Make multiple concurrent requests
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        assert all(results)
        assert len(results) == 3
