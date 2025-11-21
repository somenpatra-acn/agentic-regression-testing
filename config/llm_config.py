"""LLM configuration and initialization."""

from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from config.settings import get_settings


class LLMConfig:
    """LLM configuration manager."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM config."""
        self.settings = get_settings()
        self.provider = provider or self.settings.llm_provider
        self.model = model or self.settings.llm_model

    def get_llm(self, temperature: Optional[float] = None) -> BaseChatModel:
        """Get configured LLM instance."""
        temp = temperature if temperature is not None else self.settings.llm_temperature

        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model,
                temperature=temp,
                api_key=self.settings.openai_api_key,
            )
        elif self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=self.model,
                    temperature=temp,
                    api_key=self.settings.anthropic_api_key,
                )
            except ImportError:
                raise ImportError(
                    "Anthropic support requires langchain-anthropic. "
                    "Install with: pip install langchain-anthropic"
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def get_fast_llm(self) -> BaseChatModel:
        """Get a fast LLM for simple tasks."""
        if self.provider == "openai":
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.0,
                api_key=self.settings.openai_api_key,
            )
        elif self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model="claude-3-haiku-20240307",
                    temperature=0.0,
                    api_key=self.settings.anthropic_api_key,
                )
            except ImportError:
                # Fallback to main LLM
                return self.get_llm(temperature=0.0)
        return self.get_llm(temperature=0.0)

    def get_smart_llm(self) -> BaseChatModel:
        """Get the most capable LLM for complex tasks."""
        if self.provider == "openai":
            return ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key,
            )
        elif self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model="claude-3-opus-20240229",
                    temperature=self.settings.llm_temperature,
                    api_key=self.settings.anthropic_api_key,
                )
            except ImportError:
                return self.get_llm()
        return self.get_llm()


@lru_cache()
def get_llm(provider: Optional[str] = None, model: Optional[str] = None) -> BaseChatModel:
    """Get cached LLM instance."""
    config = LLMConfig(provider, model)
    return config.get_llm()


@lru_cache()
def get_fast_llm() -> BaseChatModel:
    """Get cached fast LLM instance."""
    config = LLMConfig()
    return config.get_fast_llm()


@lru_cache()
def get_smart_llm() -> BaseChatModel:
    """Get cached smart LLM instance."""
    config = LLMConfig()
    return config.get_smart_llm()
