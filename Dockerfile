FROM python:3.11-slim

LABEL org.opencontainers.image.title="VTK MCP Gateway"
LABEL org.opencontainers.image.description="Production MCP gateway for VTK LLM tooling"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.licenses="MIT"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies — no VTK runtime, no LiteLLM
RUN pip install vtk-knowledge vtk-validate vtk-mcp

# Bundle the knowledge artifact (built separately and passed at build time)
ARG VTK_VERSION=9.3.0
ARG KNOWLEDGE_ARTIFACT_URL=""
RUN if [ -n "$KNOWLEDGE_ARTIFACT_URL" ]; then \
    curl -fSL "$KNOWLEDGE_ARTIFACT_URL" -o /app/data/vtk-knowledge.jsonl; \
    fi

COPY data/ /app/data/

ENV VTK_MCP_KNOWLEDGE_ARTIFACT_PATH=/app/data/vtk-knowledge.jsonl
ENV VTK_MCP_VTK_VERSION=${VTK_VERSION}
ENV VTK_MCP_TRANSPORT=stdio

ENTRYPOINT ["python", "-m", "vtk_mcp"]
