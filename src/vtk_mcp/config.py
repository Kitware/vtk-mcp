"""Pydantic Settings for the vtk-mcp gateway.

All parameters are configured via environment variables prefixed with
``VTK_MCP_``.  For example: ``VTK_MCP_TRANSPORT=http``.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Layer 1 — knowledge artifact
    # When None, the artifact is downloaded automatically via VTKAPIIndex.from_artifact().
    knowledge_artifact_path: Optional[Path] = None
    vtk_version: str = "9.3.0"

    # Layer 2 — retrieval
    # When enable_retrieval is True and vtk_version is set, uses Retriever.from_artifact()
    # which downloads pre-built embedded Qdrant storage (no server required).
    # Set qdrant_url to a real Qdrant instance to use a server instead.
    enable_retrieval: bool = False
    qdrant_url: Optional[str] = None

    # Layer 3 — validation
    enable_validation: bool = True

    # Transport
    transport: str = "stdio"
    http_host: str = "0.0.0.0"
    http_port: int = 8000

    # C++ docs scraping
    enable_cpp_scraping: bool = True
    vtk_docs_base_url: str = "https://vtk.org/doc/nightly/html/"

    class Config:
        env_prefix = "VTK_MCP_"
