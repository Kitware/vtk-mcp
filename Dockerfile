LABEL org.opencontainers.image.title="VTK MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for VTK class documentation"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/kitware/vtk-mcp/blob/main/README.md"

FROM python:3.12-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for VTK
RUN apt update && apt install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev

COPY . .
RUN pip install --upgrade pip && \
    pip install --verbose .

# Create non-root user for security
#RUN useradd --create-home --shell /bin/bash --uid 1000 vtk-user && \
#    chown -R vtk-user:vtk-user /app
#USER vtk-user

EXPOSE 8000

CMD ["vtk-mcp-server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
