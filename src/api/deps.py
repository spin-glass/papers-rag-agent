from __future__ import annotations
from api.core.rag_index import RagIndexHolder

_holder = RagIndexHolder()


def get_index_holder() -> RagIndexHolder:
    return _holder
