#!/usr/bin/env python
"""Tahap 0 baseline audit smoke test.

This script avoids network and LLM calls. It checks that the local baseline
building blocks can be imported, the custom CSV loader works, mapping templates
are valid JSON, and the local reservoir can be initialized in a temporary DB.
"""

from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


def _result(name: str, ok: bool, detail: str = "") -> dict:
    return {"check": name, "ok": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local baseline audit checks.")
    parser.add_argument("--input-file", default="data/input/baseline_smoke.csv")
    parser.add_argument("--mapping-file", default="data/input/mapping_templates.json")
    parser.add_argument("--output-json", default="Riset/baseline_audit_result.json")
    args = parser.parse_args()

    started = time.time()
    print("[baseline-smoke] starting", flush=True)
    repo = Path.cwd()
    checks: list[dict] = []
    loaded_queries = 0
    database_rows = 0
    mapping_data: dict = {}

    # The audit does not need GPU. Some baseline imports initialize torch-backed
    # components, so force CPU-visible mode before importing project modules.
    import os

    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("HF_HOME", str(repo / "resources/models"))

    for runtime_dir in ("resources/logs", "resources/models", "data/output"):
        (repo / runtime_dir).mkdir(parents=True, exist_ok=True)
    print("[baseline-smoke] runtime directories ready", flush=True)

    sys.path.insert(0, str(repo))

    try:
        print("[baseline-smoke] importing baseline modules", flush=True)
        import rag.param as param
        from rag.data_loader import load_data
        from rag.sql import DataManager

        checks.append(_result("import_baseline_modules", True, "rag.param, rag.data_loader, rag.sql"))
    except Exception as exc:  # pragma: no cover - diagnostic script
        checks.append(_result("import_baseline_modules", False, repr(exc)))
        _write_report(args.output_json, started, checks, loaded_queries, database_rows)
        return 1

    input_path = repo / args.input_file
    checks.append(_result("smoke_input_exists", input_path.exists(), str(input_path)))

    try:
        print("[baseline-smoke] loading custom smoke data", flush=True)
        data, is_mapped = load_data(str(input_path), load_custom=True)
        loaded_queries = len(data or [])
        ok = bool(data) and not is_mapped
        checks.append(_result("load_custom_smoke_data", ok, f"queries={loaded_queries}, is_mapped={is_mapped}"))
    except Exception as exc:  # pragma: no cover - diagnostic script
        checks.append(_result("load_custom_smoke_data", False, repr(exc)))

    mapping_path = repo / args.mapping_file
    try:
        print("[baseline-smoke] reading mapping template json", flush=True)
        with mapping_path.open("r", encoding="utf-8") as handle:
            mapping_data = json.load(handle)
        has_database_data = isinstance(mapping_data.get("database_data"), list)
        checks.append(
            _result(
                "mapping_templates_json",
                has_database_data,
                f"path={mapping_path}, top_level_keys={len(mapping_data)}, database_data={len(mapping_data.get('database_data', []))}",
            )
        )
    except Exception as exc:  # pragma: no cover - diagnostic script
        checks.append(_result("mapping_templates_json", False, repr(exc)))

    try:
        print("[baseline-smoke] initializing temporary reservoir", flush=True)
        with tempfile.TemporaryDirectory(prefix="cde_mapper_reservoir_") as tmpdir:
            db_path = Path(tmpdir) / "variables_smoke.db"
            seed_path = Path(tmpdir) / "mapping_seed_smoke.json"
            seed_rows = (mapping_data.get("database_data") or [])[:10]
            seed_path.write_text(json.dumps({"database_data": seed_rows}), encoding="utf-8")
            db = DataManager(str(db_path), initial_json=str(seed_path))
            db.cursor.execute("SELECT COUNT(*) FROM concept_mappings")
            database_rows = int(db.cursor.fetchone()[0])
            db.close_connection()
            checks.append(_result("reservoir_temp_sqlite", database_rows > 0, f"rows={database_rows}"))
    except Exception as exc:  # pragma: no cover - diagnostic script
        checks.append(_result("reservoir_temp_sqlite", False, repr(exc)))

    checks.append(
        _result(
            "import_retrieval_stack",
            True,
            "skipped by design: full retrieval imports can initialize embedding/LLM dependencies; use run.py for full inference",
        )
    )

    ok_all = all(item["ok"] for item in checks)
    _write_report(args.output_json, started, checks, loaded_queries, database_rows)
    return 0 if ok_all else 1


def _write_report(output_json: str, started: float, checks: list[dict], loaded_queries: int, database_rows: int) -> None:
    payload = {
        "script": "scripts/baseline_smoke.py",
        "python": sys.version,
        "platform": platform.platform(),
        "duration_seconds": round(time.time() - started, 3),
        "loaded_queries": loaded_queries,
        "reservoir_rows": database_rows,
        "checks": checks,
        "ok": all(item["ok"] for item in checks),
    }
    out = Path(output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
