import os

import yaml

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
