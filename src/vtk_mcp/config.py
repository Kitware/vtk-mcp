"""Pydantic Settings for the vtk-mcp gateway.

All parameters are configured via environment variables prefixed with
``VTK_MCP_``.  For example: ``VTK_MCP_TRANSPORT=http``.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Layer 1 — knowledge artifact
    knowledge_artifact_path: Path = Path("/app/data/vtk-knowledge.jsonl")
    vtk_version: str = "9.3.0"

    # Layer 2 — retrieval
    enable_retrieval: bool = True
    qdrant_url: str = "http://qdrant:6333"

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
