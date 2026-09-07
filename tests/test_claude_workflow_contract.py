from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _without_comment_lines(text: str) -> str:
    """Drop full-line `#` comments before substring checks.

    A file-wide substring search over raw YAML text false-positives on prose
    that mentions the very thing it's warning against ("NOT self-hosted",
    "NOT secrets: inherit") -- these files are full of exactly that kind of
    comment. This does not handle trailing inline comments (`key: value  #
    note`), which none of these files use for the keys checked here.
    """
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )


def test_claude_responder_never_targets_self_hosted() -> None:
    workflow = (ROOT / ".github" / "workflows" / "claude.yml").read_text(encoding="utf-8")
    code = _without_comment_lines(workflow)

    assert "self-hosted" not in code
    assert 'runs-on: \'"ubuntu-latest"\'' in code
    assert not re.search(r"(?m)^\s*secrets:\s*inherit\s*$", code)
    assert "CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}" in code

    triggers = re.search(r"(?m)^on:\s*\n((?:^ {2}.*\n?)*)", code)
    assert triggers, "no top-level `on:` block found"
    assert "issue_comment:" in triggers.group(1)


def test_claude_review_bridge_is_hosted_scoped_and_fails_closed() -> None:
    workflow = (ROOT / ".github" / "workflows" / "claude-code-review.yml").read_text(
        encoding="utf-8"
    )
    code = _without_comment_lines(workflow)

    # Runner class: this is a public repo, so a fork PR must never reach a
    # self-hosted runner.
    assert "self-hosted" not in code
    assert re.search(r"(?m)^\s*runs-on:\s*ubuntu-latest\s*$", code)

    # Explicit timeout -- no unbounded job.
    assert re.search(r"(?m)^\s*timeout-minutes:\s*\d+\s*$", code)

    # Least-privilege: this job authenticates via BRIDGE_PAT (a PAT, not the
    # job token), so the job's own GITHUB_TOKEN permissions must be empty.
    assert re.search(r"(?m)^\s*permissions:\s*\{\}\s*$", code)

    # Fork PRs don't get repo secrets from a `pull_request` event -- the job
    # must skip them rather than fail with a misleading "secret not set".
    assert "github.event.pull_request.head.repo.full_name == github.repository" in code

    # Fails loudly, not silently, when the PAT truly is missing (same-repo PR).
    assert 'if [[ -z "${GH_TOKEN:-}" ]]' in code
    assert "BRIDGE_PAT secret is not set on this repo" in code
    # The scope in the error message must name this repo, not a copy-pasted
    # reference repo -- a wrong scope here silently misconfigures the PAT.
    assert "scoped only to pixel-detector-v2" in code

    # Marker-safe cleanup: deletion is scoped to the bridge's own marker, so a
    # human-authored `@claude review` comment (no marker) is never touched.
    assert re.search(r"MARKER: '<!-- [^']+ -->'", code), "no MARKER definition found"
    assert "select(.body | contains($marker))" in code
    assert "gh api -X DELETE" in code


def test_actionlint_workflow_validates_every_pr_with_pinned_digest() -> None:
    workflow = (ROOT / ".github" / "workflows" / "actionlint.yml").read_text(encoding="utf-8")
    code = _without_comment_lines(workflow)

    assert re.search(r"(?m)^on:\s*\n\s*pull_request:\s*$", code)
    assert not re.search(r"(?m)^\s*paths:", code)  # hangs a required check on skip
    assert re.search(r"(?m)^\s*runs-on:\s*ubuntu-latest\s*$", code)
    assert re.search(r"(?m)^\s*timeout-minutes:\s*\d+\s*$", code)
    assert re.search(r"rhysd/actionlint@sha256:[0-9a-f]{64}", code)
