import pytest

from oceangraph.core import llm
from oceangraph.text import sanitize_text_chunks


def test_text_only_mode_never_requires_vision(tmp_path, monkeypatch):
    image_path = tmp_path / "figure.png"
    image_path.write_bytes(b"not-an-image")
    monkeypatch.setenv("OCEANGRAPH_TEXT_ONLY", "1")
    chunks = [{"content": "Text evidence", "artifact": [str(image_path)]}]

    assert llm._chunks_require_vision(chunks) is False
    assert llm._chunk_image_path(chunks[0]) is None


def test_image_specific_calls_are_blocked(monkeypatch):
    monkeypatch.setenv("OCEANGRAPH_TEXT_ONLY", "1")

    with pytest.raises(RuntimeError, match="pipeline.modality is text"):
        llm.call_vlm_simple("prompt", "figure.png")


def test_sanitize_text_chunks_removes_visual_metadata():
    chunks = sanitize_text_chunks(
        [
            {
                "content": "Retained OCR or paragraph text",
                "artifact": ["figure.png"],
                "image_path": "figure.png",
                "chunk_type": "standalone image",
            },
            {"content": "", "artifact": ["image-only.png"]},
        ]
    )

    assert chunks == [
        {
            "content": "Retained OCR or paragraph text",
            "artifact": [],
            "image_path": None,
            "chunk_type": "text",
        }
    ]
