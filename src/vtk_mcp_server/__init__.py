from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vtk-mcp")
except PackageNotFoundError:
    __version__ = "unknown"
