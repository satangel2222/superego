# -*- coding: utf-8 -*-
"""read_after_write.py —— 读后写物理核销门禁 (Read-After-Write Proof-of-Work Guard).

核心使命 (物理化 R3/R20/R22):
  彻底消灭「口头搞定、虚假交付 (False-Done Bluff)」：
  当 Agent 在回复中宣称“已成功修改/已全部替换/功能已完成”，
  Stop 门禁自动对账物理落盘事实与 `git status --porcelain` + `git diff HEAD`；
  严禁未动代码却谎称完成，或改了一半却谎称全部搞定。
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

_CLAIM_DONE_RE = re.compile(
    r"(?:已(?:成功)?(?:修复|完成|解决|修改|改好了|更新|重构|替换)|"
    r"全部(?:搞定|处理完|生效|就绪)|"
    r"功能已实现|测试已全部通过)",
    re.I
)

_QUOTING_HISTORIC = re.compile(r"(?:^#\s*教训|教训案例库|【形状 20\d\d|历史案卷|历史教训|复盘)")


def get_git_status_and_diff(cwd: Optional[Path] = None) -> Tuple[List[str], str]:
    """获取当前工作区的 git status --porcelain 与 git diff HEAD"""
    base = cwd or Path.cwd()
    modified_files = []
    diff_text = ""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=2.0
        )
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    modified_files.append(parts[-1])
    except Exception:
        pass

    try:
        res_diff = subprocess.run(
            ["git", "diff", "HEAD", "--stat"],
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=2.0
        )
        if res_diff.returncode == 0:
            diff_text = res_diff.stdout.strip()
    except Exception:
        pass

    return modified_files, diff_text


def audit_proof_of_work(
    assistant_text: str,
    tool_history: Optional[List[Dict[str, Any]]] = None,
    cwd: Optional[Path] = None
) -> Tuple[bool, Optional[str]]:
    """在交付时核对物理证据闭环"""
    if not assistant_text:
        return True, None

    if _QUOTING_HISTORIC.search(assistant_text):
        return True, None

    # 1. 检查是否宣称了“任务完成/已成功修改”
    m = _CLAIM_DONE_RE.search(assistant_text)
    if not m:
        return True, None

    claim_phrase = m.group(0)

    # 2. 铁律：宣称已修复/已完成，但本轮零次工具调用（动嘴不动手），一律视为虚假交付打回！
    if not tool_history or len(tool_history) == 0:
        return False, (
            f"⛔ [PROOF_OF_WORK_FAILED] 虚假完成交付打回 (物理化 R3/R20 铁律)！\n"
            f"检测到在回复中宣称了「{claim_phrase}」，但在当前轮次工具流水中【零次调用工具】（未执行任何读写、测试或排查）！\n"
            f"严禁纯口头虚假交付！若确实已完成，必须出具客观测试日志或物理改动证据！"
        )

    # 3. 检查本轮是否存在物理写入工具或测试命令
    has_write_tool = False
    has_test_cmd = False
    written_targets = set()

    for t in tool_history:
        tname = (t.get("name") or t.get("tool_name") or "").lower()
        if any(w in tname for w in ("write", "edit", "replace_file_content", "patch")):
            has_write_tool = True
            args = t.get("args") or t.get("input") or {}
            path = args.get("TargetFile") or args.get("path") or args.get("file_path")
            if path:
                written_targets.add(Path(str(path)).name)
        elif any(c in tname for c in ("bash", "powershell", "run_command", "terminal")):
            args_str = str(t.get("args") or t.get("input") or "").lower()
            if any(k in args_str for k in ("test", "pytest", "npm run", "git status", "git diff")):
                has_test_cmd = True

    # 4. 检查 Git 物理工作树是否有改动
    modified_files, diff_stat = get_git_status_and_diff(cwd)

    # 如果有写入工具调用，或执行了测试并有工作区改动，放行
    if has_write_tool or (has_test_cmd and modified_files):
        return True, None

    # 5. 若既无写入工具，也无测试对账记录，判定为假完成
    return False, (
        f"⛔ [PROOF_OF_WORK_FAILED] 虚假完成交付打回 (物理化 R3/R20 铁律)！\n"
        f"检测到在回复中宣称了「{claim_phrase}」，但本轮工具流水中未见有效代码写入记录，"
        f"且未见回归测试执行！\n"
        f"铁律规定：严禁口头虚假交付！必须出具客观测试退出码或代码修改物理证据！"
    )
