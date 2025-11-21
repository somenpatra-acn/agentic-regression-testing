"""Embeddings management for RAG."""

from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingsManager:
    """Manage embeddings for RAG system."""

    def __init__(self):
        """Initialize embeddings manager."""
        self.settings = get_settings()
        self.embeddings = self._create_embeddings()

        logger.info(f"EmbeddingsManager initialized with model: {self.settings.embedding_model}")

    def _create_embeddings(self) -> Embeddings:
        """Create embeddings instance based on configuration."""
        if self.settings.llm_provider == "openai":
            return OpenAIEmbeddings(
                model=self.settings.embedding_model,
                openai_api_key=self.settings.openai_api_key,
            )
        elif self.settings.llm_provider == "anthropic":
            # Anthropic doesn't provide embeddings, fall back to OpenAI
            logger.warning("Anthropic doesn't provide embeddings, using OpenAI embeddings")
            if self.settings.openai_api_key:
                return OpenAIEmbeddings(
                    model=self.settings.embedding_model,
                    openai_api_key=self.settings.openai_api_key,
                )
            else:
                raise ValueError(
                    "OpenAI API key required for embeddings when using Anthropic"
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")

    def get_embeddings(self) -> Embeddings:
        """
        Get embeddings instance.

        Returns:
            Embeddings instance
        """
        return self.embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.

        Args:
            texts: List of text documents

        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text

        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)
