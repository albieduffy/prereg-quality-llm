"""Tests for the processing module (process_registrations & analyse_registrations)."""

import json

import pytest
from osf_scraper.processing import analyse_registrations, process_registrations


# ---- process_registrations tests ----


def test_process_registrations_basic(tmp_path):
    """Flattens a JSONL file into a processed JSONL with normalised columns."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "output" / "result.jsonl"

    records = [
        {"id": "abc", "attributes": {"title": "Study 1", "year": 2020}},
        {"id": "def", "attributes": {"title": "Study 2", "year": 2021}},
    ]
    input_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    process_registrations(input_file, output_file)

    assert output_file.exists()
    lines = [json.loads(l) for l in output_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert lines[0]["id"] == "abc"
    assert lines[0]["attributes.title"] == "Study 1"


def test_process_registrations_creates_output_dir(tmp_path):
    """Output directory is created automatically."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "nested" / "deep" / "out.jsonl"
    input_file.write_text(json.dumps({"id": "x"}) + "\n")

    process_registrations(input_file, output_file)

    assert output_file.exists()


def test_process_registrations_empty_input(tmp_path):
    """Empty input produces an empty output file without error."""
    input_file = tmp_path / "empty.jsonl"
    output_file = tmp_path / "out.jsonl"
    input_file.write_text("")

    process_registrations(input_file, output_file)

    assert output_file.exists()
    lines = [l for l in output_file.read_text().splitlines() if l.strip()]
    assert lines == []


# ---- analyse_registrations tests ----


def test_analyse_registrations_basic(tmp_path):
    """Extracts column names from a JSONL file."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "columns.json"

    records = [
        {"id": "abc", "title": "Study 1", "year": 2020},
        {"id": "def", "title": "Study 2", "year": 2021},
    ]
    input_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    analyse_registrations(input_file, output_file)

    assert output_file.exists()
    columns = json.loads(output_file.read_text())
    assert columns == ["id", "title", "year"]


def test_analyse_registrations_union_of_keys(tmp_path):
    """Returns the union of keys across all records, preserving order."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "columns.json"

    records = [
        {"id": "abc", "title": "Study 1"},
        {"id": "def", "extra": "value"},
    ]
    input_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")

    analyse_registrations(input_file, output_file)

    columns = json.loads(output_file.read_text())
    assert "id" in columns
    assert "title" in columns
    assert "extra" in columns
    assert len(columns) == 3


def test_analyse_registrations_creates_output_dir(tmp_path):
    """Output directory is created automatically."""
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "nested" / "cols.json"
    input_file.write_text(json.dumps({"a": 1}) + "\n")

    analyse_registrations(input_file, output_file)

    assert output_file.exists()


def test_analyse_registrations_empty_input(tmp_path):
    """Empty input produces an empty column list."""
    input_file = tmp_path / "empty.jsonl"
    output_file = tmp_path / "columns.json"
    input_file.write_text("")

    analyse_registrations(input_file, output_file)

    columns = json.loads(output_file.read_text())
    assert columns == []
