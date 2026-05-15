"""Retrieval tools — delegate to vtk-index Retriever via VTKMCPContext."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..composition import VTKMCPContext


def vector_search_docs(
    query: str,
    ctx: "VTKMCPContext",
    k: int = 10,
    role: str | None = None,
    class_name: str | None = None,
    min_visibility: float | None = None,
) -> list[dict[str, Any]]:
    """Hybrid search over VTK documentation chunks."""
    if ctx.retriever is None:
        return [{"error": "Retrieval not enabled. Set VTK_MCP_ENABLE_RETRIEVAL=true."}]
    filters = _build_filters(role=role, class_name=class_name, min_visibility=min_visibility)
    chunks = ctx.retriever.search_docs(query, k=k, filters=filters or None)
    return [_chunk_dict(c) for c in chunks]


def vector_search_examples(
    query: str,
    ctx: "VTKMCPContext",
    k: int = 10,
    role: str | None = None,
    class_name: str | None = None,
    min_visibility: float | None = None,
) -> list[dict[str, Any]]:
    """Hybrid search over VTK code example chunks."""
    if ctx.retriever is None:
        return [{"error": "Retrieval not enabled. Set VTK_MCP_ENABLE_RETRIEVAL=true."}]
    filters = _build_filters(role=role, class_name=class_name, min_visibility=min_visibility)
    chunks = ctx.retriever.search_code(query, k=k, filters=filters or None)
    return [_chunk_dict(c) for c in chunks]


def _build_filters(
    role: str | None,
    class_name: str | None,
    min_visibility: float | None,
) -> dict[str, Any]:
    f: dict[str, Any] = {}
    if role is not None:
        f["role"] = role
    if class_name is not None:
        f["class_names"] = class_name
    if min_visibility is not None:
        f["visibility_score"] = {"gte": min_visibility}
    return f


def _chunk_dict(chunk) -> dict[str, Any]:
    return chunk.model_dump()
