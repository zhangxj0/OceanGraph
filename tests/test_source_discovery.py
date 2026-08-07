from pathlib import Path

import pytest

from oceangraph.utils.sources import count_source_types, discover_source_documents


def test_source_discovery_accepts_nested_normalized_archive(tmp_path):
    nested = tmp_path / "normalized" / "normalized"
    nested.mkdir(parents=True)
    (nested / "ocean.md").write_text("# Ocean", encoding="utf-8")
    (nested / "table.txt").write_text("salinity", encoding="utf-8")
    (nested / "README.md").write_text("ignore me", encoding="utf-8")

    documents = discover_source_documents(tmp_path / "normalized")

    assert [path.name for path in documents] == ["ocean.md", "table.txt"]
    assert count_source_types(documents) == {"pdf": 0, "html": 0, "text": 2}


def test_source_discovery_rejects_duplicate_stems_for_engine_ids(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    (first / "same.md").write_text("one", encoding="utf-8")
    (second / "same.txt").write_text("two", encoding="utf-8")

    with pytest.raises(ValueError, match="unique stems"):
        discover_source_documents(tmp_path, require_unique_stems=True)
