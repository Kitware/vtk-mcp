#!/usr/bin/env python3

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import click
from fastmcp import FastMCP

from .vtk_scraper import VTKClassScraper
from .import_validator import ImportValidator

logger = logging.getLogger(__name__)

# Initialize
mcp = FastMCP("VTK MCP Server")
scraper = VTKClassScraper()

# Module-level singletons (set at startup via CLI args)
_api_index: Optional[object] = None
_retriever: Optional[object] = None
_import_validator: Optional[ImportValidator] = None


# ---------------------------------------------------------------------------
# C++ documentation tools (unchanged)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_vtk_class_info_cpp(class_name: str) -> str:
    """Get detailed information about a VTK class from online C++ docs."""
    if not class_name:
        return "Error: class_name is required"

    try:
        info = scraper.get_class_info(class_name)
        if info is None:
            return f"Class '{class_name}' not found in VTK documentation."
        return _format_class_info(info)
    except Exception as e:
        return f"Error retrieving class '{class_name}': {str(e)}"


@mcp.tool()
def search_vtk_classes(search_term: str) -> str:
    """Search for VTK classes containing a specific term."""
    if not search_term:
        return "Error: search_term is required"

    try:
        matches = scraper.search_classes(search_term)
        if not matches:
            return f"No VTK classes found containing '{search_term}'"

        response = f"VTK classes containing '{search_term}':\n\n"
        response += "\n".join(f"{i}. {cls}" for i, cls in enumerate(matches, 1))
        response += f"\n\nFound {len(matches)} classes."
        return response
    except Exception as e:
        return f"Error searching for '{search_term}': {str(e)}"


# ---------------------------------------------------------------------------
# Python API documentation tool (from vtk-data VTKAPIIndex)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_vtk_class_info_python(class_name: str) -> str:
    """Get Python API documentation for a VTK class from the pre-built API index.

    Returns class documentation, synopsis, role, and semantic methods as
    formatted markdown. Requires --data-path to be configured at startup.
    """
    if not class_name:
        return "Error: class_name is required"

    if _api_index is None:
        return (
            "Error: API index not loaded. "
            "Start the server with --data-path pointing to vtk-python-docs.jsonl"
        )

    try:
        info = _api_index.get_class_info(class_name)
        if info is None:
            return f"Class '{class_name}' not found in VTK Python API index."

        lines = [f"# Python API Documentation for {class_name}", ""]

        class_doc = info.get("class_doc", "")
        if class_doc:
            lines.extend(["## Class Documentation", "", class_doc, ""])

        synopsis = info.get("synopsis", "")
        if synopsis:
            lines.extend(["## Synopsis", "", synopsis, ""])

        role = info.get("role", "")
        if role:
            lines.extend(["## Pipeline Role", "", role, ""])

        module = info.get("module", "")
        if module:
            lines.extend(["## Module", "", f"`{module}`", ""])

        input_dt = info.get("input_datatype", "")
        output_dt = info.get("output_datatype", "")
        if input_dt or output_dt:
            lines.append("## Data Types")
            lines.append("")
            if input_dt:
                lines.append(f"- **Input:** `{input_dt}`")
            if output_dt:
                lines.append(f"- **Output:** `{output_dt}`")
            lines.append("")

        visibility = info.get("visibility_score", None)
        if visibility is not None:
            lines.extend(["## Visibility Score", "", str(visibility), ""])

        semantic_methods = info.get("semantic_methods", [])
        if semantic_methods:
            lines.append("## Semantic Methods")
            lines.append("")
            lines.extend(f"- `{m}`" for m in semantic_methods)
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving Python info for '{class_name}': {str(e)}"


# ---------------------------------------------------------------------------
# Vector search tool (Qdrant hybrid search via vtk-data Retriever)
# ---------------------------------------------------------------------------


