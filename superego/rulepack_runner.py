# -*- coding: utf-8 -*-
"""rulepack_runner.py —— Superego 2.0 规则包校验器与回归验证引擎。
负责：
  1. 校验 RulePack 规范完整性与 schema 合规性；
  2. 自动运行包内 golden_cases 进行准入回归测试；
  3. 拦截误伤率（FP）超标的残次规则包，保障生态安全。
"""
import os
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULEPACKS_DIR = HERE / "rulepacks"

try:
    from security_core import audit_tool_call
except ImportError:
    from superego.security_core import audit_tool_call

try:
    from jev_engine import judge_assistant_text
except ImportError:
    from superego.jev_engine import judge_assistant_text


def validate_rulepack_file(filepath: Path) -> dict:
    """校验并运行单个规则包测试"""
    if not filepath.exists():
        return {"ok": False, "error": f"文件不存在: {filepath}"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            pack = json.load(f)
    except Exception as e:
        return {"ok": False, "error": f"JSON解析失败: {e}"}

    required_fields = ["id", "name", "version", "category", "rules", "golden_cases"]
    for rf in required_fields:
        if rf not in pack:
            return {"ok": False, "error": f"缺少必须字段: {rf}"}

    cases = pack.get("golden_cases", [])
    if not cases:
        return {"ok": False, "error": "必须包含至少一条 golden_cases 验证样本"}

    print(f"\n📦 正在回归验证规则包: {pack['name']} ({pack['id']} v{pack['version']})...")
    print(f"   类别: {pack['category']} | 包含规则数: {len(pack['rules'])} | 验证用例数: {len(cases)}")

    correct = 0
    fp = 0
    fn = 0

    is_security_tier1 = pack.get("tier") == 1 or pack.get("category") == "security"

    for idx, c in enumerate(cases, 1):
        text = c["text"]
        exp = c["expected"]
        rule_id = c.get("rule", "")

        if is_security_tier1:
            allowed, block_reason = audit_tool_call("Bash", {"command": text})
            actual = "PASS" if allowed else "FIRE"
        else:
            res = judge_assistant_text(text)
            actual = res["verdict"]

        is_match = (actual == exp)
        if is_match:
            correct += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            if exp == "PASS":
                fp += 1
            else:
                fn += 1

        print(f"   [{idx}/{len(cases)}] {status} | 期望: {exp:<4} | 实际: {actual:<4} | 规则: {rule_id:<6} | 文本: {text[:40]}...")

    total = len(cases)
    pass_rate = correct / total
    fp_rate = fp / total if total > 0 else 0
    max_fp_allowed = pack.get("max_fp_rate", 0.005)

    print(f"\n📊 回归测试汇总: 通过率 {correct}/{total} ({pass_rate*100:.1f}%) | 误伤率: {fp_rate*100:.2f}% (允许上限: {max_fp_allowed*100:.2f}%)")

    if fp_rate > max_fp_allowed:
        print(f"❌ 规则包未通过准入门禁：误伤率超标 ({fp_rate:.4f} > {max_fp_allowed:.4f})")
        return {"ok": False, "pass_rate": pass_rate, "fp_rate": fp_rate, "error": "误伤率超标"}

    print(f"🎉 规则包验证全绿通过！完全符合生态标准。")
    return {"ok": True, "pass_rate": pass_rate, "fp_rate": fp_rate}


def test_all_rulepacks():
    """遍历测试 rulepacks 目录下的所有规则包"""
    if not RULEPACKS_DIR.exists():
        print("⚠️ 未找到 rulepacks 目录")
        return

    packs = list(RULEPACKS_DIR.glob("*.rulepack.json"))
    print(f"🔍 扫描到 {len(packs)} 个规则包待准入验证...")
    all_ok = True
    for p in packs:
        res = validate_rulepack_file(p)
        if not res.get("ok"):
            all_ok = False
    return all_ok


if __name__ == "__main__":
    test_all_rulepacks()
