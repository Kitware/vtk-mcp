"""Integration tests for vector search with RAG database."""

import pytest
import asyncio
import time
import threading
import socket
import subprocess
import tarfile
import shutil
from pathlib import Path
from vtk_mcp_server.simple_client import SimpleVTKClient

pytestmark = [pytest.mark.integration, pytest.mark.vector_search]


@pytest.fixture(scope="module")
def embeddings_database(tmp_path_factory):
    """Download and extract embeddings database from container image or use local."""
    # First check if we have a local database
    local_db = Path(__file__).parent.parent / "db" / "vtk-examples"
    if local_db.exists() and (local_db / "chroma.sqlite3").exists():
        yield str(local_db)
        return

    tmpdir = tmp_path_factory.mktemp("embeddings")
    db_path = tmpdir / "db" / "vtk-examples"
    tarball_path = tmpdir / "vtk-examples-embeddings.tar.gz"

    try:
        # Check if podman is available
        subprocess.run(
            ["podman", "--version"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Podman not available and no local database found")

    try:
        # Create temporary container to extract database
        container_name = "vtk-embeddings-test"
        image_name = "ghcr.io/kitware/vtk-mcp/embeddings-database:latest"

        # Pull the image
        subprocess.run(
            ["podman", "pull", image_name],
            check=True,
            capture_output=True,
        )

        # Create container
        subprocess.run(
            ["podman", "create", "--name", container_name, image_name],
            check=True,
            capture_output=True,
        )

        # Copy tarball from container
        subprocess.run(
            [
                "podman",
                "cp",
                f"{container_name}:/vtk-examples-embeddings.tar.gz",
                str(tarball_path),
            ],
            check=True,
            capture_output=True,
        )

        # Remove container
        subprocess.run(
            ["podman", "rm", container_name],
            check=True,
            capture_output=True,
        )

        # Extract tarball
        tmpdir.joinpath("db").mkdir(parents=True, exist_ok=True)
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(path=tmpdir / "db")

        # Verify database exists
        if not db_path.exists():
            pytest.skip(f"Database not found at {db_path}")

        yield str(db_path)

    except subprocess.CalledProcessError as e:
        pytest.skip(f"Failed to extract embeddings database: {e}")
    finally:
        # Cleanup
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def vector_search_server(embeddings_database):
    """Start HTTP server with vector search enabled."""
    # Import here to set database path before server starts
    from vtk_mcp_server import server

    # Set the database path globally
    server._database_path = embeddings_database

    # Find a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    server_thread = None
    server_started = threading.Event()

    def run_server():
        try:
            # Run server with database path configured
            asyncio.run(server.mcp.run_http_async(host="127.0.0.1", port=port))
        except Exception:
            pass  # Server might be stopped
        finally:
            server_started.set()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(1.0)

    yield f"http://127.0.0.1:{port}"

    # Cleanup - server thread will die when test ends due to daemon=True


class TestVectorSearchIntegration:
    """Test vector search functionality end-to-end."""

    def test_vector_search_red_sphere(self, vector_search_server):
        """Test vector search for 'a red vtkSphere'."""
        client = SimpleVTKClient(base_url=vector_search_server)

        # Call vector search
        payload = {
            "jsonrpc": "2.0",
            "id": "vector-search-test",
            "method": "tools/call",
            "params": {
                "name": "vector_search_vtk_examples",
                "arguments": {
                    "query": "a red vtkSphere",
                    "collection_name": "vtk-examples",
                    "top_k": 5,
                },
            },
        }

        response = client._make_request(payload)
        assert response is not None, "Vector search request failed"
        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

        result = client._parse_response(response)
        assert result is not None, "Failed to parse response"
        assert "result" in result, "No result in response"
        assert "content" in result["result"], "No content in result"

        content = result["result"]["content"][0]["text"]
        assert content is not None, "Empty response content"
        assert "Vector Search Results" in content, "Unexpected response format"
        assert "vtk" in content.lower(), "Results don't mention VTK"

        # Verify we got actual results
        assert "Code Examples" in content or "Documentation Snippets" in content, (
            "No code examples or documentation found"
        )

    def test_vector_search_with_different_top_k(self, vector_search_server):
        """Test vector search with different top_k values."""
        client = SimpleVTKClient(base_url=vector_search_server)

        payload = {
            "jsonrpc": "2.0",
            "id": "vector-search-topk",
            "method": "tools/call",
            "params": {
                "name": "vector_search_vtk_examples",
                "arguments": {
                    "query": "render a sphere",
                    "collection_name": "vtk-examples",
                    "top_k": 3,
                },
            },
        }

        response = client._make_request(payload)
        assert response is not None
        assert response.status_code == 200

        result = client._parse_response(response)
        assert result is not None
        assert "result" in result

        content = result["result"]["content"][0]["text"]
        assert "Found 3 most relevant" in content, "Expected 3 results"

    def test_vector_search_query_variations(self, vector_search_server):
        """Test vector search with various queries."""
        client = SimpleVTKClient(base_url=vector_search_server)

        test_queries = [
            "read DICOM files",
            "create a cylinder",
            "texture mapping",
        ]

        for query in test_queries:
            payload = {
                "jsonrpc": "2.0",
                "id": f"query-{query}",
                "method": "tools/call",
                "params": {
                    "name": "vector_search_vtk_examples",
                    "arguments": {
                        "query": query,
                        "top_k": 2,
                    },
                },
            }

            response = client._make_request(payload)
            assert response is not None, f"Query '{query}' failed"
            assert response.status_code == 200

            result = client._parse_response(response)
            assert result is not None
            assert "result" in result

            content = result["result"]["content"][0]["text"]
            assert "Vector Search Results" in content
