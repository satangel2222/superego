# -*- coding: utf-8 -*-
"""test_v3_six_pillars.py —— Superego 3.0 六重物理硬防御与读后写自证全景单测套件.

全面覆盖:
  1. AST 语法树穿透 (文件 + 内联 python -c 破坏性 API 拦截)
  2. No-Diagnosis-No-Edit 拓扑诊断门禁 (R14/R15/R18/R36 物理化)
  3. Action Contract 两阶段清单状态机 (R7/R28/R41 物理化)
  4. Diff Quality 代码防劣化与防假实现门禁
  5. Env Safety 环境与依赖防踩踏门禁
  6. Burst Limiter 局内工具调用风暴限频
  7. Read-After-Write 读后写物理核销 (R3/R20)
  8. Honest Scope 诚实履职对账 (R16/ENG-01)
"""
import os
import sys
import json
import time
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
if str(REPO_ROOT / "superego") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "superego"))

from tool_normalizer import normalize_tool_call
from ast_inspector import audit_command_ast, audit_python_code
from no_diagnosis_guard import check_no_diagnosis_edit, grant_diagnosis_ticket, is_exempt_file
from action_contract import check_action_contract, is_manifest_valid_and_fresh
from diff_quality_guard import check_diff_dilution
from env_safety_guard import check_env_safety
from burst_limiter import check_pre_tool_burst, record_strike, record_success, reset_conv_state
from read_after_write import audit_proof_of_work
from honest_scope_gate import check_honest_scope
from security_core import audit_tool_call


def test_1_ast_inspector():
    print("👉 [Test 1] 验证 AST 语法树穿透引擎...")
    # 1.1 内联 python -c 破坏性 API
    cmd_inline = "python -c \"import shutil; shutil.rmtree('/tmp/test')\""
    ok, err = audit_command_ast(cmd_inline)
    assert not ok and "AST_DESTRUCTIVE_API_BLOCKED" in (err or "")
    
    # 1.2 内联 Telegram delete_messages 调用
    cmd_tg = "py -c \"client.delete_messages(chat_id, [1, 2, 3])\""
    ok_tg, err_tg = audit_command_ast(cmd_tg)
    assert not ok_tg and "delete_messages" in (err_tg or "")

    # 1.3 携带 --dry-run 放行
    cmd_dry = "python -c \"import shutil; shutil.rmtree('/tmp/test')\" --dry-run"
    ok_dry, _ = audit_command_ast(cmd_dry)
    assert ok_dry, "dry-run 模式应予放行"

    # 1.4 安全普通命令放行
    cmd_safe = "python -c \"print('hello world')\""
    ok_safe, _ = audit_command_ast(cmd_safe)
    assert ok_safe
    print("   [✓] AST 穿透引擎测试全部通过")


def test_2_no_diagnosis_guard():
    print("👉 [Test 2] 验证 No-Diagnosis-No-Edit 拓扑诊断门禁...")
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        # 2.1 豁免文件 (测试、文档、草稿)
        assert is_exempt_file("tests/test_demo.py")
        assert is_exempt_file("README.md")
        assert is_exempt_file("scratch/quick_test.py")

        # 2.2 核心业务代码未诊断拦截
        core_file = str(td / "user_service.py")
        ok, err = check_no_diagnosis_edit(core_file, is_new_file=False, transcript_messages=[])
        assert not ok and "NO_DIAGNOSIS_NO_EDIT" in (err or "")

        # 2.3 携带诊断历史记录放行
        mock_msgs = [{"message": "我使用了 codegraph_explore 检索了 user_service 的调用图谱"}]
        ok_diag, _ = check_no_diagnosis_edit(core_file, is_new_file=False, transcript_messages=mock_msgs)
        assert ok_diag, "有图谱诊断记录应放行"

        # 2.4 新建文件放行
        ok_new, _ = check_no_diagnosis_edit(core_file, is_new_file=True)
        assert ok_new, "新建文件应予放行"
    print("   [✓] 拓扑诊断门禁测试全部通过")


