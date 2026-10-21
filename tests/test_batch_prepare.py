import json

import pytest

from oceangraph.batch import prepare


def test_interrupted_inventory_is_not_published_and_can_be_retried(tmp_path):
    assert hasattr(prepare, "publish_inventory"), "Inventory must be published atomically"
    path = tmp_path / "sources.jsonl"

    def interrupted():
        yield {"id": "first"}
        raise OSError("interrupted preparation")

    with pytest.raises(OSError):
        prepare.publish_inventory(path, interrupted())
    assert not path.exists()
    prepare.publish_inventory(path, [{"id": "first"}, {"id": "second"}])
    assert [json.loads(line)["id"] for line in path.read_text().splitlines()] == ["first", "second"]


def test_prepare_creates_complete_inventory_without_network(tmp_path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    body = "Marine nutrient cycling in coastal seawater controls phytoplankton growth and ocean carbon export. " * 75
    (source / "paper.md").write_text('---\ntitle: Marine coastal nutrient cycling\ndoi: example-unique\nsource_url: https://source.example/paper\n---\n## Abstract\n' + body, encoding="utf-8")
    out = tmp_path / "output"
    monkeypatch.setattr("sys.argv", ["prepare", "--input", str(source), "--output", str(out)])
    prepare.main()
    rows = [json.loads(line) for line in (out / "sources.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["id"] == "paper"
    assert json.loads((out / "source_inventory.json").read_text())["counts"]["eligible"] == 1
    with pytest.raises(SystemExit, match="already contains"):
        prepare.main()
