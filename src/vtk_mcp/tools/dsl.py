"""DSL translation tool — delegates to vtk-validate's dsl subpackage."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def translate_prompt_to_dsl(query: str, ctx: "VTKMCPContext") -> str:
    """Build DSL grammar and class context for translating a VTK request.

    Uses vtk-validate's DSL context builder with the loaded api_index for
    class context. No LLM call is made — the caller is expected to use the
    returned grammar and context to write the DSL itself.

    Args:
        query: Natural language description (e.g. "create a warped sine surface").

    Returns:
        A text block with translation instructions, the DSL grammar,
        relevant VTK class context, and the original request.
    """
    try:
        from vtk_validate.dsl import build_dsl_translation_context
    except ImportError as e:
        return f"Error: vtk-validate not installed — {e}"

    return build_dsl_translation_context(query=query, api_index=ctx.api_index)


def is_dsl_prompt(text: str) -> bool:
    """Return True if *text* is already in the VTK pipeline DSL format."""
    from vtk_validate.dsl import is_dsl

    return is_dsl(text)
