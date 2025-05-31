import os
from typing import Dict, List

# Model configurations
USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"

# OpenAI models
OPENAI_MODELS = {
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "gpt-4": "gpt-4",
    "gpt-4-turbo": "gpt-4-turbo-preview"
}

# Ollama models
OLLAMA_MODELS = {
    # "llama2": "llama2",
    # "mistral": "mistral",
    "gemma": "gemma3:27b"
}

# Embedding models
EMBEDDING_MODELS = {
    "openai": "text-embedding-3-large",
    "ollama": "mxbai-embed-large:latest"
}

def get_available_models() -> Dict[str, List[str]]:
    """Get available models based on configuration"""
    if USE_OPENAI:
        return {
            "chat": list(OPENAI_MODELS.keys()),
            "embedding": [EMBEDDING_MODELS["openai"]]
        }
    else:
        return {
            "chat": list(OLLAMA_MODELS.keys()),
            "embedding": [EMBEDDING_MODELS["ollama"]]
        }

def get_model_name(model_id: str) -> str:
    """Get the actual model name based on model ID"""
    if USE_OPENAI:
        return OPENAI_MODELS.get(model_id, "gpt-3.5-turbo")
    else:
        return OLLAMA_MODELS.get(model_id, "gemma3:27b")

def get_embedding_model() -> str:
    """Get the embedding model based on configuration"""
    if USE_OPENAI:
        return EMBEDDING_MODELS["openai"]
    else:
        return EMBEDDING_MODELS["ollama"] 