"""Regression coverage for reasoning-model truncation and incomplete corpora."""
import json
import asyncio
from types import SimpleNamespace

import pytest

from oceangraph.core import llm
from oceangraph.pipeline import chunker
from oceangraph.providers.router import ModelProfile
from oceangraph.utils.checkpoint import CheckpointManager


def response(content="", finish="length"):
    return {"choices": [{"finish_reason": finish, "message": {
        "content": content, "reasoning_content": "reasoning"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 4096}}


@pytest.fixture
def mocked_llm(monkeypatch):
    profile = ModelProfile(name="glm", backend="OPENAI", model="GLM-5.3",
                           url="https://example.test", max_output_tokens=4096)
    monkeypatch.setattr(llm, "_initialize_config", lambda: None)
    monkeypatch.setattr(llm, "_get_model_profile", lambda stage, **kwargs: profile)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    llm.reset_token_stats()
    yield
    llm.reset_token_stats()


def test_length_failure_does_not_repeat_identical_paid_request(monkeypatch, mocked_llm):
    calls = []
    def post(*args, **kwargs):
        calls.append(kwargs["json"])
        return SimpleNamespace(status_code=200, json=lambda: response())
    monkeypatch.setattr(llm.requests, "post", post)
    with pytest.raises(ValueError, match="length"):
        llm.call_llm_simple("actual prompt", use_cache=False)
    assert len(calls) == 1


def test_usage_includes_rejected_empty_responses(monkeypatch, mocked_llm):
    monkeypatch.setattr(llm.requests, "post", lambda *a, **kw:
        SimpleNamespace(status_code=200, json=lambda: response()))
    with pytest.raises(Exception):
        llm.call_llm_simple("prompt", max_retries=1, use_cache=False)
    assert llm.get_token_stats() == {"total_input_tokens": 100,
        "total_output_tokens": 4096, "total_calls": 1}


def test_partial_nonempty_length_response_is_rejected():
    with pytest.raises(ValueError, match="length"):
        llm._extract_openai_response_text(response('{"partial":'))


def test_transient_empty_response_can_still_retry(monkeypatch, mocked_llm):
    responses = iter([response(finish="stop"), response("valid", "stop")])
    monkeypatch.setattr(llm.requests, "post", lambda *a, **kw:
        SimpleNamespace(status_code=200, json=lambda: next(responses)))
    assert llm.call_llm_simple("prompt", use_cache=False) == "valid"
    assert llm.get_token_stats()["total_calls"] == 2


def test_text_context_length_failure_is_not_retried_and_is_counted(monkeypatch, mocked_llm):
    calls = []
    def post(*a, **kw):
        calls.append(1)
        return SimpleNamespace(status_code=200, json=lambda: response())
    monkeypatch.setenv("OCEANGRAPH_TEXT_ONLY", "1")
    monkeypatch.setattr(llm.requests, "post", post)
    with pytest.raises(ValueError, match="length"):
        llm.call_vlm_interweaved("prompt", [{"content":"ocean science"}], use_cache=False)
    assert calls == [1]
    assert llm.get_token_stats()["total_output_tokens"] == 4096


@pytest.mark.parametrize("kind", ["llm", "vlm"])
def test_batch_length_failure_is_not_retried(monkeypatch, kind):
    calls = []
    async def limited(*args, **kwargs):
        calls.append(1)
        raise llm.OutputTokenLimitError("finish_reason=length")
    async def no_wait(*args, **kwargs):
        pass
    monkeypatch.setattr(llm.asyncio, "sleep", no_wait)
    monkeypatch.setattr(llm, "get_rate_limiter", lambda: object())
    if kind == "llm":
        monkeypatch.setattr(llm, "_async_call_llm_simple", limited)
        result = asyncio.run(llm._batch_llm_calls_async(["prompt"]))
    else:
        monkeypatch.setattr(llm, "_async_call_vlm_interweaved", limited)
        result = asyncio.run(llm._batch_vlm_calls_async([("prompt", [{"content":"evidence"}])]))
    assert calls == [1]
    assert result[0].startswith("ERROR:")


@pytest.fixture
def small_windows(monkeypatch):
    from oceangraph.core import config
    monkeypatch.setattr(config, "load_config", lambda: {
        "chunking": {"window_size": 100, "overlap_size": 10}})


def test_failed_second_window_never_returns_partial_document(monkeypatch, small_windows):
    calls = []
    def call(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise ValueError("request failed")
        return "1<|#|>Text<|#|>evidence<|#|>None<|#|>COMPLETE<|#|><chunk_end>"
    monkeypatch.setattr(chunker, "call_llm_simple", call)
    with pytest.raises(RuntimeError, match="window 2"):
        chunker.chunk_with_windows("a" * 250)
    assert len(calls) == 2


@pytest.mark.parametrize("text", ["", "not a chunk", "1<|#|>Text<|#|><|#|>None<|#|>COMPLETE<|#|><chunk_end>"])
def test_empty_or_malformed_window_is_failure(monkeypatch, small_windows, text):
    monkeypatch.setattr(chunker, "call_llm_simple", lambda *a, **kw: text)
    with pytest.raises(RuntimeError, match="window 1"):
        chunker.chunk_with_windows("ocean evidence")


@pytest.mark.parametrize("suffix", [
    "broken second chunk<chunk_end>",
    "2<|#|>Text<|#|>evidence<|#|>None<|#|>COMPLETE<|#|>",
    "2<|#|>Text<|#|>evidence<|#|>None<|#|>UNKNOWN<|#|><chunk_end>",
])
def test_malformed_block_cannot_be_hidden_by_valid_block(monkeypatch, small_windows, suffix):
    valid = "1<|#|>Text<|#|>ocean<|#|>None<|#|>COMPLETE<|#|><chunk_end>"
    monkeypatch.setattr(chunker, "call_llm_simple", lambda *a, **kw: valid + suffix)
    with pytest.raises(RuntimeError, match="window 1"):
        chunker.chunk_with_windows("ocean evidence")


def test_missing_inner_chunk_terminator_cannot_merge_and_drop_a_chunk(monkeypatch, small_windows):
    merged = (
        "1<|#|>Text<|#|>first evidence<|#|>None<|#|>COMPLETE<|#|>"
        "2<|#|>Text<|#|>second evidence<|#|>None<|#|>COMPLETE<|#|><chunk_end>"
    )
    monkeypatch.setattr(chunker, "call_llm_simple", lambda *a, **kw: merged)
    with pytest.raises(RuntimeError, match="window 1"):
        chunker.chunk_with_windows("first evidence second evidence")


def test_checkpoint_cannot_complete_empty_document(tmp_path):
    manager = CheckpointManager(str(tmp_path))
    with pytest.raises(ValueError, match="empty"):
        manager.save_file_chunks("empty", [])
    assert manager.get_completed_chunk_files() == set()


def test_legacy_empty_checkpoint_is_not_reused(tmp_path):
    manager = CheckpointManager(str(tmp_path))
    manager.chunks_checkpoint.write_text(json.dumps({
        "completed_files": ["bad", "good"], "chunks_by_file": {
            "bad": [], "good": [{"content": "valid evidence"}]},
        "final_chunks_saved": True}), encoding="utf-8")
    resumed = CheckpointManager(str(tmp_path))
    assert resumed.get_completed_chunk_files() == {"good"}
    assert resumed.is_final_chunks_saved() is False
    assert resumed.get_all_file_chunks() == {"good": [{"content": "valid evidence"}]}


def test_new_document_chunks_invalidate_previous_final_marker_on_replay(tmp_path):
    manager = CheckpointManager(str(tmp_path))
    manager.save_file_chunks("first", [{"content": "first evidence"}])
    manager.mark_final_chunks_saved()
    manager.save_file_chunks("second", [{"content": "second evidence"}])

    assert manager.is_final_chunks_saved() is False
    assert CheckpointManager(str(tmp_path)).is_final_chunks_saved() is False


def test_repairing_legacy_empty_doc_cannot_revive_stale_final_marker(tmp_path):
    manager = CheckpointManager(str(tmp_path))
    manager.chunks_checkpoint.write_text(json.dumps({
        "completed_files": ["bad", "good"], "chunks_by_file": {
            "bad": [], "good": [{"content": "good evidence"}]},
        "final_chunks_saved": True}), encoding="utf-8")
    resumed = CheckpointManager(str(tmp_path))
    resumed.save_file_chunks("bad", [{"content": "repaired evidence"}])

    assert CheckpointManager(str(tmp_path)).is_final_chunks_saved() is False


def test_corpus_failure_preserves_good_checkpoints_without_finalizing(monkeypatch, tmp_path):
    from oceangraph import engine
    source = tmp_path / "input"
    source.mkdir()
    (source / "a_good.md").write_text("evidence")
    (source / "b_bad.md").write_text("evidence")
    (source / "z_later.md").write_text("evidence")
    output = tmp_path / "output"
    manager = CheckpointManager(str(output))
    monkeypatch.setattr(engine, "OUTPUT_DIR", str(output))
    monkeypatch.setattr(engine, "NUM_WORKERS", 1)
    monkeypatch.setattr(engine, "MAX_PDFS", None)
    processed = []
    def worker(args):
        _, name = args
        processed.append(name)
        return (name, [{"content":"evidence"}], None) if name=="a_good" else (name, [], "failed window")
    monkeypatch.setattr(engine, "_chunk_single_markdown", worker)
    with pytest.raises(RuntimeError, match="chunking"):
        engine.convert_documents_to_chunks_parallel(str(source), str(output / "chunks.json"), manager)
    assert manager.get_completed_chunk_files() == {"a_good"}
    assert processed == ["a_good", "b_bad"]
    assert manager.is_final_chunks_saved() is False
    assert not (output / "chunks.json").exists()
