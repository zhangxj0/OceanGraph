"""Stage-aware model routing with backward-compatible configuration defaults."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlsplit


def profile_url(raw: Mapping[str, Any], backend: str, fallback: str) -> str:
    """Accept a full legacy URL or an OpenAI-compatible API base, never both."""
    if raw.get("url") and raw.get("base_url"):
        raise ValueError("Set either url or base_url, not both")
    if not raw.get("base_url"):
        return str(raw.get("url") or fallback)
    if backend != "OPENAI":
        raise ValueError("Profile base_url currently requires backend OPENAI; use url otherwise")
    base = str(raw["base_url"]).strip().rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("base_url must be an HTTP(S) URL without credentials, query or fragment")
    if base.endswith("/chat/completions"):
        raise ValueError("base_url must omit /chat/completions; use url for a full endpoint")
    return base + "/chat/completions"


_DEFAULT_STAGE_ROUTES = {
    "corpus": "generator",
    "retrieval": "generator",
    "generation": "generator",
    "selection": "verifier",
    "verification": "verifier",
    "correction": "generator",
    "default": "generator",
}


@dataclass(frozen=True)
class ModelProfile:
    """Connection and generation settings for one model profile."""

    name: str
    backend: str
    model: str
    url: str
    vision_model: Optional[str] = None
    api_key_env: Optional[str] = None
    temperature: Optional[float] = 0.0
    timeout: int = 300
    thinking: Optional[bool] = None
    structured_output: bool = False
    supports_vision: bool = False
    max_output_tokens: Optional[int] = None
    extra_body: Mapping[str, Any] = field(default_factory=dict)
    fallback_api_key: str = field(default="", repr=False, compare=False)

    @property
    def api_key(self) -> str:
        if self.api_key_env:
            value = os.environ.get(self.api_key_env, "")
            if value:
                return value
        return self.fallback_api_key

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.backend not in {"GEMINI", "OLLAMA"} and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def model_name(self, vision: bool = False) -> str:
        return self.vision_model if vision and self.vision_model else self.model

    def cache_identity(
        self,
        *,
        stage: str,
        vision: bool = False,
        response_format: Optional[Mapping[str, Any]] = None,
    ) -> str:
        settings = {
            "profile": self.name,
            "backend": self.backend,
            "model": self.model_name(vision),
            "url": self.url,
            "stage": stage,
            "temperature": self.temperature,
            "thinking": self.thinking,
            "response_format": response_format,
            "max_output_tokens": self.max_output_tokens,
            "extra_body": dict(self.extra_body),
            "supports_vision": self.supports_vision,
            "router_schema": 1,
        }
        return json.dumps(settings, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def openai_payload(
        self,
        messages: list[dict[str, Any]],
        *,
        vision: bool = False,
        response_format: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model_name(vision),
            "messages": messages,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.max_output_tokens is not None:
            payload["max_tokens"] = self.max_output_tokens
        if self.thinking is not None:
            payload["enable_thinking"] = self.thinking
        if response_format and self.structured_output:
            payload["response_format"] = dict(response_format)
        payload.update(dict(self.extra_body))
        return payload


class StageModelRouter:
    """Resolve a model profile for each logical pipeline stage."""

    def __init__(
        self,
        profiles: Mapping[str, ModelProfile],
        stage_routes: Optional[Mapping[str, str]] = None,
    ) -> None:
        if "default" not in profiles:
            raise ValueError("Model router requires a 'default' profile")
        self._profiles = dict(profiles)
        self._stage_routes = {**_DEFAULT_STAGE_ROUTES, **dict(stage_routes or {})}

    @classmethod
    def from_config(
        cls,
        config: Mapping[str, Any],
        *,
        fallback_backend: str,
        fallback_url: str,
        fallback_llm_model: str,
        fallback_vlm_model: str,
        fallback_api_key: str = "",
    ) -> "StageModelRouter":
        backend = fallback_backend.upper()
        default_key_env = {
            "GEMINI": "GEMINI_API_KEY",
            "OPENAI": "OPENAI_API_KEY",
        }.get(backend)
        profiles: Dict[str, ModelProfile] = {
            "default": ModelProfile(
                name="default",
                backend=backend,
                model=fallback_llm_model,
                vision_model=fallback_vlm_model,
                supports_vision=bool(fallback_vlm_model),
                url=fallback_url,
                api_key_env=default_key_env,
                fallback_api_key=fallback_api_key,
            )
        }

        models_config = config.get("models", {}) if isinstance(config, Mapping) else {}
        raw_profiles = models_config.get("profiles", {}) if isinstance(models_config, Mapping) else {}
        for name, raw in raw_profiles.items():
            if not isinstance(raw, Mapping):
                continue
            profile_backend = str(raw.get("backend", backend)).upper()
            api_key_env = raw.get("api_key_env") or {
                "GEMINI": "GEMINI_API_KEY",
                "OPENAI": "OPENAI_API_KEY",
            }.get(profile_backend)
            profiles[name] = ModelProfile(
                name=name,
                backend=profile_backend,
                model=str(raw.get("model") or fallback_llm_model),
                vision_model=raw.get("vision_model"),
                url=profile_url(raw, profile_backend, fallback_url),
                api_key_env=str(api_key_env) if api_key_env else None,
                temperature=raw.get("temperature", 0.0),
                timeout=int(raw.get("timeout", 300)),
                thinking=raw.get("thinking"),
                structured_output=bool(raw.get("structured_output", False)),
                supports_vision=bool(
                    raw.get("supports_vision", bool(raw.get("vision_model")))
                ),
                max_output_tokens=raw.get("max_output_tokens"),
                extra_body=raw.get("extra_body", {}) or {},
                fallback_api_key=(
                    fallback_api_key
                    if profile_backend == backend and not raw.get("api_key_env")
                    else ""
                ),
            )

        stage_routes = models_config.get("stages", {}) if isinstance(models_config, Mapping) else {}
        return cls(profiles, stage_routes)

    def resolve(self, stage: str = "default", vision: bool = False) -> ModelProfile:
        profile_name = self._stage_routes.get(stage, stage)
        profile = self._profiles.get(profile_name, self._profiles["default"])
        if not vision or profile.supports_vision:
            return profile

        vision_route = self._stage_routes.get(f"{stage}_vision")
        if vision_route and self._profiles.get(vision_route, profile).supports_vision:
            return self._profiles[vision_route]

        for fallback_name in ("vision_verifier", "generator", "default"):
            candidate = self._profiles.get(fallback_name)
            if candidate and candidate.supports_vision:
                return candidate
        return profile

    def has_api_key(self) -> bool:
        """Return whether any configured profile can resolve an API key."""
        return any(profile.api_key for profile in self._profiles.values())
