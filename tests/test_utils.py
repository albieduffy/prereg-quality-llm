"""Tests for compute_remaining_ids."""

import pytest
from osf_scraper.utils import compute_remaining_ids


def test_compute_remaining_ids_basic(tmp_path):
    """Correctly computes the difference between all IDs and successful IDs."""
    all_ids_file = tmp_path / "all.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "remaining.txt"

    all_ids_file.write_text("abc\ndef\nghi\njkl\n")
    successful_file.write_text("abc\nghi\n")

    result = compute_remaining_ids(all_ids_file, successful_file, output_file)

    assert result == {"def", "jkl"}
    assert output_file.exists()
    remaining = set(output_file.read_text().strip().split("\n"))
    assert remaining == {"def", "jkl"}


def test_compute_remaining_ids_all_done(tmp_path):
    """Returns empty set when all IDs have been processed."""
    all_ids_file = tmp_path / "all.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "remaining.txt"

    all_ids_file.write_text("abc\ndef\n")
    successful_file.write_text("abc\ndef\n")

    result = compute_remaining_ids(all_ids_file, successful_file, output_file)

    assert result == set()


def test_compute_remaining_ids_none_done(tmp_path):
    """Returns all IDs when none have been processed."""
    all_ids_file = tmp_path / "all.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "remaining.txt"

    all_ids_file.write_text("abc\ndef\n")
    successful_file.write_text("")

    result = compute_remaining_ids(all_ids_file, successful_file, output_file)

    assert result == {"abc", "def"}


def test_compute_remaining_ids_creates_output_dir(tmp_path):
    """Output directory is created automatically."""
    all_ids_file = tmp_path / "all.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "nested" / "remaining.txt"

    all_ids_file.write_text("abc\n")
    successful_file.write_text("")

    compute_remaining_ids(all_ids_file, successful_file, output_file)

    assert output_file.exists()


def test_compute_remaining_ids_skips_blank_lines(tmp_path):
    """Blank lines in input files are ignored."""
    all_ids_file = tmp_path / "all.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "remaining.txt"

    all_ids_file.write_text("abc\n\ndef\n\n")
    successful_file.write_text("\nabc\n\n")

    result = compute_remaining_ids(all_ids_file, successful_file, output_file)

    assert result == {"def"}


def test_compute_remaining_ids_missing_all_file(tmp_path):
    """Raises FileNotFoundError when the all-IDs file is missing."""
    missing = tmp_path / "missing.txt"
    successful_file = tmp_path / "successful.txt"
    output_file = tmp_path / "remaining.txt"
    successful_file.write_text("")

    with pytest.raises(FileNotFoundError):
        compute_remaining_ids(missing, successful_file, output_file)


def test_compute_remaining_ids_missing_successful_file(tmp_path):
    """Raises FileNotFoundError when the successful-IDs file is missing."""
    all_ids_file = tmp_path / "all.txt"
    missing = tmp_path / "missing.txt"
    output_file = tmp_path / "remaining.txt"
    all_ids_file.write_text("abc\n")

    with pytest.raises(FileNotFoundError):
        compute_remaining_ids(all_ids_file, missing, output_file)
