# VTK MCP

<img width="256" height="256" alt="vtk-mcp" src="https://github.com/user-attachments/assets/f1e8fc6d-2f51-4a15-8d02-12a05074dded" />

A thin MCP gateway that exposes [vtk-knowledge](https://github.com/vicentebolea/vtk-knowledge), [vtk-index](https://github.com/vicentebolea/vtk-index), and [vtk-validate](https://github.com/vicentebolea/vtk-validate) as Model Context Protocol tools. All domain logic lives in those libraries; this project only wires them together.

## Installation

```bash
# With uv (recommended)
uv add vtk-mcp

# With pip
pip install \
  "git+https://github.com/vicentebolea/vtk-knowledge" \
  "git+https://github.com/vicentebolea/vtk-validate"
pip install -e .

# With retrieval support (vtk-index)
pip install \
  "git+https://github.com/vicentebolea/vtk-knowledge" \
  "git+https://github.com/vicentebolea/vtk-validate" \
  "git+https://github.com/vicentebolea/vtk-index"
pip install -e ".[retrieval]"
```

## Usage

```bash
# stdio (default — for MCP clients)
vtk-mcp

# HTTP
vtk-mcp --transport http --port 8000

# Pin a specific VTK version (artifact auto-downloaded from ghcr.io)
vtk-mcp --vtk-version 9.6.1
```

Key environment variables:

| Variable | Default | Description |
|---|---|---|
| `VTK_MCP_VTK_VERSION` | `9.3.0` | VTK version to fetch artifacts for |
| `VTK_MCP_KNOWLEDGE_ARTIFACT_PATH` | _(auto)_ | Local JSONL path; skips auto-download |
| `VTK_MCP_ENABLE_RETRIEVAL` | `false` | Enable vtk-index semantic search |
| `VTK_MCP_QDRANT_URL` | _(auto)_ | Qdrant URL; if unset uses embedded storage |
| `VTK_MCP_ENABLE_VALIDATION` | `true` | Enable vtk-validate code validation |
| `VTK_MCP_TRANSPORT` | `stdio` | `stdio` or `http` |

## MCP Tools

### Knowledge lookup — via [vtk-knowledge](https://github.com/vicentebolea/vtk-knowledge) + [vtk-validate](https://github.com/vicentebolea/vtk-validate)

Data comes from the vtk-knowledge artifact; the query helpers are implemented in vtk-validate's tool layer.

| Tool | Description |
|---|---|
| `vtk_get_class_info(class_name)` | Full class record (all fields below as one call) |
| `vtk_search_classes(query, limit)` | Search classes by name or keyword |
| `vtk_get_class_doc(class_name)` | Docstring for a class |
| `vtk_get_class_synopsis(class_name)` | One-sentence synopsis |
| `vtk_get_class_role(class_name)` | Pipeline role (`source` / `filter` / `mapper` / …) |
| `vtk_get_class_input_datatype(class_name)` | Expected input data type |
| `vtk_get_class_output_datatype(class_name)` | Produced output data type |
| `vtk_get_class_methods(class_name)` | All methods with signatures |
| `vtk_get_class_semantic_methods(class_name)` | Non-boilerplate callable methods |
| `vtk_get_method_info(class_name, method_name)` | Full method record |
| `vtk_get_method_doc(class_name, method_name)` | Method docstring |
| `vtk_get_method_signature(class_name, method_name)` | Canonical method signature |
| `vtk_get_class_module(class_name)` | `vtkmodules.*` import path |
| `vtk_get_module_classes(module)` | All classes in a module |
| `vtk_is_a_class(class_name)` | Check if a name is a valid VTK class |
| `vtk_get_class_action_phrase(class_name)` | Action phrase (e.g. "mesh smoothing") |
| `vtk_get_class_visibility(class_name)` | Visibility score 0.0–1.0 |
| `vtk_get_class_inheritance(class_name)` | Full MRO chain |
| `vtk_get_class_record_metadata(class_name)` | `{vtk_version, schema_version, content_hash}` |
| `vtk_version_info()` | VTK version and enabled features for the loaded index |

### Semantic search — via [vtk-index](https://github.com/vicentebolea/vtk-index)

Requires `VTK_MCP_ENABLE_RETRIEVAL=true`. vtk-index owns all chunking, embedding, and Qdrant hybrid retrieval (dense + BM25 with RRF fusion); vtk-mcp simply delegates.

| Tool | Description |
|---|---|
| `vector_search_docs(query, k, role, class_name, min_visibility)` | Hybrid search over VTK documentation chunks |
| `vector_search_examples(query, k, role, class_name, min_visibility)` | Hybrid search over VTK code example chunks |

Both search tools accept optional Qdrant payload filters:

| Parameter | Type | Description |
|---|---|---|
| `k` | `int` | Number of results (default 10) |
| `role` | `str` | Filter by pipeline role (`source`, `filter`, `mapper`, `output`) |
| `class_name` | `str` | Restrict to chunks mentioning a specific class |
| `min_visibility` | `float` | Minimum visibility score threshold (0.0–1.0) |

When `VTK_MCP_QDRANT_URL` is unset, vtk-index downloads a pre-built embedded Qdrant storage from `ghcr.io/vicentebolea/vtk-index` on first use — no server required.

### Validation — via [vtk-validate](https://github.com/vicentebolea/vtk-validate)

AST-based validation against the VTK API. Checks imports, constructors, method calls, argument ordering, and security issues.

| Tool | Description |
|---|---|
| `validate_vtk_code(source)` | Validate a Python source string; returns `{status, diagnostics, vtk_version, elapsed_ms}` |
| `vtk_validate_import(import_statement)` | Validate a single import line and suggest corrections |


## Docker

```bash
# Run pre-built image (artifacts pre-cached for VTK 9.6.1)
podman run ghcr.io/kitware/vtk-mcp:latest

# Build locally
podman build -f deploy.Dockerfile -t vtk-mcp .

# Build for a specific VTK version
podman build -f deploy.Dockerfile --build-arg VTK_VERSION=9.6.1 -t vtk-mcp .
```

## Development

```bash
# Install sibling packages from local checkouts
uv sync --extra dev

# Or with pip
pip install \
  "git+https://github.com/vicentebolea/vtk-knowledge" \
  "git+https://github.com/vicentebolea/vtk-validate"
pip install -e ".[dev]"

# Lint and format
ruff check src/vtk_mcp/
ruff format src/vtk_mcp/

# Tests
pytest -m unit
pytest tests/test_client_no_server.py
pytest -m integration
```

## Architecture

```
vtk-mcp  (this repo — composition root only)
├── vtk-knowledge   schema, VTKAPIIndex, artifact download
├── vtk-index       chunking, embedding, Qdrant retrieval
└── vtk-validate    AST-based code validation
```

`src/vtk_mcp/composition.py` constructs all dependencies once at startup; tool handlers in `src/vtk_mcp/tools/` delegate to the libraries with no added logic.

## Authors

- Patrick O'Leary @ Kitware
- Vicente Bolea @ Kitware
