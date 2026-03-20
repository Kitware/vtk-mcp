FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# VTK requires OpenGL libraries at introspection time
RUN apt-get update && \
    apt-get install --no-install-recommends --no-install-suggests -y \
        libgl1-mesa-dev \
        libxrender1 \
        git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install vtk-data with extraction dependencies (VTK + LiteLLM)
RUN pip install "vtk-data[extract] @ git+https://github.com/vicentebolea/vtk-data.git"

# Build the VTK API docs database.
# Requires an LLM API key as a build secret (used by vtk-data extract for enrichment).
# Output: /build/docs/vtk-python-docs.jsonl
RUN --mount=type=secret,id=llm_api_key \
    export OPENAI_API_KEY=$(cat /run/secrets/llm_api_key) && \
    vtk-data extract --output /build


FROM python:3.12-slim

LABEL org.opencontainers.image.title="VTK MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for VTK documentation"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.licenses="MIT"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VTK_DATA_PATH=/app/data/vtk-python-docs.jsonl

RUN apt-get update && \
    apt-get install --no-install-recommends --no-install-suggests -y git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install vtk-mcp and vtk-data[rag] (Qdrant retriever)
COPY . .
RUN pip install --upgrade pip && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "vtk-data[rag] @ git+https://github.com/vicentebolea/vtk-data.git" && \
    pip install .

# Copy the pre-built VTK API docs database from builder stage
RUN mkdir -p /app/data
COPY --from=builder /build/docs/vtk-python-docs.jsonl /app/data/vtk-python-docs.jsonl

CMD ["vtk-mcp-server", \
     "--transport", "http", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--data-path", "/app/data/vtk-python-docs.jsonl"]
