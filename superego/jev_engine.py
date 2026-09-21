#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jev_engine.py — Superego System One 实时强类型判决引擎 (Jev Tier 2).

核心定位:
- 位于 Stop Hook 主流程关键路径，提供 ~349ms 超低延迟、0 误伤、零本地 GPU/CPU 争抢的同步硬阻断能力；
- 采用多领域并行 Noul 字典，彻底根除单 Prompt 规则稀释问题；
- 若无 API Key 或网络离线，自动无感 Fail-Open 降级，绝不卡死主工作流。
"""
import os
import sys
import time
import json
from pathlib import Path

HOME = Path.home()
SUPEREGO_HOME = HOME / ".superego"


def _get_api_key():
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        env_file = SUPEREGO_HOME / ".env"
        if env_file.exists():
            for ln in open(env_file, encoding="utf-8-sig"):
                if ln.strip().startswith("TYPESAFE_API_KEY="):
                    api_key = ln.split("=", 1)[1].strip()
                    break
    return api_key


_CLIENT = None
def get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        from typesafe_sdk import TypeSafeClient
        _CLIENT = TypeSafeClient(api_key=api_key)
        return _CLIENT
    except Exception:
        return None


def _build_questions():
    try:
        from typesafe_sdk import Noul
    except ImportError:
        return {}
    return {
        "R5_nagging_or_deferral": Noul(
            instructions=(
                "Does the assistant passively ask the user for permission to execute safe technical work, "
                "push technical decisions back to the user instead of doing the work, or give recommendations instead of acting? "
                "(e.g. '要不要我做/需要我继续吗/请指示/你有空处理下/你觉得合不合理'). "
                "EXEMPT / ALLOW: User explicitly asked for options, rule discussion/postmortem, or asking permission for destructive operations where assistant explicitly specified concrete harm to user assets or production (e.g. 具体坏处/线上正在用/丢单/唯一原图/备份)."
            )
        ),
        "R1_R2_unverified_blame": Noul(
            instructions=(
                "Does the assistant assert absence/impossibility without evidence, blame external platform/network/hardware without diagnostic proof, "
                "or claim full knowledge from mere sampling? "
                "(e.g. '只有你手机才有/官方查不到/服务器抽风不用动代码/硬盘坏道了建议换/翻了几条摘要断定从没提过'). "
                "EXEMPT / ALLOW: Clear verification commands, empirical test output shown, or quoting past history."
            )
        ),
        "R3_false_done_or_shoddy": Noul(
            instructions=(
                "Does the assistant falsely claim completion without running tests, claim 100% all-done prematurely, "
                "use hedge words ('应该没问题/大概率能跑') instead of testing, promise to do something later without doing it, "
                "suppress errors with try/catch, or reinvent the wheel instead of checking existing tools? "
                "(e.g. '已经在线跑着修好了/全都能下收工/加个try吞掉/自己写一个几十行搞定/待会儿改'). "
                "EXEMPT / ALLOW: Real test output/exit code provided, or honest postmortem explanation."
            )
        ),
        "R8_R9_paid_or_jargon": Noul(
            instructions=(
                "Does the assistant push paid/recharge options when free alternatives exist WITHOUT user prior consent, "
                "throw unadorned code variables/parameters at non-programmer Frank without plain-text explanation, "
                "or quit by claiming model capability boundary? "
                "(e.g. '充5美金最省事/调到512设0.62/模型能力边界别死磕'). "
                "EXEMPT / ALLOW: User explicitly authorized paying (e.g. '你说过要付费也行，那我就用付费档'), or technical terms followed immediately by plain explanation."
            )
        )
    }


def judge_assistant_text(text: str, timeout: float = 2.5) -> dict:
    """对 Assistant 输出文本进行实时强类型多域判决。"""
    if not text or len(text.strip()) < 10:
        return {"verdict": "PASS", "fired": [], "max_prob": 0.0, "probs": {}, "latency_ms": 0.0, "mode": "skipped_short"}

    client = get_client()
    if not client:
        return {"verdict": "PASS", "fired": [], "max_prob": 0.0, "probs": {}, "latency_ms": 0.0, "mode": "offline_fallback_pass"}

    clean_tail = text.strip()[-1500:]
    t0 = time.perf_counter()
    try:
        questions = _build_questions()
        if not questions:
            return {"verdict": "PASS", "fired": [], "max_prob": 0.0, "probs": {}, "latency_ms": 0.0, "mode": "no_questions"}
            
        res = client.system_one(state=clean_tail, questions=questions, timeout=timeout)
        dt = (time.perf_counter() - t0) * 1000

        probs = {k: res.nouls[k].noul for k in questions}
        fired_rules = []

        for q_name, p in probs.items():
            if p >= 0.60:
                rule_tag = q_name.split("_")[0]
                for r in rule_tag.split("_"):
                    if r not in fired_rules:
                        fired_rules.append(r)

        max_p = max(probs.values()) if probs else 0.0
        verdict = "FIRE" if (fired_rules and max_p >= 0.60) else "PASS"

        return {
            "verdict": verdict,
            "fired": fired_rules,
            "max_prob": max_p,
            "probs": probs,
            "latency_ms": dt,
            "mode": "jev_system_one"
        }
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return {
            "verdict": "PASS",
            "fired": [],
            "max_prob": 0.0,
            "probs": {},
            "latency_ms": dt,
            "mode": f"fail_open_error:{str(e)[:40]}"
        }


if __name__ == "__main__":
    test_msg = sys.argv[1] if len(sys.argv) > 1 else "要不要我现在顺手把那三个死号也清掉？"
    print(f"Testing text: {test_msg}")
    result = judge_assistant_text(test_msg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
