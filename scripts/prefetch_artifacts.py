"""Pre-fetch vtk-knowledge and vtk-index artifacts into the local cache.

Run during image build so the container serves requests without network access.
"""

import logging
import os

logging.basicConfig(level=logging.INFO)

vtk_version = os.environ["VTK_MCP_VTK_VERSION"]

try:
    from vtk_knowledge import VTKAPIIndex

    VTKAPIIndex.from_artifact(vtk_version)
    logging.info("vtk-knowledge artifact cached for %s", vtk_version)
except Exception as e:
    logging.warning("vtk-knowledge artifact not cached (will download at runtime): %s", e)

try:
    from vtk_index import Retriever

    Retriever.from_artifact(vtk_version)
    logging.info("vtk-index embedded storage cached for %s", vtk_version)
except Exception as e:
    logging.warning("vtk-index embedded storage not cached (will download at runtime): %s", e)
