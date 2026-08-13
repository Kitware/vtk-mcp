"""DSL translation tool — delegates to vtk-validate's dsl subpackage."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def translate_prompt_to_dsl(
    query: str,
    ctx: "VTKMCPContext",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """Translate a natural language VTK request into the pipeline DSL.

    Uses vtk-validate's DSL translator with the loaded api_index for class
    context. All parameters fall back to VTK_MCP_TRANSLATE_* env vars when
    not provided.

    Args:
        query: Natural language description (e.g. "create a warped sine surface").
        model: LiteLLM model identifier. Overrides VTK_MCP_TRANSLATE_MODEL when set.
        base_url: OpenAI-compatible base URL (e.g. ``http://localhost:11434`` for Ollama).
                  Overrides VTK_MCP_TRANSLATE_BASE_URL when set.
        api_key: API key for the endpoint. Overrides VTK_MCP_TRANSLATE_API_KEY when set.

    Returns:
        A VTK pipeline DSL string ready for code generation.
    """
    try:
        from vtk_validate.dsl import translate_to_dsl

        return translate_to_dsl(
            query=query,
            api_index=ctx.api_index,
            model=model or ctx.settings.translate_model,
            base_url=base_url or ctx.settings.translate_base_url,
            api_key=api_key or ctx.settings.translate_api_key,
        )
    except ImportError as e:
        return f"Error: vtk-validate[translate] not installed — {e}"


def is_dsl_prompt(text: str) -> bool:
    """Return True if *text* is already in the VTK pipeline DSL format."""
    from vtk_validate.dsl import is_dsl

    return is_dsl(text)
