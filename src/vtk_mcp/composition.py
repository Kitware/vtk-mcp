"""Composition root — wires layers 1–3 at startup.

All layer dependencies are constructed exactly once here and held as
singletons on VTKMCPContext.  Tool handlers receive a context instance
rather than constructing their own dependencies.
"""

from __future__ import annotations

import logging

from vtk_knowledge import VTKAPIIndex

from .config import Settings

logger = logging.getLogger(__name__)


class VTKMCPContext:
    """Holds all layer-1/2/3 dependencies as singletons.

    Constructed once at gateway startup; injected into every tool handler.
    """

    api_index: VTKAPIIndex
    retriever: object  # vtk_index.Retriever | None
    validate: object  # callable(source: str) -> ValidationReport | None
    settings: Settings

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Layer 1: knowledge index — download artifact if no local path given
        if settings.knowledge_artifact_path is not None:
            logger.info("Loading knowledge artifact from %s", settings.knowledge_artifact_path)
            self.api_index = VTKAPIIndex.from_jsonl(settings.knowledge_artifact_path)
        else:
            logger.info("Downloading knowledge artifact for VTK %s", settings.vtk_version)
            self.api_index = VTKAPIIndex.from_artifact(settings.vtk_version)
        logger.info(
            "Loaded %d classes (vtk_version=%s)",
            len(self.api_index.classes),
            self.api_index.vtk_version,
        )

        # Layer 2: retrieval (optional)
        self.retriever = None
        if settings.enable_retrieval:
            try:
                from vtk_index import Retriever

                if settings.qdrant_url:
                    # Connect to a running Qdrant server
                    self.retriever = Retriever(
                        qdrant_url=settings.qdrant_url,
                        vtk_version=self.api_index.vtk_version,
                    )
                    logger.info("Retriever connected to %s", settings.qdrant_url)
                else:
                    # Download pre-built embedded storage (no server required)
                    logger.info(
                        "Downloading embedded Qdrant storage for VTK %s",
                        self.api_index.vtk_version,
                    )
                    self.retriever = Retriever.from_artifact(self.api_index.vtk_version)
                    logger.info("Retriever ready (embedded storage)")
            except Exception as exc:
                logger.warning("Retrieval disabled: %s", exc)

        # Layer 3: validation (optional — library call, no subprocess)
        self.validate = None
        if settings.enable_validation:
            try:
                from vtk_validate import validate as _validate

                _index = self.api_index

                def _validate_bound(source: str):
                    return _validate(source, _index)

                self.validate = _validate_bound
                logger.info("Validation enabled")
            except Exception as exc:
                logger.warning("Validation disabled: %s", exc)


_context: VTKMCPContext | None = None


def get_context() -> VTKMCPContext:
    if _context is None:
        raise RuntimeError("VTKMCPContext not initialised. Call init_context() first.")
    return _context


def init_context(settings: Settings | None = None) -> VTKMCPContext:
    global _context
    if settings is None:
        settings = Settings()
    _context = VTKMCPContext(settings)
    return _context
