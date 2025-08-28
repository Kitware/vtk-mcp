LABEL org.opencontainers.image.title="VTK MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for VTK class documentation"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.authors="Vicente Adolfo Bolea Sanchez <vicente.bolea@kitware.com>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/kitware/vtk-mcp/blob/main/README.md"

FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for VTK
RUN apt update && \
    apt install --no-install-recommends --no-install-suggests -y \
    libgl1-mesa-dev \
    libxrender-dev/stable

WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install --verbose .

EXPOSE 8000

CMD ["vtk-mcp-server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
