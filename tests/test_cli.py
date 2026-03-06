"""Tests for CLI entry points."""

import sys
from unittest.mock import patch

import pytest
from osf_scraper.cli import analyse, discover, process, remaining, scrape


class TestDiscoverCLI:
    def test_help_exits_zero(self):
        """osf-discover --help should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["osf-discover", "--help"]):
                discover()
        assert exc_info.value.code == 0


class TestScrapeCLI:
    def test_help_exits_zero(self):
        """osf-scrape --help should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["osf-scrape", "--help"]):
                scrape()
        assert exc_info.value.code == 0

    def test_missing_file_exits_nonzero(self, tmp_path):
        """osf-scrape with a missing input file should exit with code 1."""
        missing = tmp_path / "nonexistent.txt"
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                ["osf-scrape", "--file", str(missing)],
            ):
                scrape()
        assert exc_info.value.code == 1


class TestProcessCLI:
    def test_help_exits_zero(self):
        """osf-process --help should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["osf-process", "--help"]):
                process()
        assert exc_info.value.code == 0


class TestAnalyseCLI:
    def test_help_exits_zero(self):
        """osf-analyse --help should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["osf-analyse", "--help"]):
                analyse()
        assert exc_info.value.code == 0


class TestRemainingCLI:
    def test_help_exits_zero(self):
        """osf-remaining --help should exit with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["osf-remaining", "--help"]):
                remaining()
        assert exc_info.value.code == 0

    def test_missing_files_exits_nonzero(self, tmp_path):
        """osf-remaining with missing input files should exit with code 1."""
        missing_all = tmp_path / "all.txt"
        missing_succ = tmp_path / "succ.txt"
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "osf-remaining",
                    "--all-ids",
                    str(missing_all),
                    "--successful-ids",
                    str(missing_succ),
                ],
            ):
                remaining()
        assert exc_info.value.code == 1
