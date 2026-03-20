FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install --no-install-recommends --no-install-suggests -y git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Install CPU-only torch first to avoid pulling CUDA packages
RUN pip install --upgrade pip && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "vtk-data[rag] @ git+https://github.com/vicentebolea/vtk-data.git" && \
    pip install .

COPY vtk-python-docs.jsonl /app/data/vtk-python-docs.jsonl

CMD ["vtk-mcp-server", \
     "--transport", "http", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--data-path", "/app/data/vtk-python-docs.jsonl"]
