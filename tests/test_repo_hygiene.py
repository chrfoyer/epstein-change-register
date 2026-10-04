"""Cheap guards against merge accidents that CI otherwise cannot see."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEXT_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".toml", ".html", ".csv"}
CONFLICT = re.compile(r"^(<{7}( |$)|={7}$|>{7}( |$))", re.MULTILINE)


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / p for p in out.stdout.splitlines() if (ROOT / p).suffix in TEXT_SUFFIXES]


def test_no_merge_conflict_markers():
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in tracked_text_files()
        if p.exists() and CONFLICT.search(p.read_text(encoding="utf-8", errors="replace"))
    ]
    assert offenders == []


def test_decision_ids_are_unique_and_ascending():
    """A botched rebase can delete or duplicate an entry; the log must stay intact."""
    text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    ids = [int(m) for m in re.findall(r"^## D-(\d{3}) ", text, re.MULTILINE)]
    assert ids == sorted(set(ids)), f"decision ids not unique and ascending: {ids}"
    assert ids[0] == 1
