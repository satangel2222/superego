# -*- coding: utf-8 -*-
"""test_model_freshness_gate.py —— 物理门禁：外部大模型版本真实性与零搜索拦截测试 (Model Freshness & Live Search Gate).

【翻车形状 2026-09-24-MF】:
病根：AI 张口宣称「Google Gemini 默认推荐 gemini-2.5-flash」，把 2024/2025 年预训练静态权重当成 2026 年当期事实。
而客观世界中，2026 年 9 月 Google 已 GA 发布 Gemini 3.8 系列（gemini-3.8-flash），且正在紧锣密鼓预训练 Gemini 4。
本门禁确保：只要对外部大模型版本做出事实断言或推荐，必须在当前轮次有 search_web 或官方最新文档检索凭据，否则一律物理拦截！
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from truthgate.ag_superego_bridge import (
    check_external_model_freshness_violation,
    check_model_authenticity_violation,
    evaluate_all_structural_gates
)


class TestModelFreshnessGate(unittest.TestCase):
    """测试大模型时效性与零搜索物理拦截门禁"""

    def test_01_block_stale_gemini_claim_without_search(self):
        """【门禁 1】未执行搜索就断言/推荐 gemini-2.5-flash 或过时版本 -> 必须物理拦截"""
        text = "模型提供商推荐：Google Gemini（官方推荐 · 默认 gemini-2.5-flash）"
        tool_calls = [] # 零次搜索
        blob = ""
        user_prompt = "请问外审模型默认推荐什么？"

        vio = check_external_model_freshness_violation(text, tool_calls, blob, user_prompt)
        self.assertIsNotNone(vio, "未调用 search_web 凭空断言 gemini-2.5-flash 必须被拦截")
        self.assertIn("external-model-freshness-gate", vio)
        self.assertIn("零次执行 search_web", vio)

    def test_02_pass_fresh_model_claim_with_live_search(self):
        """【门禁 2】本轮调用了 search_web 查实最新版本 -> 放行"""
        text = "根据 Google 2026 年 9 月最新发布，推荐使用 Gemini 3.8 系列（默认 gemini-3.8-flash）"
        tool_calls = [
            {"function": {"name": "search_web", "args": {"query": "Gemini latest models Google 2026"}}}
        ]
        blob = "search_web: Gemini 3.8 Flash GA September 2026"
        user_prompt = "请问外审模型默认推荐什么？"

        vio = check_external_model_freshness_violation(text, tool_calls, blob, user_prompt)
        self.assertIsNone(vio, "已调用 search_web 取得客观凭据的回复必须放行")

    def test_03_pass_historic_lesson_quote(self):
        """【门禁 3】在复盘教训或引述历史错误时提到旧模型 -> 放行（防止误杀自省）"""
        text = "历史复盘：严禁再使用 gemini-2.5-flash 作为默认推荐，这是典型的拿过时旧知当最新错误。"
        tool_calls = []
        blob = ""
        user_prompt = "复盘刚才的错误"

        vio = check_external_model_freshness_violation(text, tool_calls, blob, user_prompt)
        self.assertIsNone(vio, "复盘与纠正语境严禁误拦")

    def test_04_pipeline_integration_intercepts_stale_model(self):
        """【门禁 4】evaluate_all_structural_gates 流水线能自动捕获 external-model-freshness-gate"""
        text = "默认推荐使用 gemini-2.5 快速审查"
        tool_calls = []
        blob = ""
        violations = evaluate_all_structural_gates(text, tool_calls, blob, user_prompt="推荐个模型")
        gate_names = [v[0] for v in violations]
        self.assertIn("external-model-freshness-gate", gate_names, f"流水线未捕获时效门禁: {gate_names}")


if __name__ == "__main__":
    unittest.main()
