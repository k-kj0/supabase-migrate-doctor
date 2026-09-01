"""
cli.py
`supabase-migrate scan <path>` - the CLI Engineer-facing surface of the
tool. Human-readable table by default, --json for CI pipelines, and a
non-zero exit code when CRITICAL/HIGH findings exist so this can gate
a deploy.
"""
from __future__ import annotations

import argparse
import json
import sys

from .classifier import CRITICAL, HIGH, classify, sort_issues
from .rag import explain, load_knowledge_base
from .scanner import scan_repo

_SEVERITY_COLOR = {
    "CRITICAL": "\033[91m",
    "HIGH": "\033[93m",
    "MEDIUM": "\033[94m",
    "INFO": "\033[90m",
}
_RESET = "\033[0m"


def build_report(path: str, explain_findings: bool = True) -> dict:
    result = scan_repo(path)
    issues = sort_issues([classify(f) for f in result.findings])
    kb = load_knowledge_base() if explain_findings else {}

    report_issues = []
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "INFO": 0}
    for issue in issues:
        counts[issue.severity] += 1
        entry = {
            "severity": issue.severity,
            "file": issue.finding.file,
            "line": issue.finding.line_no,
            "snippet": issue.finding.line,
            "reason": issue.reason,
        }
        if explain_findings:
            entry["explanation"] = explain(issue.doc_topic, issue.finding.line, kb)
        report_issues.append(entry)

    return {
        "files_scanned": result.files_scanned,
        "counts": counts,
        "issues": report_issues,
    }


def _print_human(report: dict) -> None:
    print(f"\nScanned {report['files_scanned']} files.\n")
    c = report["counts"]
    print(f"  CRITICAL: {c['CRITICAL']}   HIGH: {c['HIGH']}   MEDIUM: {c['MEDIUM']}   INFO: {c['INFO']}\n")

    if not report["issues"]:
        print("No legacy Supabase key references found.")
        return

    for issue in report["issues"]:
        color = _SEVERITY_COLOR.get(issue["severity"], "")
        print(f"{color}[{issue['severity']}]{_RESET} {issue['file']}:{issue['line']}")
        print(f"    {issue['snippet']}")
        print(f"    -> {issue['reason']}")
        if "explanation" in issue:
            print(f"    -> {issue['explanation']}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="supabase-migrate")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a repo for legacy Supabase API key usage")
    scan_p.add_argument("path", help="Path to the repo to scan")
    scan_p.add_argument("--json", action="store_true", help="Output JSON instead of a human-readable report")
    scan_p.add_argument("--no-explain", action="store_true", help="Skip the retrieval-grounded explanations (faster)")
    scan_p.add_argument(
        "--fail-on",
        choices=["CRITICAL", "HIGH", "MEDIUM", "none"],
        default="HIGH",
        help="Exit non-zero if any issue at or above this severity is found (default: HIGH). Use 'none' to always exit 0.",
    )

    args = parser.parse_args(argv)

    if args.command == "scan":
        report = build_report(args.path, explain_findings=not args.no_explain)

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            _print_human(report)

        if args.fail_on == "none":
            return 0
        threshold = {"CRITICAL": [CRITICAL], "HIGH": [CRITICAL, HIGH], "MEDIUM": [CRITICAL, HIGH, "MEDIUM"]}
        if any(issue["severity"] in threshold[args.fail_on] for issue in report["issues"]):
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
