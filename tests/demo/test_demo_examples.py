from __future__ import annotations

import json
from pathlib import Path

import pytest

from libs.demo.examples import DemoExample, load_examples

_MINIMAL_EXAMPLE = {
    "example_id": "ex001",
    "title": "Test Example",
    "duration_seconds": 8.5,
    "degradation_ids": ["far_field_room"],
    "ground_truth": "Hello world",
}


def test_load_examples_returns_empty_when_file_absent(tmp_path):
    result = load_examples(tmp_path / "nonexistent.json")
    assert result == []


def test_load_examples_returns_empty_when_file_is_empty_array(tmp_path):
    config = tmp_path / "examples.json"
    config.write_text("[]", encoding="utf-8")
    assert load_examples(config) == []


def test_load_examples_returns_examples_from_json(tmp_path):
    config = tmp_path / "examples.json"
    config.write_text(json.dumps([_MINIMAL_EXAMPLE]), encoding="utf-8")
    result = load_examples(config)
    assert len(result) == 1
    assert result[0].example_id == "ex001"
    assert result[0].title == "Test Example"
    assert result[0].ground_truth == "Hello world"


def test_demo_example_defaults_audio_available_false():
    ex = DemoExample(**_MINIMAL_EXAMPLE)
    assert ex.audio_available is False


def test_demo_example_defaults_description_empty():
    ex = DemoExample(**_MINIMAL_EXAMPLE)
    assert ex.description == ""


def test_demo_example_defaults_clean_audio_path_none():
    ex = DemoExample(**_MINIMAL_EXAMPLE)
    assert ex.clean_audio_path is None


def test_demo_example_defaults_degraded_audio_paths_empty():
    ex = DemoExample(**_MINIMAL_EXAMPLE)
    assert ex.degraded_audio_paths == {}


def test_demo_examples_module_does_not_import_platform_db():
    src = Path("libs/demo/examples.py").read_text(encoding="utf-8")
    assert "from libs.common.db" not in src
    assert "sqlalchemy" not in src
