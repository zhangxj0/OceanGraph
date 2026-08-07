import json

from oceangraph.utils.checkpoint import CheckpointManager
from oceangraph.utils.llm_cache import LLMCache


def test_checkpoint_journal_replays_without_full_snapshot_rewrites(tmp_path):
    fingerprint = "c" * 64
    manager = CheckpointManager(str(tmp_path), run_fingerprint=fingerprint)
    manager.mark_markdown_complete("ocean", "ocean.md")
    manager.save_qa_result(
        "1",
        successful=[{"question": "Q", "answer": "A"}],
        failed=[],
        chunk_with_context={"original_chunk_id": "1"},
    )

    assert manager.markdown_checkpoint.with_suffix(".jsonl").exists()
    assert manager.qa_checkpoint.with_suffix(".jsonl").exists()
    assert not manager.qa_checkpoint.exists()

    reloaded = CheckpointManager(str(tmp_path), run_fingerprint=fingerprint)
    successful, failed, contexts = reloaded.get_accumulated_qa()

    assert reloaded.get_completed_markdown_files() == {"ocean"}
    assert successful == [{"question": "Q", "answer": "A"}]
    assert failed == []
    assert contexts == [{"original_chunk_id": "1"}]


def test_checkpoint_replay_ignores_only_an_incomplete_tail(tmp_path):
    manager = CheckpointManager(str(tmp_path), run_fingerprint="d" * 64)
    manager.mark_markdown_complete("valid", "valid.md")
    journal = manager.markdown_checkpoint.with_suffix(".jsonl")
    with journal.open("a", encoding="utf-8") as handle:
        handle.write('{"op": "markdown_complete"')

    reloaded = CheckpointManager(str(tmp_path), run_fingerprint="d" * 64)
    reloaded.mark_markdown_complete("after_repair", "after_repair.md")
    repaired = CheckpointManager(str(tmp_path), run_fingerprint="d" * 64)

    assert repaired.get_completed_markdown_files() == {"valid", "after_repair"}


def test_checkpoint_reads_legacy_json_snapshot_before_new_journal_events(tmp_path):
    fingerprint = "e" * 64
    initial = CheckpointManager(str(tmp_path), run_fingerprint=fingerprint)
    initial.markdown_checkpoint.write_text(
        json.dumps(
            {
                "completed_files": ["legacy"],
                "failed_files": [],
                "last_updated": "2026-07-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    migrated = CheckpointManager(str(tmp_path), run_fingerprint=fingerprint)
    migrated.mark_markdown_complete("new", "new.md")
    reloaded = CheckpointManager(str(tmp_path), run_fingerprint=fingerprint)

    assert reloaded.get_completed_markdown_files() == {"legacy", "new"}


def test_llm_cache_journal_round_trip_and_legacy_compatibility(tmp_path):
    cache_dir = tmp_path / "cache"
    cache = LLMCache(str(cache_dir))
    cache.set("llm_simple", "prompt", "response", model="model-a")

    assert cache.journal_file.exists()
    assert not cache.cache_file.exists()
    assert cache.get("llm_simple", "prompt", model="model-a") == "response"
    assert (
        cache.get(
            "llm_simple",
            "prompt",
            model="model-a",
            max_age_seconds=3600,
        )
        == "response"
    )
    assert cache.get("llm_simple", "prompt", model="model-a", max_age_seconds=0) is None

    reloaded = LLMCache(str(cache_dir))
    assert reloaded.get("llm_simple", "prompt", model="model-a") == "response"

    with reloaded.journal_file.open("a", encoding="utf-8") as handle:
        handle.write('{"key": "partial"')
    repaired_cache = LLMCache(str(cache_dir))
    repaired_cache.set("llm_simple", "second", "second-response", model="model-a")
    final_cache = LLMCache(str(cache_dir))
    assert final_cache.get("llm_simple", "prompt", model="model-a") == "response"
    assert final_cache.get("llm_simple", "second", model="model-a") == "second-response"

    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    key = LLMCache._hash_content("unused")
    (legacy_dir / "llm_responses.json").write_text(
        json.dumps({key: {"response": "legacy"}}),
        encoding="utf-8",
    )
    legacy_cache = LLMCache(str(legacy_dir))
    assert legacy_cache.get_stats()["cache_size"] == 1
