import pytest

from oceangraph.core.llm import (
    _extract_openai_response_text,
    _requeue_invalid_cache_entries,
)
from oceangraph.providers import StageModelRouter


def test_stage_router_selects_generator_and_verifier(monkeypatch):
    monkeypatch.setenv("PARATERA_API_KEY", "qwen-secret")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-secret")
    config = {
        "models": {
            "profiles": {
                "generator": {
                    "backend": "OPENAI",
                    "url": "https://example.test/qwen/chat/completions",
                    "api_key_env": "PARATERA_API_KEY",
                    "model": "Qwen3.7-Plus",
                    "supports_vision": False,
                    "thinking": False,
                    "structured_output": True,
                },
                "verifier": {
                    "backend": "OPENAI",
                    "url": "https://example.test/deepseek/chat/completions",
                    "api_key_env": "DEEPSEEK_API_KEY",
                    "model": "deepseek-v4-pro",
                },
            }
        }
    }

    router = StageModelRouter.from_config(
        config,
        fallback_backend="OPENAI",
        fallback_url="https://example.test/default",
        fallback_llm_model="fallback-text",
        fallback_vlm_model="fallback-vision",
    )

    generator = router.resolve("generation")
    verifier = router.resolve("verification")
    assert generator.model == "Qwen3.7-Plus"
    assert verifier.model == "deepseek-v4-pro"
    assert generator.supports_vision is False
    assert generator.headers["Authorization"] == "Bearer qwen-secret"
    assert verifier.headers["Authorization"] == "Bearer deepseek-secret"
    assert router.has_api_key() is True


def test_openai_payload_only_enables_supported_structured_output():
    router = StageModelRouter.from_config(
        {
            "models": {
                "profiles": {
                    "generator": {
                        "backend": "OPENAI",
                        "url": "https://example.test/chat/completions",
                        "model": "qwen3.7-plus",
                        "thinking": False,
                        "structured_output": True,
                    }
                }
            }
        },
        fallback_backend="OPENAI",
        fallback_url="https://example.test/default",
        fallback_llm_model="fallback-text",
        fallback_vlm_model="fallback-vision",
    )
    profile = router.resolve("generation")
    payload = profile.openai_payload(
        [{"role": "user", "content": "return JSON"}],
        response_format={"type": "json_object"},
    )

    assert payload["response_format"] == {"type": "json_object"}
    assert payload["enable_thinking"] is False
    assert "api_key" not in payload


def test_openai_response_extractor_rejects_reasoning_only_success():
    payload = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": "", "reasoning_content": "hidden reasoning"},
            }
        ]
    }

    with pytest.raises(ValueError, match="content is empty"):
        _extract_openai_response_text(payload)


def test_openai_response_extractor_accepts_text_content_blocks():
    payload = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": [
                        {"type": "text", "text": "{\"ok\":"},
                        {"type": "text", "text": "true}"},
                    ]
                },
            }
        ]
    }

    assert _extract_openai_response_text(payload) == '{"ok":true}'


def test_invalid_cached_responses_are_requeued():
    cached = ["valid", "", "ERROR: timed out", None]

    misses = _requeue_invalid_cache_entries(cached, [3])

    assert misses == [1, 2, 3]
    assert cached == ["valid", None, None, None]
