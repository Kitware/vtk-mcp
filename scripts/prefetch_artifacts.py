"""Pre-fetch vtk-knowledge and vtk-index artifacts into the local cache.

Run during image build so the container serves requests without network access.
"""

import logging
import os

logging.basicConfig(level=logging.INFO)

vtk_version = os.environ["VTK_MCP_VTK_VERSION"]

from vtk_knowledge import VTKAPIIndex

VTKAPIIndex.from_artifact(vtk_version)

try:
    from vtk_index import Retriever

    Retriever.from_artifact(vtk_version)
except Exception as e:
    logging.warning("vtk-index embedded storage skipped: %s", e)
