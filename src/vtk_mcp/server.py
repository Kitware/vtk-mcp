"""FastMCP server with all tool registrations.

This module registers every MCP tool exposed by the gateway. Each tool
delegates to a function in ``vtk_mcp.tools.*``, which in turn delegates
to the appropriate layer-1/2/3 library.  No domain logic lives here.
"""

from __future__ import annotations

from fastmcp import FastMCP

from .composition import VTKMCPContext

mcp = FastMCP("vtk-mcp")

# The context singleton is set by composition.init_context() before the
# server starts.  Tools call get_context() at request time.


def _ctx() -> VTKMCPContext:
    from .composition import get_context
    return get_context()


# ── Layer 1: Documentation lookup ─────────────────────────────────────────

@mcp.tool()
def get_vtk_class_info_python(class_name: str) -> dict:
    """Get Python API info for a VTK class (module, methods, synopsis, role, etc.)."""
    from .tools.docs import get_vtk_class_info_python as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_search_classes(query: str, limit: int = 10) -> list:
    """Search for VTK classes by name or keyword."""
    from .tools.docs import vtk_search_classes as _f
    return _f(query, _ctx(), limit=limit)


@mcp.tool()
def vtk_get_class_doc(class_name: str) -> str:
    """Get the docstring for a VTK class."""
    from .tools.docs import vtk_get_class_doc as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_synopsis(class_name: str) -> str:
    """Get a one-sentence synopsis for a VTK class."""
    from .tools.docs import vtk_get_class_synopsis as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_role(class_name: str) -> str:
    """Get the pipeline role of a VTK class (source, filter, mapper, output, etc.)."""
    from .tools.docs import vtk_get_class_role as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_input_datatype(class_name: str) -> str:
    """Get the input data type expected by a VTK class."""
    from .tools.docs import vtk_get_class_input_datatype as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_output_datatype(class_name: str) -> str:
    """Get the output data type produced by a VTK class."""
    from .tools.docs import vtk_get_class_output_datatype as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_methods(class_name: str) -> list:
    """List all methods (with signatures) for a VTK class."""
    from .tools.docs import vtk_get_class_methods as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_semantic_methods(class_name: str) -> list:
    """List non-boilerplate callable methods for a VTK class."""
    from .tools.docs import vtk_get_class_semantic_methods as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_method_info(class_name: str, method_name: str) -> dict:
    """Get documentation for a specific method of a VTK class."""
    from .tools.docs import vtk_get_method_info as _f
    return _f(class_name, method_name, _ctx())


@mcp.tool()
def vtk_get_method_doc(class_name: str, method_name: str) -> str:
    """Get the docstring for a specific method of a VTK class."""
    from .tools.docs import vtk_get_method_doc as _f
    return _f(class_name, method_name, _ctx())


@mcp.tool()
def vtk_get_method_signature(class_name: str, method_name: str) -> str:
    """Get the canonical signature for a specific method of a VTK class."""
    from .tools.docs import vtk_get_method_signature as _f
    return _f(class_name, method_name, _ctx())


@mcp.tool()
def vtk_get_class_module(class_name: str) -> str:
    """Get the vtkmodules.* import path for a VTK class."""
    from .tools.docs import vtk_get_class_module as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_module_classes(module: str) -> list:
    """List all VTK classes in a specific module."""
    from .tools.docs import vtk_get_module_classes as _f
    return _f(module, _ctx())


@mcp.tool()
def vtk_is_a_class(class_name: str) -> bool:
    """Check if a name is a valid VTK class."""
    from .tools.docs import vtk_is_a_class as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_action_phrase(class_name: str) -> str:
    """Get the action phrase for a VTK class (e.g. 'mesh smoothing')."""
    from .tools.docs import vtk_get_class_action_phrase as _f
    return _f(class_name, _ctx())


@mcp.tool()
def vtk_get_class_visibility(class_name: str) -> float | None:
    """Get the visibility score (0.0–1.0) for a VTK class."""
    from .tools.docs import vtk_get_class_visibility as _f
    return _f(class_name, _ctx())


# ── Layer 2: Retrieval ─────────────────────────────────────────────────────

@mcp.tool()
def vector_search_docs(query: str, k: int = 10) -> list:
    """Hybrid semantic search over VTK documentation chunks."""
    from .tools.search import vector_search_docs as _f
    return _f(query, _ctx(), k=k)


@mcp.tool()
def vector_search_examples(query: str, k: int = 10) -> list:
    """Hybrid semantic search over VTK code example chunks."""
    from .tools.search import vector_search_examples as _f
    return _f(query, _ctx(), k=k)


# ── Layer 3: Validation ────────────────────────────────────────────────────

@mcp.tool()
def validate_vtk_code(source: str) -> dict:
    """Validate a Python source string against the VTK API.

    Returns a ValidationReport with status and diagnostics.
    """
    from .tools.validation import validate_vtk_code as _f
    return _f(source, _ctx())


@mcp.tool()
def vtk_validate_import(import_statement: str) -> dict:
    """Validate a VTK import statement and suggest corrections."""
    from .tools.validation import vtk_validate_import as _f
    return _f(import_statement, _ctx())


# ── C++ scraping (self-contained, no layer dependency) ─────────────────────

@mcp.tool()
def get_vtk_class_info_cpp(class_name: str) -> str:
    """Get detailed information about a VTK class from the online C++ docs."""
    from .tools.scraping import get_vtk_class_info_cpp as _f
    return _f(class_name, _ctx())


@mcp.tool()
def search_vtk_classes_cpp(search_term: str) -> str:
    """Search for VTK classes in the C++ documentation."""
    from .tools.scraping import search_vtk_classes_cpp as _f
    return _f(search_term, _ctx())


# ── Meta ───────────────────────────────────────────────────────────────────

@mcp.tool()
def vtk_version_info() -> dict:
    """Return the VTK version loaded by this gateway instance."""
    ctx = _ctx()
    return {
        "vtk_version": ctx.api_index.vtk_version,
        "class_count": len(ctx.api_index.classes),
        "retrieval_enabled": ctx.retriever is not None,
        "validation_enabled": ctx.validate is not None,
    }
