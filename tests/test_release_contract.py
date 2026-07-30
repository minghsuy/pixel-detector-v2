from __future__ import annotations

import re
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
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert "set -euo pipefail" in preflight
    assert "git ls-remote" in preflight
    assert "uv build" in preflight
    assert "uv export" in preflight
    assert "--locked" in preflight
    assert "--require-hashes" in preflight
    assert "uv pip install" in preflight
    assert re.search(r"pixel-detector.*--version", preflight)

    assert re.search(r"(?m)^\s+tags:\s*$", workflow)
    assert '"v*"' in workflow
    assert re.search(r"(?m)^permissions:\s*\{\}\s*$", workflow)
    assert "contents: write" in workflow
    assert "release-preflight.sh" in workflow
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
