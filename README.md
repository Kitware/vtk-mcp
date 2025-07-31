# VTK MCP Server

<img width="256" height="256" alt="vtk-mcp" src="https://github.com/user-attachments/assets/f1e8fc6d-2f51-4a15-8d02-12a05074dded" />

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

## Docker

### Using Pre-built Image

```bash
# Run with Docker/Podman
docker run -p 8000:8000 ghcr.io/kitware/vtk-mcp:latest

# Or with Podman
podman run -p 8000:8000 ghcr.io/kitware/vtk-mcp:latest

# Access server at http://localhost:8000/mcp/
```

### Building Locally

```bash
# Build image
docker build -t vtk-mcp-server .

# Or with Podman
podman build -t vtk-mcp-server .

# Run container
docker run -p 8000:8000 vtk-mcp-server
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

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

## Testing

Install test dependencies:

```bash
pip install -e ".[test]"
```

Run tests:

```bash
# Run all tests
pytest

# Run specific test types using markers
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests only
pytest -m http                  # HTTP transport tests
pytest -m stdio                 # Stdio transport tests

# Run specific test files
pytest tests/test_server_functions.py      # Server unit tests
pytest tests/test_client_no_server.py      # Client error handling
pytest tests/test_http_integration.py      # HTTP integration
pytest tests/test_stdio_integration.py     # Stdio integration

# Useful pytest options
pytest -v                       # Verbose output
pytest -x                       # Stop on first failure
pytest --tb=short              # Short traceback format
pytest -k "test_name"          # Run tests matching pattern
```

### Test Structure

- `tests/test_server_functions.py` - Unit tests for MCP tool functions (no server required)
- `tests/test_client_no_server.py` - Client error handling when server unavailable
- `tests/test_http_integration.py` - Full integration tests with HTTP transport
- `tests/test_stdio_integration.py` - Full integration tests with stdio transport
- `tests/conftest.py` - Shared test fixtures and configuration

## Authors
- Vicente Bolea @ Kitware
