# -*- coding: utf-8 -*-
"""Superego (Legacy Compatibility Shim for TruthGate)."""
import warnings

warnings.warn(
    "The 'superego' package has been rebranded to 'truthgate'. "
    "Please update your imports and CLI commands to 'truthgate' / 'tg'.",
    DeprecationWarning,
    stacklevel=2,
)

from truthgate import *
from truthgate import __version__
