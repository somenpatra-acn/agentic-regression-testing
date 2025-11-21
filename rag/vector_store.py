"""Vector store management for RAG."""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from config.settings import get_settings
from rag.embeddings import EmbeddingsManager
from utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    """Manage vector store for test knowledge base."""

    def __init__(self, collection_name: str = "test_knowledge"):
        """
        Initialize vector store manager.

        Args:
            collection_name: Name of the vector store collection
        """
        self.settings = get_settings()
        self.collection_name = collection_name
        self.embeddings_manager = EmbeddingsManager()

        self.store_dir = self.settings.knowledge_base_dir / "vector_store"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.vector_store: Optional[VectorStore] = None

        # Load existing store or create new one
        self._load_or_create_store()

        logger.info(f"VectorStoreManager initialized for collection: {collection_name}")

    def _load_or_create_store(self) -> None:
        """Load existing vector store or create a new one."""
        store_path = self.store_dir / f"{self.collection_name}.faiss"

        if store_path.exists():
            try:
                self.vector_store = FAISS.load_local(
                    str(self.store_dir),
                    self.embeddings_manager.get_embeddings(),
                    self.collection_name,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded existing vector store from {store_path}")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}. Creating new one.")
                self.vector_store = None

        if self.vector_store is None:
            # Create empty store with a dummy document
            dummy_doc = Document(
                page_content="Initialization document",
                metadata={"type": "init"}
            )
            self.vector_store = FAISS.from_documents(
                [dummy_doc],
                self.embeddings_manager.get_embeddings()
            )
            logger.info("Created new vector store")

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to vector store.

        Args:
            documents: List of Document objects

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        try:
            ids = self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return []

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Add texts to vector store.

        Args:
            texts: List of text strings
            metadatas: Optional list of metadata dicts

        Returns:
            List of document IDs
        """
        if not texts:
            return []

        try:
            ids = self.vector_store.add_texts(texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} texts to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding texts: {e}")
            return []

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar documents
        """
        try:
            results = self.vector_store.similarity_search(
                query,
                k=k,
                filter=filter
            )
            logger.debug(f"Similarity search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of (document, score) tuples
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter
            )
            logger.debug(f"Similarity search with score returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            return []

    def save(self) -> None:
        """Save vector store to disk."""
        try:
            self.vector_store.save_local(
                str(self.store_dir),
                self.collection_name
            )
            logger.info(f"Vector store saved to {self.store_dir}")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def delete_collection(self) -> None:
        """Delete the vector store collection."""
        store_path = self.store_dir / f"{self.collection_name}.faiss"
        if store_path.exists():
            store_path.unlink()
            logger.info(f"Deleted vector store: {self.collection_name}")

    def get_store(self) -> VectorStore:
        """
        Get the underlying vector store.

        Returns:
            VectorStore instance
        """
        return self.vector_store

    def as_retriever(self, **kwargs) -> Any:
        """
        Get vector store as a retriever.

        Args:
            **kwargs: Arguments to pass to as_retriever()

        Returns:
            Retriever instance
        """
        return self.vector_store.as_retriever(**kwargs)
