"""
NAYA SUPREME V19 — VectorDBIntegration shim
Re-exports from the actual implementation at memory/vector_db/.
Provides VectorDBIntegration as alias for VectorDatabaseManager.
"""
from NAYA_CORE.memory.vector_db.vector_db_integration import (
    VectorDatabaseManager as VectorDBIntegration,
    EmbeddingGenerator,
    PineconeIndexManager,
    ProspectVectorStore,
    ConversationMemory,
    SemanticSearchEngine,
)

__all__ = [
    "VectorDBIntegration",
    "EmbeddingGenerator",
    "PineconeIndexManager",
    "ProspectVectorStore",
    "ConversationMemory",
    "SemanticSearchEngine",
]
