#!/usr/bin/env python
"""Capture a secret-free dependency and runtime snapshot for Stage 0."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> dict:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {"command": list(command), "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="configs/cde-mapper-environment.json")
    args = parser.parse_args()
    pip = run(sys.executable, "-m", "pip", "freeze", "--all")
    conda = run("conda", "list", "--json")
    git_commit = run("git", "rev-parse", "HEAD")
    git_status = run("git", "status", "--porcelain")
    payload = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "git_commit": git_commit["stdout"] if git_commit["returncode"] == 0 else None,
        "git_dirty": bool(git_status["stdout"]),
        "pip_freeze": pip["stdout"].splitlines() if pip["returncode"] == 0 else [],
        "conda_packages": json.loads(conda["stdout"]) if conda["returncode"] == 0 else [],
        "errors": [item for item in (pip, conda, git_commit, git_status) if item["returncode"] != 0],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {output} ({len(payload['conda_packages'])} conda packages, {len(payload['pip_freeze'])} pip entries)")
    return 0 if not payload["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
