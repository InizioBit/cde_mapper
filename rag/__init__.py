"""CDE-Mapper RAG package.

Keep package import lightweight. Import concrete modules directly, for example:

    from rag.data_loader import load_data
    from rag.retriever import map_data

The previous package initializer imported the full retrieval and LLM stack on
`import rag`, which made reproducibility checks fail when GPU devices or LLM
credentials were unavailable.
"""

from .param import *  # noqa: F403

