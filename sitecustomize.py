"""Process-wide runtime settings for Windows scientific Python stacks.

This file is imported automatically by Python during startup when the project
root is on sys.path. Set these before importing torch, onnxruntime, faiss, or
fastembed so Windows does not abort on duplicate OpenMP runtime discovery.
"""

import os


os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
