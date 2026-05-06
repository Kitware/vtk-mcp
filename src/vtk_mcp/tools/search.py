"""Retrieval tools — delegate to vtk-index Retriever via VTKMCPContext."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def vector_search_docs(
    query: str,
    ctx: "VTKMCPContext",
    k: int = 10,
) -> list[dict[str, Any]]:
    """Hybrid search over VTK documentation chunks."""
    if ctx.retriever is None:
        return [{"error": "Retrieval not enabled. Set VTK_MCP_ENABLE_RETRIEVAL=true."}]
    chunks = ctx.retriever.search_docs(query, k=k)
    return [_chunk_dict(c) for c in chunks]


def vector_search_examples(
    query: str,
    ctx: "VTKMCPContext",
    k: int = 10,
) -> list[dict[str, Any]]:
    """Hybrid search over VTK code example chunks."""
    if ctx.retriever is None:
        return [{"error": "Retrieval not enabled. Set VTK_MCP_ENABLE_RETRIEVAL=true."}]
    chunks = ctx.retriever.search_code(query, k=k)
    return [_chunk_dict(c) for c in chunks]


def _chunk_dict(chunk) -> dict[str, Any]:
    return chunk.model_dump()
