# -*- coding: utf-8 -*-
"""__main__.py —— Superego 命令行直接入口。
支持:
    python -m superego install
    python -m superego dashboard
    python -m superego status
    python -m superego detect
    python -m superego rollback
    python -m superego replay
"""
import sys
from pathlib import Path

# 确保包根目录在 sys.path 中
HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from superego.installer import main

if __name__ == "__main__":
    main()
