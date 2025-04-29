import pytest

from app.agents.test_generator import load_prompt


def test_generator_prompt_has_sentinels():
    text = load_prompt("code_generator.txt")
    assert "@@START_CODE@@" in text and "@@END_CODE@@" in text


def test_reviewer_prompt_has_approval_flag():
    text = load_prompt("code_reviewer.txt")
    assert "Approved:" in text


def test_load_prompt_missing_file():
    with pytest.raises(FileNotFoundError):
        load_prompt("totally_missing.txt")


def test_load_prompt_missing_marker(tmp_path, monkeypatch):
    # Write a dummy prompt that lacks required markers
    bad_prompt = tmp_path / "bad.txt"
    bad_prompt.write_text("no markers here", encoding="utf-8")
    monkeypatch.setattr("app.agents.test_generator._PROMPT_DIR", tmp_path)

    with pytest.raises(ValueError):
        load_prompt("bad.txt", must_contain=("@@FOO@@",))
