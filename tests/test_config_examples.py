from pathlib import Path

import yaml

from oceangraph.core.config import load_config


def test_recommended_config_routes_glm_with_stage_reasoning():
    config_path = Path(__file__).parents[1] / "configs" / "oceangraph.yaml.example"
    raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = load_config(str(config_path))
    profiles = config["models"]["profiles"]

    assert raw_config["llm_config_file"] == "configs/llm.yaml"
    assert "models" not in raw_config
    assert config["framework"]["version"] == "4.0.0"
    assert config["framework"]["agents"] == [
        "corpus",
        "evidence",
        "qa",
        "verifier",
    ]
    assert profiles["generator"]["url"] == (
        "https://llmapi.paratera.com/v1/chat/completions"
    )
    assert profiles["generator"]["api_key_env"] == "OPENAI_API_KEY"
    assert profiles["generator"]["model"] == "GLM-5.3"
    assert profiles["generator"]["max_output_tokens"] == 32768
    assert profiles["generator"].get("thinking") is None
    assert profiles["generator"]["extra_body"] == {
        "thinking": {"type": "enabled"}, "reasoning_effort": "low",
    }
    assert config["pipeline"]["modality"] == "text"
    assert profiles["generator"]["supports_vision"] is False
    assert profiles["verifier"]["url"] == (
        "https://llmapi.paratera.com/v1/chat/completions"
    )
    assert profiles["verifier"]["api_key_env"] == "OPENAI_API_KEY"
    assert profiles["verifier"]["model"] == "GLM-5.3"
    assert profiles["verifier"].get("thinking") is None
    assert profiles["verifier"]["extra_body"] == {
        "thinking": {"type": "enabled"}, "reasoning_effort": "high",
    }
    assert profiles["verifier"]["max_output_tokens"] == 32768
    assert config["processing"]["max_pdfs"] is None
    assert config["chunking"] == {"window_size": 8000, "overlap_size": 800}
    assert config["evaluation"]["run_evaluation"] is False
    assert config["evaluation"]["judge_stage"] == "verification"
    assert config["evaluation"]["embedding_backend"] == "local"
    assert config["evaluation"]["embedding_model"] == "BAAI/bge-m3"
    assert config["training_export"]["split"] is None
    assert config["training_export"]["split_ratios"] == {
        "train": 0.8,
        "dev": 0.1,
        "test": 0.1,
    }
    assert config["preflight"]["check_timeout_seconds"] == 180
    assert config["preflight"]["api_probe_cache_ttl_seconds"] == 3600


def test_recommended_config_uses_cost_bounded_verification():
    config_path = Path(__file__).parents[1] / "configs" / "oceangraph.yaml.example"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    qa_config = config["qa_generation"]

    assert qa_config["model_selection"] is False
    assert qa_config["verification_profile"] == "cost_efficient"
    assert qa_config["max_answer_words"] == 12
    assert qa_config["max_answer_cjk_chars"] == 16
    assert qa_config["multihop_verification_mode"] == "balanced"
    assert qa_config["max_verification_chunks"] == 4
    assert qa_config["max_unknown_verdicts"] == 1
    assert qa_config["counterfactual_verification"] is False
    assert config["qa_correction"] == {"enabled": False, "max_attempts": 0}


def test_llm_file_is_the_only_recommended_model_edit_location():
    root = Path(__file__).parents[1]
    config = yaml.safe_load((root / "configs" / "llm.yaml").read_text(encoding="utf-8"))

    assert config["models"]["stages"]["generation"] == "generator"
    assert config["models"]["stages"]["verification"] == "verifier"
    assert config["models"]["profiles"]["generator"]["api_key_env"] == "OPENAI_API_KEY"
    assert config["models"]["profiles"]["verifier"]["api_key_env"] == "OPENAI_API_KEY"
    assert "api_key" not in config["models"]["profiles"]["generator"]


def test_normalized_corpus_profile_matches_server_safe_defaults():
    root = Path(__file__).parents[1]
    profile_path = root / "configs" / "normalized_corpus.yaml.example"
    profile = yaml.safe_load(
        profile_path.read_text(encoding="utf-8")
    )
    resolved = load_config(str(profile_path))

    assert profile["paths"]["input_pdf_dir"] == "data/normalized"
    assert profile["paths"]["output_dir"] == "output/normalized_dataset"
    assert profile["processing"]["max_pdfs"] is None
    assert profile["chunking"] == {"window_size": 8000, "overlap_size": 800}
    assert profile["embedding"]["local_files_only"] is True
    assert profile["faiss"]["use_gpu"] is False
    assert resolved["models"]["profiles"]["generator"]["model"] == "GLM-5.3"
    assert resolved["models"]["profiles"]["verifier"]["model"] == "GLM-5.3"