@mcp.tool()
def vector_search_vtk_examples(
    query: str,
    collection: str = "vtk_code",
    top_k: int = 5,
) -> str:
    """Search VTK examples using hybrid vector similarity search (Qdrant).

    Performs semantic + BM25 hybrid search over VTK code examples and
    documentation indexed in Qdrant, returning the most relevant results.

    Args:
        query: The search query describing what you're looking for
        collection: Qdrant collection name (default: vtk_code; also vtk_docs)
        top_k: Number of top results to return (default: 5)

    Returns:
        Formatted markdown string with code snippets and relevance information
    """
    if not query:
        return "Error: query is required"

    if _retriever is None:
        return (
            "Error: Retriever not configured. "
            "Start the server with --qdrant-url option."
        )

    try:
        results = _retriever.hybrid_search(query, collection=collection, limit=top_k)
        return _format_search_results(query, results)
    except Exception as e:
        return f"Error performing vector search: {str(e)}"


def _format_search_results(query: str, results) -> str:
    """Format hybrid search results into readable markdown."""
    lines = [
        f"# Vector Search Results for: {query}",
        "",
        f"Found {len(results)} results.",
        "",
    ]

    for i, result in enumerate(results, 1):
        lines.append(f"## Result {i} (Score: {result.score:.4f})")
        lines.append("")

        if result.class_name:
            lines.append(f"**Class:** `{result.class_name}`")
        if result.role:
            lines.append(f"**Role:** {result.role}")
        if result.example_id:
            lines.append(f"**Source:** {result.example_id}")
        if result.synopsis:
            lines.append(f"**Synopsis:** {result.synopsis}")
        lines.append("")

        content = result.content.strip()
        if content:
            # Detect if content looks like Python code
            is_code = result.collection == "vtk_code" or any(
                kw in content for kw in ("import vtk", "vtk.", "vtkmodules")
            )
            if is_code:
                lines.append("```python")
                lines.append(content)
                lines.append("```")
            else:
                lines.append(content)
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation tools (ported from vtkapi-mcp, 18 tools)
# ---------------------------------------------------------------------------


def _require_api_index() -> str:
    """Return error message if API index is not loaded, else empty string."""
    if _api_index is None:
        return (
            "Error: API index not loaded. "
            "Start the server with --data-path pointing to vtk-python-docs.jsonl"
        )
    return ""


@mcp.tool()
def vtk_get_class_info(class_name: str) -> str:
    """Get complete information about a VTK class including module path, description, and methods."""
    if err := _require_api_index():
        return err

    info = _api_index.get_class_info(class_name)
    if info:
        result = {
            "class_name": info["class_name"],
            "module": info["module"],
            "class_doc": info.get("class_doc", ""),
            "synopsis": info.get("synopsis", ""),
            "role": info.get("role", ""),
            "visibility_score": info.get("visibility_score", ""),
            "input_datatype": info.get("input_datatype", ""),
            "output_datatype": info.get("output_datatype", ""),
            "content": info["content"],
        }
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_search_classes(query: str, limit: int = 10) -> str:
    """Search for VTK classes by name or keyword."""
    if err := _require_api_index():
        return err

    results = _api_index.search_classes(query, limit)
    return json.dumps(results, indent=2)


