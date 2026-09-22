# -*- coding: utf-8 -*-
"""Superego (Legacy Compatibility Shim for TruthGate)."""
import sys
import warnings
import importlib.util

warnings.warn(
    "The 'superego' package has been rebranded to 'truthgate'. "
    "Please update your imports and CLI commands to 'truthgate' / 'tg'.",
    DeprecationWarning,
    stacklevel=2,
)

class _SuperegoAliasFinder:
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname.startswith("superego."):
            sub = fullname[len("superego."):]
            try:
                return importlib.util.find_spec(f"truthgate.{sub}")
            except Exception:
                return None
        return None

if not any(isinstance(f, type) and f.__name__ == "_SuperegoAliasFinder" for f in sys.meta_path):
    sys.meta_path.insert(0, _SuperegoAliasFinder)

import truthgate
from truthgate import *
from truthgate import __version__
