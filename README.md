# VTK MCP Server

Access VTK class documentation through a Model Context Protocol server.

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install .
```

## Usage

### Server

```bash
# Start stdio server (for MCP clients)
vtk-mcp-server

# Start HTTP server for direct access
vtk-mcp-server --transport http --host localhost --port 8000
```

### Client

```bash
# Get detailed C++ class information  
vtk-mcp-client info-cpp vtkActor
vtk-mcp-client info-cpp vtkPolyData

# Get Python API documentation
vtk-mcp-client info-python vtkSphere
vtk-mcp-client info-python Renderer

# Search for classes containing a term
vtk-mcp-client search Camera
vtk-mcp-client search Filter

# List available tools
vtk-mcp-client list-tools

# Connect to different server
vtk-mcp-client --host localhost --port 8000 info-cpp vtkActor
```

## MCP Tools

The server provides three MCP tools:
- `get_vtk_class_info_cpp(class_name)` - Get detailed C++ documentation for a VTK class from online documentation
- `get_vtk_class_info_python(class_name)` - Get Python API documentation using help() function
- `search_vtk_classes(search_term)` - Search for VTK classes containing a term

## Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Format and lint
black src/
flake8 src/ --max-line-length=88

# Test the HTTP server and client
vtk-mcp-server --transport http &
vtk-mcp-client info-cpp vtkActor
```
