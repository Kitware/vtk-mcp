"""Validation tools — delegate to vtk-validate library via VTKMCPContext."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def validate_vtk_code(source: str, ctx: "VTKMCPContext") -> dict[str, Any]:
    """Validate a Python source string against the VTK API.

    Returns a ValidationReport dict with ``status`` and ``diagnostics``.
    """
    if ctx.validate is None:
        return {"error": "Validation not enabled. Set VTK_MCP_ENABLE_VALIDATION=true."}
    report = ctx.validate(source)
    return report.model_dump()


def vtk_validate_import(import_statement: str, ctx: "VTKMCPContext") -> dict[str, Any]:
    from vtk_validate.tools import vtk_validate_import as _f
    return _f(import_statement, ctx.api_index)
