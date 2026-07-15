from pathlib import Path

import yaml


def test_recommended_config_routes_qwen_and_deepseek():
    config_path = Path(__file__).parents[1] / "configs" / "oceangraph.yaml.example"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    profiles = config["models"]["profiles"]

    assert profiles["generator"]["url"] == (
        "https://llmapi.paratera.com/v1/chat/completions"
    )
    assert profiles["generator"]["api_key_env"] == "PARATERA_API_KEY"
    assert profiles["generator"]["model"] == "Qwen3.7-Plus"
    assert config["pipeline"]["modality"] == "text"
    assert profiles["generator"]["supports_vision"] is False
    assert profiles["verifier"]["url"] == "https://api.deepseek.com/chat/completions"
    assert profiles["verifier"]["api_key_env"] == "DEEPSEEK_API_KEY"
    assert profiles["verifier"]["model"] == "deepseek-v4-pro"
    assert config["evaluation"]["run_evaluation"] is False
    assert config["evaluation"]["judge_stage"] == "verification"
    assert config["evaluation"]["embedding_backend"] == "local"
    assert config["evaluation"]["embedding_model"] == "BAAI/bge-m3"
