LABEL org.opencontainers.image.title="VTK MCP Server with Embeddings"
LABEL org.opencontainers.image.description="Model Context Protocol server for VTK with vector search embeddings"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.authors="Vicente Adolfo Bolea Sanchez <vicente.bolea@kitware.com>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/kitware/vtk-mcp/blob/main/README.md"

FROM python:3.12-slim AS embeddings

# Download embeddings database from GHCR
COPY --from=ghcr.io/kitware/vtk-mcp/embeddings-database:latest /vtk-examples-embeddings.tar.gz /tmp/

# Extract the database
RUN mkdir -p /app/db && \
    tar -xzf /tmp/vtk-examples-embeddings.tar.gz -C /app/db && \
    rm /tmp/vtk-examples-embeddings.tar.gz

FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for VTK
RUN apt update && \
    apt install --no-install-recommends --no-install-suggests -y \
    libgl1-mesa-dev \
    libxrender-dev/stable \
    git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application code
COPY . .

# Copy embeddings database from first stage
COPY --from=embeddings /app/db /app/db

# Install Python dependencies (including RAG dependencies)
RUN pip install --upgrade pip && \
    pip install --verbose .

# Start server with database path configured
CMD ["vtk-mcp-server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "--database-path", "/app/db/vtk-examples"]
