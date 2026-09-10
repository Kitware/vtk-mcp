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

    # Layer 2 — retrieval (always attempted; silently disabled if vtk-index not installed)
    # Set qdrant_url to a running Qdrant server; if unset, uses embedded storage from ghcr.io.
    qdrant_url: Optional[str] = None

    # Layer 3 — validation
    enable_validation: bool = True

    # Transport
    transport: str = "stdio"
    http_host: str = "0.0.0.0"
    http_port: int = 8000

    class Config:
        env_prefix = "VTK_MCP_"
