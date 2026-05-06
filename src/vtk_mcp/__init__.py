"""vtk-mcp — production MCP gateway composing vtk-knowledge, vtk-index, and vtk-validate."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vtk-mcp")
except PackageNotFoundError:
    __version__ = "unknown"
