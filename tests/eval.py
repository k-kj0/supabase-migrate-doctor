"""
eval.py
Precision/recall of the scanner+classifier against a small hand-labeled
fixture repo. This is the piece that makes "we have grounded, cited
explanations" a checkable claim instead of a vibe: run this after any
change to scanner.py or classifier.py.

Usage: python -m tests.eval
"""
from __future__ import annotations

import json
from pathlib import Path

from supabase_migrate.classifier import classify
from supabase_migrate.scanner import scan_repo

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "sample_repo"
EXPECTED_PATH = Path(__file__).parent / "fixtures" / "expected.json"


def run_eval() -> None:
    expected = json.loads(EXPECTED_PATH.read_text())
    expected_set = {(e["file"], e["line"], e["severity"]) for e in expected}

    result = scan_repo(FIXTURE_ROOT)
    actual = [classify(f) for f in result.findings]
    actual_set = {(iss.finding.file, iss.finding.line_no, iss.severity) for iss in actual}

    true_positives = expected_set & actual_set
    false_positives = actual_set - expected_set
    false_negatives = expected_set - actual_set

    precision = len(true_positives) / len(actual_set) if actual_set else 0.0
    recall = len(true_positives) / len(expected_set) if expected_set else 0.0

    print(f"Expected: {len(expected_set)}  Found: {len(actual_set)}  Matched: {len(true_positives)}")
    print(f"Precision: {precision:.2f}   Recall: {recall:.2f}\n")

    if false_positives:
        print("False positives (flagged but not expected):")
        for fp in sorted(false_positives):
            print(f"  {fp}")
    if false_negatives:
        print("False negatives (expected but missed):")
        for fn in sorted(false_negatives):
            print(f"  {fn}")
    if not false_positives and not false_negatives:
        print("All findings match expected ground truth exactly.")


if __name__ == "__main__":
    run_eval()
