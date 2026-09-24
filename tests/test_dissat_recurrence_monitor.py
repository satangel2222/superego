# -*- coding: utf-8 -*-
"""test_dissat_recurrence_monitor.py —— 人类纠错批评与假阴性(False Negative)自愈门禁物理单测"""
import sys
import os
import sqlite3
import unittest
from pathlib import Path

# Add truthgate package to path
REPO_DIR = Path(__file__).resolve().parent.parent
TG_DIR = REPO_DIR / "truthgate"
if str(TG_DIR) not in sys.path:
    sys.path.insert(0, str(TG_DIR))

from postmortem_guard import detect_reprimand, audit_postmortem_compliance
from verdict_monitor import (
    record_verdict,
    check_user_reprimand_and_record_false_negative,
    get_monitor_stats,
    MONITOR_DB
)
from ag_superego_bridge import evaluate_all_structural_gates


class TestDissatRecurrenceMonitor(unittest.TestCase):

    def test_01_detect_frank_reprimands(self):
        """测试对 Frank 真实指正批评语境的高灵敏度嗅探"""
        prompts = [
            "既然我随便都找到有问题，你却看不到有问题的主要原因和根因是什么？你应该怎么彻底解决做什么？",
            "17925是正确端口？是不是搞错了什么？还是我本地版和Github版没完整对齐，现在别人用着的是什么？",
            "凡事我有再次提醒，gate没开火就是有问题，这个gate有没有审查自动Monitor?",
            "你又错了，根本没修好！",
            "做完对的步骤了吗？还在糊弄我！"
        ]
        for p in prompts:
            res = detect_reprimand(p)
            self.assertIsNotNone(res, f"未能嗅探到指正批评: {p}")
            self.assertTrue(res.get("is_reprimand"), f"未能判定为 reprimand: {p}")
            print(f"  [✓] 成功命中指正: {res.get('trigger_word')} -> {p[:30]}...")

    def test_02_postmortem_compliance_audit(self):
        """测试未履职 5 步自愈协议时的硬打回拦截"""
        rep_info = {"is_reprimand": True, "trigger_word": "既然我随便都找到有问题"}

        # 1. 狡辩安抚型回复（无形状、无机器防御）-> 必须打回 BLOCK
        excuse_reply = "对不起 Frank，其实是因为之前的脚本没对齐端口，我现在马上改。"
        res = audit_postmortem_compliance(excuse_reply, rep_info)
        self.assertTrue(res.get("fired"), "狡辩安抚回复必须被 postmortem_guard 拦截！")
        self.assertEqual(res.get("rule"), "POSTMORTEM_AUTO_GUARD")

        # 2. 完整 5 步自愈型回复（包含错误形状 + 机器能否防御代码落地）-> 予以放行 PASS
        compliant_reply = """
### 1. 不辩解认错
承认事实：之前的比对流于表面文件检查。
### 2. 归纳错误形状
本次发作的错误形状属于典型：`Inference as Fact` + `Toy Comparison Fallacy`。
### 3. 查复发
历史在 lessons.md 中曾记录过类似端口残留。
### 4. 机器能否防御
机器能否防御：绝对能防！通过 deep_parity_auditor 与 AST 变量静态扫描，断言 100% 拦截。
### 5. 物理落地门禁与单测
物理落地门禁代码已写入 postmortem_guard.py，并编写单测 tests/test_dissat_recurrence_monitor.py。
"""
        res_ok = audit_postmortem_compliance(compliant_reply, rep_info)
        self.assertFalse(res_ok.get("fired"), "符合5步自愈协议的规范交付必须放行！")

    def test_03_false_negative_recording_and_stats(self):
        """测试用户纠错时，上一轮 PASS 记录自动被对账标记为 False Negative"""
        # 先模拟上一轮产出一个 PASS 裁决
        vid = record_verdict(
            turn_type="test_turn",
            verdict="PASS",
            fired_rules=[],
            reasons=[],
            mode="test_mode",
            latency_ms=10.0,
            user_prompt="这个端口对吗？",
            assistant_text="全部已经配置好了，运行正常。"
        )
        self.assertGreater(vid, 0)

        # 模拟下一轮用户纠错批评
        user_correction = "既然我随便都找到有问题，你却看不到有问题的主要原因和根因是什么？"
        fn_res = check_user_reprimand_and_record_false_negative(user_correction)
        self.assertIsNotNone(fn_res, "必须捕获到 False Negative")
        self.assertEqual(fn_res.get("verdict_id"), vid)

        # 验证数据库物理字段状态
        with sqlite3.connect(MONITOR_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT is_false_negative FROM verdict_records WHERE id=?", (vid,))
            row = cur.fetchone()
            self.assertEqual(row[0], 1, "上一轮 PASS 记录的 is_false_negative 必须被置为 1！")

            cur.execute("SELECT COUNT(*) FROM false_negatives WHERE verdict_id=?", (vid,))
            count = cur.fetchone()[0]
            self.assertGreaterEqual(count, 1, "false_negatives 审计表中必须插入对账案卷！")

        # 验证双向指标统计 (Precision + Recall)
        stats = get_monitor_stats()
        self.assertIn("false_negatives", stats)
        self.assertIn("recall_rate", stats)
        print(f"  [✓] 实时监控指标: Precision={stats['precision_rate']}%, Recall={stats['recall_rate']}%, FN={stats['false_negatives']}")

    def test_04_bridge_structural_gate_integration(self):
        """测试在 ag_superego_bridge 的 evaluate_all_structural_gates 中全真集成生效"""
        user_prompt = "既然我随便都找到有问题，你却看不到有问题的主要原因？"
        bad_text = "我刚才看了一下，端口好像有点不对，我现在帮你看看。"

        violations = evaluate_all_structural_gates(
            text=bad_text,
            tool_calls=[],
            blob="",
            user_prompt=user_prompt,
            conv_id="test-conv",
            stop_on_first=False
        )
        gate_names = [g for g, _ in violations]
        self.assertIn("postmortem-to-guard-gate", gate_names, "未履行复盘的回复必须被 evaluate_all_structural_gates 命中！")


if __name__ == "__main__":
    unittest.main()
