"""
Evaluation module for OceanGraph - Metrics and dataset evaluation.

Imports are lazy to avoid loading optional dependencies at import time.
"""

_LAZY_IMPORTS = {
    "LocalEmbeddingWrapper": ("metrics", "LocalEmbeddingWrapper"),
    "RoutedMetricsEvaluator": ("metrics", "RoutedMetricsEvaluator"),
    "run_pipeline_evaluation": ("metrics", "run_pipeline_evaluation"),
}


def __getattr__(name):
    """Lazy import to avoid loading optional dependencies at import time."""
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        import importlib
        module = importlib.import_module(f"oceangraph.evaluation.{module_name}")
        return getattr(module, attr_name)
    raise AttributeError(f"module 'oceangraph.evaluation' has no attribute '{name}'")
