from oceangraph.providers import StageModelRouter


def test_stage_router_selects_generator_and_verifier(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "qwen-secret")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-secret")
    config = {
        "models": {
            "profiles": {
                "generator": {
                    "backend": "OPENAI",
                    "url": "https://example.test/qwen/chat/completions",
                    "api_key_env": "DASHSCOPE_API_KEY",
                    "model": "qwen3.7-plus",
                    "vision_model": "qwen3.7-plus",
                    "supports_vision": True,
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
    assert generator.model == "qwen3.7-plus"
    assert verifier.model == "deepseek-v4-pro"
    assert router.resolve("verification", vision=True).model == "qwen3.7-plus"
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
