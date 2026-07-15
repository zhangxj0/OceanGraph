"""
Core module for OceanGraph - LLM/VLM interfaces, prompts, and configuration.

Imports are lazy to allow the package to be imported without a config file.
"""


def __getattr__(name):
    """Lazy import to avoid import-time config loading."""
    # LLM functions
    if name in ("call_llm_simple", "call_vlm_interweaved", "call_vlm_with_multiple_images",
                "batch_call_vlm_interweaved", "setup_logging", "test_llm_connection",
                "test_vlm_connection", "BACKEND", "LLM_MODEL_NAME", "VLM_MODEL_NAME",
                "GEMINI_RPM", "GEMINI_BURST", "get_token_stats", "reset_token_stats",
                "print_token_stats"):
        from oceangraph.core import llm
        return getattr(llm, name)
    
    # Prompts
    if name in ("PROMPTS", "PROMPTS_CHUNK"):
        from oceangraph.core import prompts
        return getattr(prompts, name)
    
    # Config
    if name in ("load_config", "get_config_value", "ConfigLoader"):
        from oceangraph.core import config
        return getattr(config, name)
    
    raise AttributeError(f"module 'oceangraph.core' has no attribute '{name}'")


__all__ = [
    # LLM functions
    "call_llm_simple",
    "call_vlm_interweaved",
    "call_vlm_with_multiple_images",
    "batch_call_vlm_interweaved",
    "setup_logging",
    "test_llm_connection",
    "test_vlm_connection",
    "BACKEND",
    "LLM_MODEL_NAME",
    "VLM_MODEL_NAME",
    "GEMINI_RPM",
    "GEMINI_BURST",
    # Token tracking
    "get_token_stats",
    "reset_token_stats",
    "print_token_stats",
    # Prompts
    "PROMPTS",
    "PROMPTS_CHUNK",
    # Config
    "load_config",
    "get_config_value",
    "ConfigLoader",
]
