"""Documentation lookup tools (delegates to vtk-knowledge via VTKMCPContext)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def get_vtk_class_info_python(class_name: str, ctx: "VTKMCPContext") -> dict:
    """Get Python API info for a VTK class from the knowledge index."""
    from vtk_validate.tools import vtk_get_class_info

    return vtk_get_class_info(class_name, ctx.api_index)


def vtk_search_classes(query: str, ctx: "VTKMCPContext", limit: int = 10) -> list:
    from vtk_validate.tools import vtk_search_classes as _search

    return _search(query, ctx.api_index, limit=limit)


def vtk_get_class_doc(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_doc as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_synopsis(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_synopsis as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_role(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_role as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_input_datatype(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_input_datatype as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_output_datatype(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_output_datatype as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_methods(class_name: str, ctx: "VTKMCPContext") -> list:
    from vtk_validate.tools import vtk_get_class_methods as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_semantic_methods(class_name: str, ctx: "VTKMCPContext") -> list:
    from vtk_validate.tools import vtk_get_class_semantic_methods as _f

    return _f(class_name, ctx.api_index)


def vtk_get_method_info(class_name: str, method_name: str, ctx: "VTKMCPContext") -> dict:
    from vtk_validate.tools import vtk_get_method_info as _f

    return _f(class_name, method_name, ctx.api_index)


def vtk_get_method_doc(class_name: str, method_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_method_doc as _f

    return _f(class_name, method_name, ctx.api_index)


def vtk_get_method_signature(class_name: str, method_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_method_signature as _f

    return _f(class_name, method_name, ctx.api_index)


def vtk_get_class_module(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_module as _f

    return _f(class_name, ctx.api_index)


def vtk_get_module_classes(module: str, ctx: "VTKMCPContext") -> list:
    from vtk_validate.tools import vtk_get_module_classes as _f

    return _f(module, ctx.api_index)


def vtk_is_a_class(class_name: str, ctx: "VTKMCPContext") -> bool:
    from vtk_validate.tools import vtk_is_a_class as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_action_phrase(class_name: str, ctx: "VTKMCPContext") -> str:
    from vtk_validate.tools import vtk_get_class_action_phrase as _f

    return _f(class_name, ctx.api_index)


def vtk_get_class_visibility(class_name: str, ctx: "VTKMCPContext"):
    from vtk_validate.tools import vtk_get_class_visibility as _f

    return _f(class_name, ctx.api_index)
