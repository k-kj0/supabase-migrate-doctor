"""
scanner.py
Walks a repo and finds every place that references Supabase's legacy
JWT-based API keys (anon / service_role), whether as a literal key
value, an env var name, or a client-init call.

This is intentionally regex/heuristic based, not AST-based - it needs
to work across .env, .js, .ts, .jsx, .tsx, .py, .json, .yml files with
one implementation. AST parsing per-language is a reasonable v2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SCAN_EXTENSIONS = {
    ".env", ".js", ".jsx", ".ts", ".tsx", ".py", ".json", ".yml", ".yaml",
    ".toml", ".txt", ".md", ".env.local", ".env.production",
}

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next"}

# A legacy Supabase key is a JWT: header.payload.signature, base64url segments.
LEGACY_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")

# New-format keys - used to positively confirm a project HAS migrated a given usage.
NEW_PUBLISHABLE_RE = re.compile(r"\bsb_publishable_[A-Za-z0-9_-]{10,}\b")
NEW_SECRET_RE = re.compile(r"\bsb_secret_[A-Za-z0-9_-]{10,}\b")

# Env-var / identifier names that reference legacy keys even when the
# literal value isn't committed (the far more common real-world case).
LEGACY_NAME_RE = re.compile(
    r"\b("
    r"SUPABASE_ANON_KEY|SUPABASE_SERVICE_ROLE_KEY|SUPABASE_KEY|"
    r"NEXT_PUBLIC_SUPABASE_ANON_KEY|VITE_SUPABASE_ANON_KEY|"
    r"REACT_APP_SUPABASE_ANON_KEY|EXPO_PUBLIC_SUPABASE_ANON_KEY|"
    r"SUPABASE_SERVICE_KEY|SUPABASE_SERVICE_ROLE"
    r")\b"
)

# Frontend / client-bundled context signals - if a legacy reference shows
# up near these, risk goes up because it may ship to the browser.
FRONTEND_SIGNALS_RE = re.compile(
    r"(NEXT_PUBLIC_|VITE_|REACT_APP_|EXPO_PUBLIC_|/src/|/public/|\.jsx|\.tsx|createClient\()"
)

SERVICE_ROLE_HINT_RE = re.compile(r"service_role|SERVICE_ROLE|service-role", re.IGNORECASE)


@dataclass
class Finding:
    file: str
    line_no: int
    line: str
    kind: str          # "literal_jwt" | "legacy_name" | "new_format"
    is_service_role_ish: bool
    in_frontend_context: bool

    def key(self):
        return (self.file, self.line_no, self.kind)


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0


def _iter_source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in SCAN_EXTENSIONS or path.name.startswith(".env"):
            yield path


def scan_repo(root: str | Path) -> ScanResult:
    root = Path(root)
    result = ScanResult()

    for path in _iter_source_files(root):
        result.files_scanned += 1
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue

        rel = str(path.relative_to(root))

        for i, line in enumerate(text.splitlines(), start=1):
            is_frontend = bool(FRONTEND_SIGNALS_RE.search(line)) or any(
                seg in rel for seg in ("src/", "public/", "client/")
            )
            service_ish = bool(SERVICE_ROLE_HINT_RE.search(line))

            if LEGACY_JWT_RE.search(line):
                result.findings.append(Finding(rel, i, line.strip(), "literal_jwt", service_ish, is_frontend))
            elif LEGACY_NAME_RE.search(line):
                result.findings.append(Finding(rel, i, line.strip(), "legacy_name", service_ish, is_frontend))
            elif NEW_PUBLISHABLE_RE.search(line) or NEW_SECRET_RE.search(line):
                result.findings.append(Finding(rel, i, line.strip(), "new_format", service_ish, is_frontend))

    return result
