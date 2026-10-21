"""Load the same stage profiles as the normal pipeline; never read secret files."""
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from oceangraph.providers.router import StageModelRouter

STAGES = ("generation", "verification")
RESERVED = {"model", "messages", "max_tokens", "max_completion_tokens", "max_output_tokens",
            "stream", "n", "api_key", "headers", "authorization", "response_format"}


def load_routes(path, require_keys=False):
    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Model configuration must be a mapping")
    models = config.get("models", {})
    if not isinstance(models, dict) or not isinstance(models.get("profiles"), dict):
        raise ValueError("models.profiles must define generator and verifier")
    profiles = models["profiles"]
    stage_names = models.get("stages", {})
    if not isinstance(stage_names, dict):
        raise ValueError("models.stages must be a mapping")
    for stage, default in zip(STAGES, ("generator", "verifier")):
        name = stage_names.get(stage, default)
        raw = profiles.get(name)
        if not isinstance(raw, Mapping) or not raw.get("model"):
            raise ValueError(f"Missing explicit model profile for {stage}")
        if str(raw.get("backend", "OPENAI")).upper() != "OPENAI":
            raise ValueError("Batch runner supports OPENAI-compatible chat completions only")
        if not (raw.get("url") or raw.get("base_url")):
            raise ValueError(f"Missing url/base_url for {stage}")
        extra = raw.get("extra_body", {}) or {}
        if not isinstance(extra, Mapping) or RESERVED.intersection(k.lower() for k in extra):
            raise ValueError("extra_body must be a mapping and cannot override routing, credentials, messages, format or budget")
        cap = raw.get("max_output_tokens", 8192)
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            raise ValueError("max_output_tokens must be a positive integer")
        if raw.get("structured_output", True) is not True:
            raise ValueError("Batch runner requires structured_output: true")
    router = StageModelRouter.from_config(config, fallback_backend="OPENAI", fallback_url="",
                                         fallback_llm_model="", fallback_vlm_model="")
    routes = {stage: router.resolve(stage) for stage in STAGES}
    for stage, profile in routes.items():
        parsed = urlsplit(profile.url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError(f"Invalid endpoint for {stage}; do not place credentials in URLs")
        if profile.timeout <= 0:
            raise ValueError("timeout must be positive")
        if require_keys and not profile.api_key:
            raise ValueError(f"Missing environment variable {profile.api_key_env} for {stage}")
    return routes


def request_for(routes, stage, prompt, max_tokens=8192):
    profile = routes[stage]
    payload = profile.openai_payload([{"role": "user", "content": prompt}],
                                     response_format={"type": "json_object"})
    payload["response_format"] = {"type": "json_object"}
    payload["max_tokens"] = min(profile.max_output_tokens or max_tokens, max_tokens)
    metadata = {"profile": profile.name, "model": profile.model, "url": profile.url,
                "api_key_env": profile.api_key_env, "max_tokens": payload["max_tokens"],
                "timeout": min(profile.timeout, 180),
                "parameters": {k: v for k, v in payload.items() if k not in {"messages", "model"}}}
    metadata["config_id"] = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()[:16]
    return profile.url, profile.headers, payload, metadata


def route_summary(routes):
    return {stage: request_for(routes, stage, "")[3] for stage in STAGES}
