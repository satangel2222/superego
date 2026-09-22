# -*- coding: utf-8 -*-
"""truthgate.integrations.jev —— Jev System-1 Fast Semantic Intent Guard Adapter.

Provides sub-350ms non-autoregressive parallel gating for AI Coding Agents
using TypeSafe AI's Jev model with deterministic offline fallback.
"""
from typing import Dict, Any, Optional
from truthgate.jev_engine import judge_assistant_text, get_client


class JevIntentGate:
    """Jev System-1 Intent Gate for TruthGate.

    Evaluates Agent output against parallel structured questions:
    - R1_fake_done: Claiming completion without execution
    - R2_destructive: Unconfirmed destructive operations
    - R5_nagging: Passive nagging and decision deferral
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 3.0):
        self.api_key = api_key
        self.timeout = timeout

    def evaluate(self, text: str) -> Dict[str, Any]:
        """Evaluate agent output text against Jev System-1 parallel questions.

        Returns:
            dict with verdict ('PASS' | 'FIRE'), fired rules, latency_ms, and probabilities.
        """
        return judge_assistant_text(text, timeout=self.timeout)

    @property
    def is_available(self) -> bool:
        """Check if Jev client is configured and available."""
        return get_client() is not None