@mcp.tool()
def vtk_get_class_module(class_name: str) -> str:
    """Return the vtkmodules.* import path for a given VTK class."""
    if err := _require_api_index():
        return err

    module = _api_index.get_class_module(class_name)
    if module:
        result = {"class_name": class_name, "module": module, "found": True}
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_methods(class_name: str, method_name: str = None) -> str:
    """List all methods (with signatures) for a VTK class and optionally verify a specific method."""
    if err := _require_api_index():
        return err

    class_info = _api_index.get_class_info(class_name)
    if not class_info:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
        return json.dumps(result, indent=2)

    methods = _api_index.get_class_methods(class_name)
    requested_method = None
    if method_name:
        requested_method = next(
            (m for m in methods if m["method_name"] == method_name), None
        )
        if not requested_method:
            method_info = _api_index.get_method_info(class_name, method_name)
            if method_info:
                requested_method = {
                    "method_name": method_name,
                    "content": method_info.get("content"),
                    "section": method_info.get("section"),
                }

    result = {
        "class_name": class_name,
        "method_count": len(methods),
        "methods": methods,
        "requested_method": requested_method,
        "method_requested": bool(method_name),
        "found": True,
    }
    if method_name and requested_method is None:
        result["method_error"] = f"Method '{method_name}' not found on '{class_name}'"
        result["method_found"] = False
    else:
        result["method_found"] = bool(requested_method) if method_name else None

    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_module_classes(module: str) -> str:
    """List all VTK classes in a specific module."""
    if err := _require_api_index():
        return err

    classes = _api_index.get_module_classes(module)
    result = {"module": module, "classes": classes, "count": len(classes)}
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_validate_import(import_statement: str) -> str:
    """Validate if a VTK import statement is correct and suggest corrections."""
    if _import_validator is None:
        return json.dumps(
            {
                "error": (
                    "Import validator not available. "
                    "Start the server with --data-path pointing to vtk-python-docs.jsonl"
                )
            },
            indent=2,
        )

    result = _import_validator.validate_import(import_statement)
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_method_info(class_name: str, method_name: str) -> str:
    """Get documentation for a specific method of a VTK class."""
    if err := _require_api_index():
        return err

    info = _api_index.get_method_info(class_name, method_name)
    if info:
        return json.dumps(info, indent=2)
    else:
        result = {
            "error": f"Method '{method_name}' not found in class '{class_name}'",
            "class_name": class_name,
            "method_name": method_name,
            "found": False,
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_method_doc(class_name: str, method_name: str) -> str:
    """Get just the docstring for a specific method of a VTK class."""
    if err := _require_api_index():
        return err

    doc = _api_index.get_method_doc(class_name, method_name)
    if doc is not None:
        result = {
            "class_name": class_name,
            "method_name": method_name,
            "docstring": doc,
            "found": True,
        }
    else:
        result = {
            "error": f"Method '{method_name}' not found in class '{class_name}'",
            "class_name": class_name,
            "method_name": method_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_method_signature(class_name: str, method_name: str) -> str:
    """Return only the canonical signature for a specific method of a VTK class (minimal payload)."""
    if err := _require_api_index():
        return err

    signature = _api_index.get_method_signature(class_name, method_name)
    result = {
        "class_name": class_name,
        "method_name": method_name,
        "signature": signature,
        "found": bool(signature),
    }
    if not signature:
        result["error"] = f"Method '{method_name}' not found in class '{class_name}'"
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_doc(class_name: str) -> str:
    """Get the class documentation string for a VTK class."""
    if err := _require_api_index():
        return err

    doc = _api_index.get_class_doc(class_name)
    if doc is not None:
        result = {"class_name": class_name, "class_doc": doc, "found": True}
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_synopsis(class_name: str) -> str:
    """Get a brief synopsis/summary of what a VTK class does."""
    if err := _require_api_index():
        return err

    synopsis = _api_index.get_class_synopsis(class_name)
    if synopsis is not None:
        result = {"class_name": class_name, "synopsis": synopsis, "found": True}
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_action_phrase(class_name: str) -> str:
    """Get the action phrase describing what a VTK class does (e.g., 'data reading', 'mesh filtering')."""
    if err := _require_api_index():
        return err

    action_phrase = _api_index.get_class_action_phrase(class_name)
    if action_phrase is not None:
        result = {
            "class_name": class_name,
            "action_phrase": action_phrase,
            "found": True,
        }
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_role(class_name: str) -> str:
    """Get the pipeline role of a VTK class.

    Returns one of: input, filter, properties, renderer, scene, infrastructure,
    output, utility, color.
    """
    if err := _require_api_index():
        return err

    role = _api_index.get_class_role(class_name)
    if role is not None:
        result = {"class_name": class_name, "role": role, "found": True}
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_visibility(class_name: str) -> str:
    """Get the visibility score of a VTK class (0.0-1.0).

    Higher scores indicate classes more likely to be used directly.
    """
    if err := _require_api_index():
        return err

    visibility = _api_index.get_class_visibility(class_name)
    if visibility is not None:
        result = {"class_name": class_name, "visibility": visibility, "found": True}
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_input_datatype(class_name: str) -> str:
    """Get the input data type for a VTK class (e.g., 'vtkPolyData', 'vtkImageData')."""
    if err := _require_api_index():
        return err

    input_datatype = _api_index.get_class_input_datatype(class_name)
    if input_datatype is not None:
        result = {
            "class_name": class_name,
            "input_datatype": input_datatype,
            "found": True,
        }
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_output_datatype(class_name: str) -> str:
    """Get the output data type for a VTK class (e.g., 'vtkPolyData', 'vtkImageData')."""
    if err := _require_api_index():
        return err

    output_datatype = _api_index.get_class_output_datatype(class_name)
    if output_datatype is not None:
        result = {
            "class_name": class_name,
            "output_datatype": output_datatype,
            "found": True,
        }
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_get_class_semantic_methods(class_name: str) -> str:
    """Get non-boilerplate callable methods for a VTK class.

    Excludes dunder methods, private methods, and VTK infrastructure methods.
    """
    if err := _require_api_index():
        return err

    semantic_methods = _api_index.get_class_semantic_methods(class_name)
    if semantic_methods is not None:
        result = {
            "class_name": class_name,
            "semantic_methods": semantic_methods,
            "found": True,
        }
    else:
        result = {
            "error": f"Class '{class_name}' not found in VTK API",
            "class_name": class_name,
            "found": False,
        }
    return json.dumps(result, indent=2)


@mcp.tool()
def vtk_is_a_class(class_name: str) -> str:
    """Check if a given name is a valid VTK class.

    Returns true if it exists in the VTK API, false otherwise.
    """
    if err := _require_api_index():
        return err

    exists = _api_index.get_class_info(class_name) is not None
    result = {"class_name": class_name, "is_vtk_class": exists}
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_class_info(info: dict) -> str:
    """Format C++ class info into readable markdown."""
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport protocol",
)
@click.option("--host", default="127.0.0.1", help="Host (HTTP only)")
@click.option("--port", default=8000, type=int, help="Port (HTTP only)")
@click.option(
    "--data-path",
    type=click.Path(exists=True),
    help="Path to vtk-python-docs.jsonl (enables Python API info and validation tools)",
)
@click.option(
    "--qdrant-url",
    default="http://localhost:6333",
    help="Qdrant server URL (enables vector_search_vtk_examples)",
)
def main(transport, host, port, data_path, qdrant_url):
    """Run the VTK MCP Server"""
    global _api_index, _retriever, _import_validator

    if data_path:
        try:
            from vtk_data.index import VTKAPIIndex

            _api_index = VTKAPIIndex(Path(data_path))
            _import_validator = ImportValidator(_api_index)
            click.echo(f"Loaded VTK API index from: {data_path}")
        except ImportError:
            click.echo(
                "Warning: vtk-data package not installed. "
                "Install with 'pip install vtk-data'. "
                "Python API info and validation tools will be unavailable.",
                err=True,
            )
        except Exception as e:
            click.echo(f"Warning: Failed to load API index: {e}", err=True)

    if qdrant_url:
        try:
            from vtk_data.retriever import Retriever

            _retriever = Retriever(qdrant_url=qdrant_url)
            click.echo(f"Connected to Qdrant at: {qdrant_url}")
        except ImportError:
            click.echo(
                "Warning: vtk-data[rag] not installed. "
                "Install with 'pip install vtk-data[rag]'. "
                "Vector search will be unavailable.",
                err=True,
            )
        except Exception as e:
            click.echo(f"Warning: Failed to connect to Qdrant: {e}", err=True)

    if transport == "http":
        click.echo(f"Starting VTK MCP Server on http://{host}:{port}")
        asyncio.run(mcp.run_http_async(host=host, port=port))
    else:
        click.echo("Starting VTK MCP Server on stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()
