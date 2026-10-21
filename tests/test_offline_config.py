import os

import yaml
import pytest

from oceangraph.core.config import load_config


def test_local_files_only_enables_transformer_offline_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("TRANSFORMERS_OFFLINE", raising=False)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"embedding": {"local_files_only": True}}),
        encoding="utf-8",
    )

    config = load_config(str(config_path))

    assert config["embedding"]["local_files_only"] is True
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"


@pytest.mark.parametrize("fallback", [False, True])
def test_runtime_embedding_loader_enforces_offline_for_every_attempt(monkeypatch, fallback):
    from oceangraph import engine
    from oceangraph.utils import device
    import sentence_transformers
    attempts = []

    def load(name, **kwargs):
        attempts.append((name, kwargs))
        if fallback and len(attempts) == 1:
            raise RuntimeError("CPU loading unavailable")
        return object()

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", load)
    monkeypatch.setattr(device, "get_device", lambda: "cpu")
    monkeypatch.setattr(engine, "get_embedding_config", lambda: {"local_files_only": True})

    engine._load_sentence_transformer("BAAI/bge-m3")

    assert len(attempts) == (2 if fallback else 1)
    assert all(kwargs.get("local_files_only") is True for _, kwargs in attempts)


def test_text_reranker_enforces_offline_loading(monkeypatch):
    from oceangraph.core import config
    from oceangraph.embeddings import rerankers
    import sentence_transformers
    captured = {}

    def load(name, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(config, "get_embedding_config", lambda: {"local_files_only": True})
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", load)
    monkeypatch.setattr(rerankers, "get_device", lambda: "cpu")

    rerankers.TextEmbeddingReranker()

    assert captured.get("local_files_only") is True
