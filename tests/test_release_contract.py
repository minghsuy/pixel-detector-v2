from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pixel_detector

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "2.3.0"


def test_release_version_is_single_consistent_contract() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert pyproject["project"]["version"] == EXPECTED_VERSION
    assert pixel_detector.__version__ == EXPECTED_VERSION
    assert re.search(
        rf"^## \[{re.escape(EXPECTED_VERSION)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        changelog,
        flags=re.MULTILINE,
    )


def test_release_preflight_and_workflow_are_present_and_fail_closed() -> None:
    preflight = (ROOT / "scripts" / "release-preflight.sh").read_text(encoding="utf-8")
    build_constraints = (
        ROOT / "requirements" / "release-build.txt"
    ).read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert "set -euo pipefail" in preflight
    assert "uv python find 3.11" in preflight
    assert "python3 -c" not in preflight
    assert '"+refs/heads/main:refs/remotes/origin/main"' in preflight
    assert 'require_synchronized_main "release candidate"' in preflight
    assert 'require_synchronized_main "release tag"' in preflight
    assert "git ls-remote" in preflight
    assert "uv build" in preflight
    assert "--build-constraints requirements/release-build.txt" in preflight
    assert "uv export" in preflight
    assert "--locked" in preflight
    assert "--require-hashes" in preflight
    assert "uv pip install" in preflight
    assert re.search(r"pixel-detector.*--version", preflight)
    assert "hatchling==1.31.0" in build_constraints
    assert "--hash=sha256:" in build_constraints

    assert re.search(r"(?m)^\s+tags:\s*$", workflow)
    assert '"v*"' in workflow
    assert re.search(r"(?m)^permissions:\s*\{\}\s*$", workflow)
    assert "contents: write" in workflow
    action_uses = re.findall(r"(?m)^\s*uses:\s+[^@\s]+@([^#\s]+)", workflow)
    assert action_uses
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_uses)
    assert 'version: "0.9.28"' in workflow
    assert "uv sync --all-extras --python 3.11 --locked" in workflow
    assert "release-preflight.sh" in workflow
    assert '"+refs/tags/${GITHUB_REF_NAME}:refs/release-tags/current"' in workflow
    assert "git rev-list -n 1 refs/release-tags/current" in workflow
    assert 'current_commit" != "$EXPECTED_COMMIT' in workflow
    assert "EXPECTED_COMMIT: ${{ github.sha }}" in workflow
    assert "gh release create" in workflow
    assert "pypi" not in workflow.lower()


def test_release_preflight_rejects_version_drift_before_build(tmp_path: Path) -> None:
    # Fixed repository script path and fixed arguments; no untrusted input.
    result = subprocess.run(  # noqa: S603
        [
            ROOT / "scripts" / "release-preflight.sh",
            "--package",
            "2.3.1",
            tmp_path / "artifacts",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "pyproject.toml version is 2.3.0, expected 2.3.1" in result.stderr
    assert not (tmp_path / "artifacts").exists()


def test_release_preflight_rejects_tag_not_on_main_before_build(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        """#!/usr/bin/env bash
case "$1" in
  describe)
    printf 'v2.3.0\\n'
    ;;
  fetch)
    exit 0
    ;;
  rev-parse)
    if [[ "$2" == "HEAD" ]]; then
      printf 'tagged-commit\\n'
    else
      printf 'main-commit\\n'
    fi
    ;;
  *)
    exit 99
    ;;
esac
""",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)

    # Fixed repository script path and controlled test-only PATH shim.
    result = subprocess.run(  # noqa: S603
        [
            ROOT / "scripts" / "release-preflight.sh",
            "--tag",
            EXPECTED_VERSION,
            tmp_path / "artifacts",
        ],
        cwd=ROOT,
        env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "release tag commit is not synchronized with origin/main" in result.stderr
    assert not (tmp_path / "artifacts").exists()


def test_release_preflight_rejects_tampered_build_constraints(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    shutil.copytree(
        ROOT,
        project,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "dist",
        ),
    )
    constraints = project / "requirements" / "release-build.txt"
    original = constraints.read_text(encoding="utf-8")
    tampered, replacement_count = re.subn(
        r"sha256:[0-9a-f]{64}",
        f"sha256:{'0' * 64}",
        original,
    )
    assert replacement_count > 0
    constraints.write_text(tampered, encoding="utf-8")

    # Fixed copied script path and controlled cache/output locations.
    result = subprocess.run(  # noqa: S603
        [
            project / "scripts" / "release-preflight.sh",
            "--package",
            EXPECTED_VERSION,
            tmp_path / "artifacts",
        ],
        cwd=project,
        env={**os.environ, "UV_CACHE_DIR": str(tmp_path / "uv-cache")},
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode != 0
    assert "hash mismatch" in (result.stdout + result.stderr).lower()
    assert not list((tmp_path / "artifacts").glob("*.whl"))
    assert not list((tmp_path / "artifacts").glob("*.tar.gz"))