def test_3_action_contract():
    print("👉 [Test 3] 验证两阶段清单状态机 (Action Contract)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        # 3.1 存在合法未过期清单放行
        manifest_file = td / ".manifest.json"
        manifest_data = {
            "targets": ["msg_101", "msg_102"],
            "operation": "delete",
            "timestamp": time.time()
        }
        manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
        
        ok_m, _ = is_manifest_valid_and_fresh(manifest_file)
        assert ok_m, "合法清单应通过验证"

        # 3.2 携带清单的执行命令放行
        cmd_exec = f"python clean_tg.py --manifest {manifest_file}"
        ok_c, _ = check_action_contract(cmd_exec, cwd=td)
        assert ok_c, "携带有效清单的执行应放行"

        # 3.3 空 targets 清单拦截
        empty_manifest = td / "empty.json"
        empty_manifest.write_text(json.dumps({"targets": []}), encoding="utf-8")
        ok_empty, err_empty = is_manifest_valid_and_fresh(empty_manifest)
        assert not ok_empty and "为空" in (err_empty or "")
    print("   [✓] 动作契约状态机测试全部通过")


def test_4_diff_quality_guard():
    print("👉 [Test 4] 验证代码防劣化与防偷工减料审查...")
    # 4.1 构造 50 行真实逻辑代码
    old_code = "\n".join([f"    def step_{i}(self): return do_work({i})" for i in range(50)])
    # 4.2 偷工减料版 (直接退化为 pass)
    new_lazy_code = "    pass\n"
    
    ok, err = check_diff_dilution("services/core.py", old_code, new_lazy_code)
    assert not ok and "DIFF_DILUTION_BLOCKED" in (err or "")

    # 4.3 正常重构 (代码量正常)
    new_good_code = "\n".join([f"    def optimized_step_{i}(self): return execute({i})" for i in range(45)])
    ok_good, _ = check_diff_dilution("services/core.py", old_code, new_good_code)
    assert ok_good, "正常完备重构应放行"
    print("   [✓] 代码防劣化门禁测试全部通过")


def test_5_env_safety_guard():
    print("👉 [Test 5] 验证环境与依赖防踩踏门禁...")
    # 5.1 拦截私自删除 package-lock.json
    ok_rm, err_rm = check_env_safety("rm -f package-lock.json")
    assert not ok_rm and "LOCKFILE_DESTRUCTION_BLOCKED" in (err_rm or "")

    # 5.2 拦截全局 pip --break-system-packages
    ok_pip, err_pip = check_env_safety("pip install requests --break-system-packages")
    assert not ok_pip and "GLOBAL_ENV_POLLUTION_BLOCKED" in (err_pip or "")

    # 5.3 放行普通 npm run build
    ok_safe, _ = check_env_safety("npm run build")
    assert ok_safe
    print("   [✓] 环境防踩踏门禁测试全部通过")


def test_6_burst_limiter():
    print("👉 [Test 6] 验证局内工具调用风暴限频...")
    cid = "test_burst_session"
    reset_conv_state(cid)

    # 连续记录 3 次 strike
    record_strike(cid, "TEST_GATE")
    record_strike(cid, "TEST_GATE")
    record_strike(cid, "TEST_GATE")

    ok, err = check_pre_tool_burst(cid)
    assert not ok and "BURST_LIMIT_TRIPPED" in (err or "")

    # 重置后恢复
    reset_conv_state(cid)
    ok_clean, _ = check_pre_tool_burst(cid)
    assert ok_clean
    print("   [✓] 局内风暴限频测试全部通过")


def test_7_read_after_write():
    print("👉 [Test 7] 验证读后写物理核销门禁 (R3)...")
    # 7.1 零工具调用却宣称搞定 -> 拦截
    claim_text = "我已经全部修改搞定，接口功能已修复！"
    ok, err = audit_proof_of_work(claim_text, tool_history=[])
    assert not ok and "PROOF_OF_WORK_FAILED" in (err or "")

    # 7.2 有真实写入工具调用 -> 放行
    mock_history = [{"name": "replace_file_content", "args": {"TargetFile": "app.py"}}]
    ok_written, _ = audit_proof_of_work(claim_text, tool_history=mock_history)
    assert ok_written, "有实际写入工具记录应放行"
    print("   [✓] 读后写物理核销门禁测试全部通过")


def test_8_honest_scope_gate():
    print("👉 [Test 8] 验证诚实履职对账门禁 (R16)...")
    # 8.1 零次查阅却宣称逐页调阅 -> 拦截
    fake_claim = "我已经遵照您的要求，把所有文档逐页调阅并分析完毕。"
    ok, err = check_honest_scope(fake_claim, tool_history=[])
    assert not ok and "HONEST_SCOPE_VIOLATION" in (err or "")

    # 8.2 带有诚实定量免责说明 -> 放行
    honest_claim = "根据查阅，实际精读了 5 篇核心文档，尚有 40 篇未读，分析如下："
    ok_honest, _ = check_honest_scope(honest_claim, tool_history=[])
    assert ok_honest, "带定量说明的诚实交付应放行"
    print("   [✓] 诚实履职对账门禁测试全部通过")


def main():
    print("=" * 65)
    print("🛡️ SUPEREGO 3.0 六重物理硬防御与物理证据验真 全景自动化回归测试")
    print("=" * 65)
    test_1_ast_inspector()
    test_2_no_diagnosis_guard()
    test_3_action_contract()
    test_4_diff_quality_guard()
    test_5_env_safety_guard()
    test_6_burst_limiter()
    test_7_read_after_write()
    test_8_honest_scope_gate()
    print("=" * 65)
    print("🎉 8 大核心物理门禁单元测试 100% 全部通过 (Zero Failure)！")
    print("=" * 65)


if __name__ == "__main__":
    main()
