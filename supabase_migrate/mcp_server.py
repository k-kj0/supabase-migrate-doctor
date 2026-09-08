"""
mcp_server.py
Exposes supabase-migrate-doctor as an MCP (Model Context Protocol) server -
so an AI assistant like Claude Desktop, Claude Code, or Cursor can call
`scan_repo` directly as a tool, instead of you running the CLI by hand.

Run it locally with: python -m supabase_migrate.mcp_server
Or point an MCP client's config at this file - see README's MCP section.
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .cli import build_report

mcp = MCPServer(
    name="supabase-migrate-doctor",
    instructions=(
        "Scans a codebase for legacy Supabase API key usage (the "
        "anon/service_role JWT keys being deprecated end of 2026) and "
        "explains, with a citation, what to do about each finding."
    ),
)


@mcp.tool()
def scan_repo(path: str, explain: bool = True) -> dict:
    """
    Scan a local repository path for legacy Supabase API key usage.

    Args:
        path: Filesystem path to the repository to scan.
        explain: Whether to include a grounded explanation for each finding
            (set False for a faster, bare-findings scan).

    Returns:
        A dict with files_scanned, counts by severity, and a list of
        issues - each with file, line, snippet, severity, reason, and
        (if explain=True) a cited explanation.
    """
    return build_report(path, explain_findings=explain)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
