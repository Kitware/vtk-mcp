# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="VTK MCP Gateway"
LABEL org.opencontainers.image.description="Production MCP gateway for VTK LLM tooling"
LABEL org.opencontainers.image.source="https://github.com/Kitware/vtk-mcp"
LABEL org.opencontainers.image.licenses="MIT"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# VTK version to pre-cache at image build time
ARG VTK_VERSION=9.3.0
ENV VTK_MCP_VTK_VERSION=${VTK_VERSION}

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

# Install vtk-* sibling packages from GitHub (not on PyPI)
RUN uv pip install --system \
    "git+https://github.com/vicentebolea/vtk-knowledge" \
    "git+https://github.com/vicentebolea/vtk-validate"

# Install vtk-mcp with optional retrieval support
COPY . /app/
RUN uv pip install --system -e ".[retrieval]"

# Pre-download the vtk-knowledge JSONL artifact and vtk-index embedded
# Qdrant storage so the image is ready to serve without network access.
RUN python - <<'EOF'
import logging
logging.basicConfig(level=logging.INFO)
import os
vtk_version = os.environ["VTK_MCP_VTK_VERSION"]
from vtk_knowledge import VTKAPIIndex
VTKAPIIndex.from_artifact(vtk_version)
try:
    from vtk_index import Retriever
    Retriever.from_artifact(vtk_version)
except Exception as e:
    logging.warning("vtk-index embedded storage skipped: %s", e)
EOF

ENV VTK_MCP_TRANSPORT=stdio
ENV VTK_MCP_ENABLE_VALIDATION=true
ENV VTK_MCP_ENABLE_RETRIEVAL=true

ENTRYPOINT ["python", "-m", "vtk_mcp"]
