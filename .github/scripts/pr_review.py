#!/usr/bin/env python3
"""
Advisory AI code reviewer for PRLifts pull requests.

Fetches the PR diff, sends it to Claude with ARCHITECTURE.md and STANDARDS.md
as context, and posts a structured review comment. The workflow always exits 0
so a review result never blocks merging.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

CHARS_PER_TOKEN = 4
DIFF_TOKEN_LIMIT = 6_000
DIFF_CHAR_LIMIT = DIFF_TOKEN_LIMIT * CHARS_PER_TOKEN

# Path substrings that indicate security-sensitive content within the diff.
SECURITY_PATTERNS = (
    "auth",
    "delet",
    "sync",
    "rls",
    "migrat",
    "password",
    "token",
    "secret",
    "credential",
    "permission",
    "role",
    "biometric",
    "consent",
    "photo",
)

SYSTEM_PROMPT = (
    "You are an expert code reviewer for PRLifts, an iOS + iPadOS fitness tracking app. "
    "You enforce the project's architectural rules and engineering standards strictly. "
    "Flag IDOR risks explicitly: any endpoint or query that accesses cross-user data "
    "without returning 404 is a **critical** security finding. "
    "Be specific — cite file paths and approximate line numbers when relevant."
)

REVIEW_FORMAT = """\
Produce your review in exactly this format — no preamble, no trailing text:

## AI Code Review — Advisory

> This review is generated automatically and is advisory only. It does not block merging.

### Security
Findings on authentication, authorisation, IDOR risks (flag any cross-user data access \
that does not return 404 as **critical**), injection, data exposure, RLS gaps, \
photo/biometric data handling. Write "No issues found." if clean.

### Architecture Decisions
Findings on compliance with ARCHITECTURE.md rules. Cite decision numbers where applicable. \
Flag layer violations (iOS calling backend directly, AI keys outside backend, etc.) and \
missing async patterns. Write "No issues found." if clean.

### Standards
Findings on compliance with STANDARDS.md — including the §5.7 artifact requirement, \
schema pairing rule (§5.6), query standards (§5.5), and any other applicable sections. \
Write "No issues found." if clean.

### General
Code quality, naming, test coverage, missing edge cases, and anything else worth raising. \
Write "No issues found." if clean.\
"""


def _github_request(url: str, accept: str) -> bytes:
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def fetch_pr_metadata() -> dict:
    pr_number = os.environ["PR_NUMBER"]
    repo = os.environ["REPO"]
    data = _github_request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        "application/vnd.github+json",
    )
    return json.loads(data)


def fetch_diff() -> str:
    pr_number = os.environ["PR_NUMBER"]
    repo = os.environ["REPO"]
    data = _github_request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        "application/vnd.github.diff",
    )
    return data.decode("utf-8")


def split_diff_by_file(diff: str) -> dict[str, str]:
    files: dict[str, str] = {}
    current_file: str | None = None
    lines: list[str] = []

    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current_file is not None:
                files[current_file] = "".join(lines)
            # "diff --git a/path b/path" — take the b/ side
            current_file = line.split(" ")[-1].strip()[2:]
            lines = [line]
        elif current_file is not None:
            lines.append(line)

    if current_file is not None:
        files[current_file] = "".join(lines)

    return files


def is_security_sensitive(path: str) -> bool:
    lower = path.lower()
    return any(p in lower for p in SECURITY_PATTERNS)


def build_diff_context(diff: str) -> str:
    """Return diff as-is when within token budget; otherwise prioritise security files."""
    if len(diff) <= DIFF_CHAR_LIMIT:
        return diff

    file_diffs = split_diff_by_file(diff)
    security = {k: v for k, v in file_diffs.items() if is_security_sensitive(k)}
    other = {k: v for k, v in file_diffs.items() if not is_security_sensitive(k)}

    parts: list[str] = []

    if security:
        parts.append("# Security-sensitive files — reviewed in full\n")
        for fname, content in security.items():
            parts.append(f"\n## {fname}\n{content}")

    if other:
        parts.append(
            "\n\n# Other changed files — diff exceeded ~6 000-token limit; summarised\n"
        )
        for fname, content in other.items():
            added = sum(
                1 for ln in content.splitlines()
                if ln.startswith("+") and not ln.startswith("+++")
            )
            removed = sum(
                1 for ln in content.splitlines()
                if ln.startswith("-") and not ln.startswith("---")
            )
            parts.append(f"- `{fname}` (+{added} / -{removed} lines)\n")

    return "".join(parts)


def read_doc(path: str) -> str:
    try:
        with open(path) as fh:
            return fh.read()
    except FileNotFoundError:
        return f"[{path} not found in this checkout]"


def post_comment(body: str) -> None:
    pr_number = os.environ["PR_NUMBER"]
    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body", body],
        check=True,
    )


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ANTHROPIC_API_KEY not set — skipping AI review.", file=sys.stderr)
        sys.exit(0)

    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed — skipping AI review.", file=sys.stderr)
        sys.exit(0)

    architecture_md = read_doc("docs/ARCHITECTURE.md")
    standards_md = read_doc("docs/STANDARDS.md")

    pr_meta = fetch_pr_metadata()
    pr_title = pr_meta.get("title", "")
    pr_body = (pr_meta.get("body") or "").strip()

    raw_diff = fetch_diff()
    diff_context = build_diff_context(raw_diff)

    # ARCHITECTURE.md and STANDARDS.md are static across PRs — cache them so
    # back-to-back CI runs within the 5-minute TTL avoid re-processing ~32K tokens.
    user_content = [
        {
            "type": "text",
            "text": "ARCHITECTURE.md — source of truth for architectural decisions:\n\n" + architecture_md,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": "STANDARDS.md — engineering standards:\n\n" + standards_md,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": (
                f"PR Title: {pr_title}\n\n"
                f"PR Description:\n{pr_body or '(none)'}\n\n"
                f"Diff:\n{diff_context}\n\n"
                + REVIEW_FORMAT
            ),
        },
    ]

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        betas=["prompt-caching-2024-07-31"],
    )

    review_text = message.content[0].text
    post_comment(review_text)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        # Advisory reviews must never fail CI. Log the error and exit cleanly.
        print(f"AI review error (non-blocking): {exc}", file=sys.stderr)
        sys.exit(0)
