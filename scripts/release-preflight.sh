#!/usr/bin/env bash
#
# Build and verify the package artifacts used by the v2.3.0 GitHub Release.
#
# Usage:
#   scripts/release-preflight.sh --package <version> <artifact-dir>
#   scripts/release-preflight.sh --candidate <version> <artifact-dir>
#   scripts/release-preflight.sh --tag <version> <artifact-dir>
#
# --package verifies metadata and artifacts from any clean or dirty checkout.
# --candidate additionally requires synchronized main and an unused local/remote
#             tag. Run it immediately before creating the release tag.
# --tag requires HEAD to be exactly the expected tag. The tag workflow uses it.
set -euo pipefail

usage() {
  echo "usage: $0 --package|--candidate|--tag <version> <artifact-dir>" >&2
  exit 2
}

MODE="${1:-}"
EXPECTED_VERSION="${2:-}"
ARTIFACT_DIR="${3:-}"

case "$MODE" in
  --package | --candidate | --tag) ;;
  *) usage ;;
esac

if [[ ! "$EXPECTED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: version must be MAJOR.MINOR.PATCH (got: ${EXPECTED_VERSION:-empty})" >&2
  exit 2
fi

if [[ -z "$ARTIFACT_DIR" ]]; then
  usage
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

PYTHON_311="$(uv python find 3.11)"
PROJECT_VERSION="$(
  "$PYTHON_311" -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])'
)"
MODULE_VERSION="$(
  sed -nE 's/^__version__ = "([^"]+)"$/\1/p' src/pixel_detector/__init__.py
)"

if [[ "$PROJECT_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "error: pyproject.toml version is $PROJECT_VERSION, expected $EXPECTED_VERSION" >&2
  exit 1
fi

if [[ "$MODULE_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "error: pixel_detector.__version__ is $MODULE_VERSION, expected $EXPECTED_VERSION" >&2
  exit 1
fi

if ! grep -Eq "^## \[${EXPECTED_VERSION//./\\.}\] - [0-9]{4}-[0-9]{2}-[0-9]{2}$" CHANGELOG.md; then
  echo "error: CHANGELOG.md has no dated [$EXPECTED_VERSION] release heading" >&2
  exit 1
fi

EXPECTED_TAG="v${EXPECTED_VERSION}"

require_synchronized_main() {
  local context="$1"

  git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
  if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
    echo "error: $context commit is not synchronized with origin/main" >&2
    exit 1
  fi
}

if [[ "$MODE" == "--candidate" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "error: release candidate checkout is dirty" >&2
    git status --short >&2
    exit 1
  fi

  if [[ "$(git branch --show-current)" != "main" ]]; then
    echo "error: release candidate must be checked from main" >&2
    exit 1
  fi

  require_synchronized_main "release candidate"

  if git show-ref --verify --quiet "refs/tags/$EXPECTED_TAG"; then
    echo "error: local tag $EXPECTED_TAG already exists" >&2
    exit 1
  fi

  remote_tag_status=0
  git ls-remote --exit-code --tags origin "refs/tags/$EXPECTED_TAG" >/dev/null 2>&1 \
    || remote_tag_status=$?
  if [[ "$remote_tag_status" -eq 0 ]]; then
    echo "error: remote tag $EXPECTED_TAG already exists" >&2
    exit 1
  fi
  if [[ "$remote_tag_status" -ne 2 ]]; then
    echo "error: could not verify whether remote tag $EXPECTED_TAG exists" >&2
    exit 1
  fi
elif [[ "$MODE" == "--tag" ]]; then
  if [[ "$(git describe --tags --exact-match HEAD 2>/dev/null || true)" != "$EXPECTED_TAG" ]]; then
    echo "error: HEAD is not exactly tagged $EXPECTED_TAG" >&2
    exit 1
  fi
  require_synchronized_main "release tag"
fi

if [[ -d "$ARTIFACT_DIR" ]] && [[ -n "$(find "$ARTIFACT_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  echo "error: artifact directory must be absent or empty: $ARTIFACT_DIR" >&2
  exit 1
fi
mkdir -p "$ARTIFACT_DIR"
ARTIFACT_DIR="$(cd "$ARTIFACT_DIR" && pwd)"

uv build --out-dir "$ARTIFACT_DIR"

shopt -s nullglob
wheels=("$ARTIFACT_DIR"/pixel_detector-"$EXPECTED_VERSION"-*.whl)
sdists=("$ARTIFACT_DIR"/pixel_detector-"$EXPECTED_VERSION".tar.gz)
shopt -u nullglob

if [[ "${#wheels[@]}" -ne 1 ]]; then
  echo "error: expected one wheel for $EXPECTED_VERSION, found ${#wheels[@]}" >&2
  exit 1
fi
if [[ "${#sdists[@]}" -ne 1 ]]; then
  echo "error: expected one source distribution for $EXPECTED_VERSION, found ${#sdists[@]}" >&2
  exit 1
fi

SMOKE_DIR="$(mktemp -d)"
trap 'rm -rf "$SMOKE_DIR"' EXIT
uv venv --python 3.11 "$SMOKE_DIR/venv"
uv export \
  --quiet \
  --locked \
  --no-dev \
  --no-emit-project \
  --no-header \
  --format requirements.txt \
  --output-file "$SMOKE_DIR/requirements.txt"
uv pip install \
  --python "$SMOKE_DIR/venv/bin/python" \
  --require-hashes \
  --requirements "$SMOKE_DIR/requirements.txt"
uv pip install \
  --python "$SMOKE_DIR/venv/bin/python" \
  --no-deps \
  "${wheels[0]}"

"$SMOKE_DIR/venv/bin/python" - "$EXPECTED_VERSION" <<'PY'
from __future__ import annotations

import sys
from importlib.metadata import version

import pixel_detector

expected = sys.argv[1]
assert pixel_detector.__version__ == expected
assert version("pixel-detector") == expected
PY

CLI_VERSION="$("$SMOKE_DIR/venv/bin/pixel-detector" --version)"
if [[ "$CLI_VERSION" != "pixel-detector version $EXPECTED_VERSION" ]]; then
  echo "error: installed CLI reported unexpected version: $CLI_VERSION" >&2
  exit 1
fi

echo "verified pixel-detector $EXPECTED_VERSION"
echo "wheel: ${wheels[0]}"
echo "sdist: ${sdists[0]}"
