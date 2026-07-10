#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/mnt/d/Program/cde_mapper}"
CONDA_ENV="${CONDA_ENV:-cde-mapper}"

cd "$REPO_DIR"

if command -v conda >/dev/null 2>&1; then
  :
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
fi

export CUDA_VISIBLE_DEVICES=""
export PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}"
conda run --no-capture-output -n "$CONDA_ENV" python -u scripts/audit_id_preprocess.py
