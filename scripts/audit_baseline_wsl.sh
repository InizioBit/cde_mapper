#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CDE_MAPPER_CONDA_ENV:-cde-mapper}"
REPO_DIR="${CDE_MAPPER_REPO_DIR:-/mnt/d/Program/cde_mapper}"
PY_SCRIPT="scripts/baseline_smoke.py"

find_conda() {
  if command -v conda >/dev/null 2>&1; then
    command -v conda
    return 0
  fi

  local candidates=(
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "/opt/conda/etc/profile.d/conda.sh"
  )

  for conda_sh in "${candidates[@]}"; do
    if [[ -f "$conda_sh" ]]; then
      # shellcheck source=/dev/null
      source "$conda_sh"
      if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
      fi
    fi
  done

  return 1
}

cd "$REPO_DIR"

export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${HF_HOME:-$REPO_DIR/resources/models}"

if ! find_conda >/dev/null; then
  echo "ERROR: conda tidak ditemukan di shell WSL non-interaktif." >&2
  echo "Coba jalankan manual di WSL: source ~/miniconda3/etc/profile.d/conda.sh" >&2
  exit 2
fi

if ! conda env list | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
  echo "ERROR: conda env '$ENV_NAME' tidak ditemukan di WSL." >&2
  conda env list >&2
  exit 3
fi

conda run --no-capture-output -n "$ENV_NAME" python -u "$PY_SCRIPT" \
  --input-file data/input/baseline_smoke.csv \
  --mapping-file data/input/mapping_templates.json \
  --output-json Riset/baseline_audit_result.json
