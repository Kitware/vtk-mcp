"""Tests for client behavior when server is not available."""

import responses
from unittest.mock import patch
from vtk_mcp_server.simple_client import SimpleVTKClient


class TestClientWithoutServer:
    """Test client error handling when server is unavailable."""

    def test_initialization_with_no_server(self):
        """Test client initialization when server is not running."""
        with patch("requests.Session.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            # Client should initialize but fail silently
            client = SimpleVTKClient("http://localhost:9999")
            assert client.session_id is None

    @responses.activate
    def test_get_class_info_cpp_no_server(self):
        """Test get_class_info_cpp when server is not available."""
        responses.add(
            responses.POST,
            "http://localhost:9999/mcp/",
            body=Exception("Connection refused"),
        )

        client = SimpleVTKClient("http://localhost:9999")

        # Should not crash, should handle error gracefully
        with patch("builtins.print") as mock_print:
            client.get_class_info_cpp("vtkSphere")
            mock_print.assert_called()

    @responses.activate
    def test_get_class_info_python_no_server(self):
        """Test get_class_info_python when server is not available."""
        responses.add(
            responses.POST,
            "http://localhost:9999/mcp/",
            body=Exception("Connection refused"),
        )

        client = SimpleVTKClient("http://localhost:9999")

        # Should not crash, should handle error gracefully
        with patch("builtins.print") as mock_print:
            client.get_class_info_python("vtkSphere")
            mock_print.assert_called()

    @responses.activate
    def test_search_classes_no_server(self):
        """Test search_classes when server is not available."""
        responses.add(
            responses.POST,
            "http://localhost:9999/mcp/",
            body=Exception("Connection refused"),
        )

        client = SimpleVTKClient("http://localhost:9999")

        # Should not crash, should handle error gracefully
        with patch("builtins.print") as mock_print:
            client.search_classes("Camera")
            mock_print.assert_called()

    @responses.activate
    def test_list_tools_no_server(self):
        """Test list_tools when server is not available."""
        responses.add(
            responses.POST,
            "http://localhost:9999/mcp/",
            body=Exception("Connection refused"),
        )

        client = SimpleVTKClient("http://localhost:9999")

        # Should not crash, should handle error gracefully
        with patch("builtins.print") as mock_print:
            client.list_tools()
            mock_print.assert_called()

    def test_malformed_response_handling(self):
        """Test client handling of malformed server responses."""
        with responses.RequestsMock() as rsps:
            # Mock initialization
            rsps.add(
                responses.POST,
                "http://localhost:8000/mcp/",
                json={"result": {"capabilities": {}}},
                headers={"Mcp-Session-Id": "test-session"},
            )
            rsps.add(responses.POST, "http://localhost:8000/mcp/", body="OK")

            # Mock malformed response
            rsps.add(
                responses.POST, "http://localhost:8000/mcp/", body="data: invalid json"
            )

            client = SimpleVTKClient("http://localhost:8000")

            with patch("builtins.print") as mock_print:
                client.get_class_info_cpp("vtkSphere")
                # Should print parse error
                mock_print.assert_called()

    def test_http_error_response(self):
        """Test client handling of HTTP error responses."""
        with responses.RequestsMock() as rsps:
            # Mock initialization
            rsps.add(
                responses.POST,
                "http://localhost:8000/mcp/",
                json={"result": {"capabilities": {}}},
                headers={"Mcp-Session-Id": "test-session"},
            )
            rsps.add(responses.POST, "http://localhost:8000/mcp/", body="OK")

            # Mock HTTP error
            rsps.add(
                responses.POST,
                "http://localhost:8000/mcp/",
                status=500,
                body="Server Error",
            )

            client = SimpleVTKClient("http://localhost:8000")

            with patch("builtins.print") as mock_print:
                client.get_class_info_cpp("vtkSphere")
                # Should print HTTP error
                mock_print.assert_called()
