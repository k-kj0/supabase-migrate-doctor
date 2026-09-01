"""
classifier.py
Turns a raw Finding into a risk-scored MigrationIssue. This is the
part that keeps the tool from just being "grep for eyJ" - the same
pattern (a legacy key reference) means very different things depending
on whether it's a privileged key, and whether it's reachable from the
browser bundle.
"""
from __future__ import annotations

from dataclasses import dataclass

from .scanner import Finding

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
INFO = "INFO"

_SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, INFO: 3}


@dataclass
class MigrationIssue:
    finding: Finding
    severity: str
    reason: str
    doc_topic: str  # which knowledge-base topic to retrieve for the explanation


def classify(finding: Finding) -> MigrationIssue:
    if finding.kind == "new_format":
        return MigrationIssue(
            finding=finding,
            severity=INFO,
            reason="Already using a new-format (sb_publishable_/sb_secret_) key here - no action needed.",
            doc_topic="new_key_format",
        )

    if finding.kind == "literal_jwt":
        if finding.is_service_role_ish and finding.in_frontend_context:
            return MigrationIssue(
                finding=finding,
                severity=CRITICAL,
                reason=(
                    "A literal legacy key is committed in a file that looks like it ships to the "
                    "browser, and the surrounding context suggests a privileged (service_role) key. "
                    "If this is real, treat it as an active credential leak, not just a migration item."
                ),
                doc_topic="service_role_exposure",
            )
        if finding.is_service_role_ish:
            return MigrationIssue(
                finding=finding,
                severity=HIGH,
                reason=(
                    "A literal legacy privileged key appears to be committed to source. It should be "
                    "rotated to the new sb_secret_ format and removed from git history, regardless of "
                    "the 2026 deprecation deadline."
                ),
                doc_topic="secret_key_rotation",
            )
        return MigrationIssue(
            finding=finding,
            severity=MEDIUM,
            reason="A literal legacy anon key is committed to source. Migrate to sb_publishable_ format.",
            doc_topic="anon_key_migration",
        )

    # legacy_name: an env-var / identifier reference, not a literal key.
    if finding.is_service_role_ish and finding.in_frontend_context:
        return MigrationIssue(
            finding=finding,
            severity=CRITICAL,
            reason=(
                "A service_role-style identifier is referenced from what looks like client/frontend "
                "code. Even as an env var, a privileged key referenced here risks being bundled into "
                "the browser build. Verify this isn't shipping client-side before anything else."
            ),
            doc_topic="service_role_exposure",
        )
    if finding.is_service_role_ish:
        return MigrationIssue(
            finding=finding,
            severity=HIGH,
            reason="Legacy service_role key reference. Migrate to the new sb_secret_ key before the deprecation deadline.",
            doc_topic="secret_key_rotation",
        )
    return MigrationIssue(
        finding=finding,
        severity=MEDIUM,
        reason="Legacy anon key reference. Migrate to the new sb_publishable_ key.",
        doc_topic="anon_key_migration",
    )


def sort_issues(issues: list[MigrationIssue]) -> list[MigrationIssue]:
    return sorted(issues, key=lambda iss: _SEVERITY_ORDER[iss.severity])
