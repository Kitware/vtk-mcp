LABEL org.opencontainers.image.title="VTK MCP Embeddings Database"
LABEL org.opencontainers.image.description="Vector search embeddings database for VTK examples"
LABEL org.opencontainers.image.source="https://github.com/kitware/vtk-mcp"
LABEL org.opencontainers.image.authors="Vicente Adolfo Bolea Sanchez <vicente.bolea@kitware.com>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/kitware/vtk-mcp/blob/main/README.md"

FROM scratch

COPY vtk-examples-embeddings.tar.gz /
