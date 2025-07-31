"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vtk():
    """Mock VTK module for testing."""
    with patch("vtk_mcp_server.server.vtk") as mock_vtk:
        # Set up common VTK class mocks
        mock_vtk.vtkSphere = type("vtkSphere", (), {})
        mock_vtk.vtkCamera = type("vtkCamera", (), {})
        mock_vtk.vtkRenderer = type("vtkRenderer", (), {})
        yield mock_vtk


@pytest.fixture
def mock_scraper():
    """Mock VTK scraper for testing."""
    with patch("vtk_mcp_server.server.scraper") as mock_scraper:
        # Set up default return values
        mock_scraper.get_class_info.return_value = {
            "class_name": "vtkSphere",
            "brief": "Test sphere class",
            "detailed_description": "A test sphere implementation",
            "inheritance": ["vtkImplicitFunction", "vtkObject"],
            "methods": [
                {"name": "SetRadius", "description": "Set sphere radius"},
                {"name": "GetRadius", "description": "Get sphere radius"},
            ],
            "url": "https://test.vtk.org/classvtkSphere.html",
        }

        mock_scraper.search_classes.return_value = [
            "vtkSphere",
            "vtkSphereSource",
            "vtkSpherePuzzle",
        ]

        yield mock_scraper


@pytest.fixture
def sample_class_info():
    """Sample class info data for testing."""
    return {
        "class_name": "vtkTestClass",
        "brief": "A test VTK class",
        "detailed_description": "This is a detailed description of the test class",
        "inheritance": ["vtkObject"],
        "methods": [
            {"name": "TestMethod", "description": "A test method"},
        ],
        "url": "https://test.vtk.org/classvtkTestClass.html",
    }


@pytest.fixture
def mcp_request():
    """Sample MCP request for testing."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request",
        "method": "tools/call",
        "params": {
            "name": "get_vtk_class_info_cpp",
            "arguments": {"class_name": "vtkSphere"},
        },
    }


@pytest.fixture
def mcp_init_request():
    """Sample MCP initialization request."""
    return {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
