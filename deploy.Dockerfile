ARG DATABASE_IMAGE=ghcr.io/vicentebolea/vtk-data-database:latest

FROM ${DATABASE_IMAGE} AS database

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

# Two modes, controlled by build arg:
#
#   SKIP_EXTRACT=false (default)
#     Runs vtk-data extract. Requires --secret id=llm_api_key.
#     Build command:
#       podman build --secret id=llm_api_key,src=~/.llm_api_key -f deploy.Dockerfile .
#
#   SKIP_EXTRACT=true
#     Copies vtk-python-docs.jsonl from the pre-built database image.
#     Build command:
#       podman build --build-arg SKIP_EXTRACT=true -f deploy.Dockerfile .
ARG SKIP_EXTRACT=false

COPY --from=database /vtk-python-docs.jsonl /build/docs/vtk-python-docs.jsonl.cached

RUN --mount=type=secret,id=llm_api_key,required=false \
    if [ "$SKIP_EXTRACT" = "true" ]; then \
        echo "Using existing database from image..." && \
        cp /build/docs/vtk-python-docs.jsonl.cached /build/docs/vtk-python-docs.jsonl; \
    else \
        export OPENAI_API_KEY=$(cat /run/secrets/llm_api_key 2>/dev/null || true) && \
        vtk-data extract --output /build; \
    fi


FROM python:3.12-slim

LABEL org.opencontainers.image.title="VTK MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for VTK documentation"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.licenses="MIT"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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

COPY --from=builder /build/docs/vtk-python-docs.jsonl /app/data/vtk-python-docs.jsonl

CMD ["vtk-mcp-server", \
     "--transport", "http", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--data-path", "/app/data/vtk-python-docs.jsonl"]
