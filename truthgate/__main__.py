# -*- coding: utf-8 -*-
"""__main__.py —— TruthGate 命令行直接入口。
支持:
    python -m truthgate install
    python -m truthgate dashboard
    python -m truthgate status
    python -m truthgate detect
    python -m truthgate rollback
    python -m truthgate replay
    python -m truthgate doctor
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

try:
    from truthgate.installer import main
except ImportError:
    from installer import main

if __name__ == "__main__":
    main()
