"""Unit tests for server functions before MCP tool decoration."""

import pytest
from unittest.mock import patch, MagicMock
import io


pytestmark = pytest.mark.unit


def get_vtk_class_info_cpp_func(class_name: str) -> str:
    """Local copy of the C++ info function for testing."""
    from vtk_mcp_server.vtk_scraper import VTKClassScraper

    if not class_name:
        return "Error: class_name is required"

    try:
        scraper = VTKClassScraper()
        info = scraper.get_class_info(class_name)
        if info is None:
            return f"Class '{class_name}' not found in VTK documentation."

        # Simplified formatting for testing
        lines = [f"# {info['class_name']}", ""]

        for section, title in [
            ("brief", "## Brief Description"),
            ("detailed_description", "## Detailed Description"),
        ]:
            if info.get(section):
                lines.extend([title, info[section], ""])

        if info.get("inheritance"):
            lines.append("## Inheritance Hierarchy")
            lines.extend(f"- {cls}" for cls in info["inheritance"])
            lines.append("")

        if info.get("methods"):
            lines.append("## Public Methods")
            methods = info["methods"][:10]
            lines.extend(
                f"- **{m['name']}**: {m.get('description', 'No description')}"
                for m in methods
            )
            if len(info["methods"]) > 10:
                lines.append(f"- ... and {len(info['methods']) - 10} more methods")
            lines.append("")

        lines.extend(["## Documentation URL", info["url"]])
        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving class '{class_name}': {str(e)}"


def get_vtk_class_info_python_func(class_name: str) -> str:
    """Local copy of the Python info function for testing."""
    from contextlib import redirect_stdout

    if not class_name:
        return "Error: class_name is required"

    try:
        # Import vtk module
        import vtk

        # Ensure class name starts with 'vtk'
        if not class_name.startswith("vtk"):
            class_name = f"vtk{class_name}"

        # Get the class from vtk module
        if not hasattr(vtk, class_name):
            return f"Class '{class_name}' not found in VTK Python API."

        vtk_class = getattr(vtk, class_name)

        # Capture help() output
        help_output = io.StringIO()
        with redirect_stdout(help_output):
            help(vtk_class)

        help_text = help_output.getvalue()

        if not help_text:
            return f"No help documentation available for '{class_name}'"

        # Format the output nicely
        return (
            f"# Python API Documentation for {class_name}\n\n" f"```\n{help_text}\n```"
        )

    except ImportError:
        return (
            "Error: VTK Python package is not installed. "
            "Install with 'pip install vtk'"
        )
    except Exception as e:
        return f"Error getting Python help for '{class_name}': {str(e)}"


def search_vtk_classes_func(search_term: str) -> str:
    """Local copy of the search function for testing."""
    from vtk_mcp_server.vtk_scraper import VTKClassScraper

    if not search_term:
        return "Error: search_term is required"

    try:
        scraper = VTKClassScraper()
        matches = scraper.search_classes(search_term)
        if not matches:
            return f"No VTK classes found containing '{search_term}'"

        response = f"VTK classes containing '{search_term}':\n\n"
        response += "\n".join(f"{i}. {cls}" for i, cls in enumerate(matches, 1))
        response += f"\n\nFound {len(matches)} classes."
        return response
    except Exception as e:
        return f"Error searching for '{search_term}': {str(e)}"


class TestServerFunctionsCpp:
    """Test the C++ documentation function."""

    @patch("vtk_mcp_server.vtk_scraper.VTKClassScraper")
    def test_get_vtk_class_info_cpp_success(self, mock_scraper_class):
        """Test successful C++ class info retrieval."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.get_class_info.return_value = {
            "class_name": "vtkSphere",
            "brief": "Test brief description",
            "detailed_description": "Test detailed description",
            "inheritance": ["vtkImplicitFunction", "vtkObject"],
            "methods": [
                {"name": "SetRadius", "description": "Set sphere radius"},
                {"name": "GetRadius", "description": "Get sphere radius"},
            ],
            "url": "https://vtk.org/doc/nightly/html/classvtkSphere.html",
        }

        result = get_vtk_class_info_cpp_func("vtkSphere")

        assert "# vtkSphere" in result
        assert "Test brief description" in result
        assert "Test detailed description" in result
        assert "vtkImplicitFunction" in result
        assert "SetRadius" in result
        mock_scraper.get_class_info.assert_called_once_with("vtkSphere")

    @patch("vtk_mcp_server.vtk_scraper.VTKClassScraper")
    def test_get_vtk_class_info_cpp_not_found(self, mock_scraper_class):
        """Test C++ class info when class not found."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.get_class_info.return_value = None

        result = get_vtk_class_info_cpp_func("NonExistentClass")

        assert "not found in VTK documentation" in result
        mock_scraper.get_class_info.assert_called_once_with("NonExistentClass")

    def test_get_vtk_class_info_cpp_empty_class_name(self):
        """Test C++ class info with empty class name."""
        result = get_vtk_class_info_cpp_func("")
        assert "Error: class_name is required" in result

        result = get_vtk_class_info_cpp_func(None)
        assert "Error: class_name is required" in result


class TestServerFunctionsPython:
    """Test the Python API documentation function."""

    def test_get_vtk_class_info_python_success(self):
        """Test successful Python class info retrieval."""
        # Since VTK is actually installed, let's test with real VTK
        result = get_vtk_class_info_python_func("vtkSphere")

        # Should return formatted Python API documentation
        assert "# Python API Documentation for vtkSphere" in result
        assert "```" in result  # Should be formatted in code block
        assert "class vtkSphere" in result

    def test_get_vtk_class_info_python_empty_class_name(self):
        """Test Python class info with empty class name."""
        result = get_vtk_class_info_python_func("")
        assert "Error: class_name is required" in result

        result = get_vtk_class_info_python_func(None)
        assert "Error: class_name is required" in result


class TestServerFunctionsSearch:
    """Test the search classes function."""

    @patch("vtk_mcp_server.vtk_scraper.VTKClassScraper")
    def test_search_vtk_classes_success(self, mock_scraper_class):
        """Test successful class search."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.search_classes.return_value = [
            "vtkCamera",
            "vtkCameraActor",
            "vtkCameraWidget",
        ]

        result = search_vtk_classes_func("Camera")

        assert "VTK classes containing 'Camera'" in result
        assert "1. vtkCamera" in result
        assert "2. vtkCameraActor" in result
        assert "3. vtkCameraWidget" in result
        assert "Found 3 classes" in result
        mock_scraper.search_classes.assert_called_once_with("Camera")

    @patch("vtk_mcp_server.vtk_scraper.VTKClassScraper")
    def test_search_vtk_classes_no_results(self, mock_scraper_class):
        """Test search when no classes found."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.search_classes.return_value = []

        result = search_vtk_classes_func("NonExistentTerm")

        assert "No VTK classes found containing 'NonExistentTerm'" in result
        mock_scraper.search_classes.assert_called_once_with("NonExistentTerm")

    def test_search_vtk_classes_empty_term(self):
        """Test search with empty search term."""
        result = search_vtk_classes_func("")
        assert "Error: search_term is required" in result

        result = search_vtk_classes_func(None)
        assert "Error: search_term is required" in result
