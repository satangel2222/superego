# -*- coding: utf-8 -*-
"""no_diagnosis_guard.py —— 拓扑诊断前置门禁 (No-Diagnosis-No-Edit Guard).

核心使命 (物理化 R14/R15/R18/R36):
  严禁 AI 在未调阅调用图谱、未查上下游拓扑的情况下，对核心业务代码进行「冰山一角盲改与局部 patch」！
  在 PreToolUse 阶段拦截针对核心源码的 write_to_file / replace_file_content / Edit / Write。

自适应与防死锁设计:
  1. 新建文件、单测文件、文档、草稿脚本自动豁免，绝不干扰正常研发；
  2. 若仓库未建 .codegraph/ 索引，自适应平滑降级为检查 grep_search / view_file；
  3. 一旦诊断过某模块，下发会话级「诊断票据 (Diagnosis Ticket)」，后续关联改动无需反复重查。
"""
import os
import re
import json
import time
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

# 豁免文件后缀与目录 (仅限明确的草稿或配置)
_EXEMPT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".svg", ".png", ".jpg"}
_EXEMPT_DIRS = {"scratch", ".idea", ".vscode"}

# 核心代码后缀
_CODE_EXTENSIONS = {".py", ".ts", ".js", ".mjs", ".cjs", ".go", ".rs", ".java", ".c", ".cpp", ".cs", ".php"}

# 内存/临时诊断票据存储目录
TICKETS_DIR = Path.home() / ".superego" / "tickets"


def is_exempt_file(file_path_str: str) -> bool:
    """判断文件是否属于自动豁免范畴"""
    if not file_path_str:
        return True
    path = Path(file_path_str)

    # 1. 检查文件后缀
    if path.suffix.lower() in _EXEMPT_EXTENSIONS:
        return True

    # 2. 检查目录黑名单 (测试、临时脚本、草稿)
    parts = set(p.lower() for p in path.parts)
    if parts & _EXEMPT_DIRS:
        return True

    # 3. 检查单测文件 (test_*.py, *.test.ts 等)
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py") or ".test." in name or ".spec." in name:
        return True

    return False


def has_diagnosis_ticket(file_path_str: str, max_age_seconds: int = 1800) -> bool:
    """检查当前文件是否在 30 分钟内已获得诊断授权票据"""
    try:
        if not TICKETS_DIR.exists():
            return False
        import hashlib
        fp_hash = hashlib.md5(file_path_str.encode("utf-8")).hexdigest()[:12]
        ticket_file = TICKETS_DIR / f"{fp_hash}.ticket"
        if ticket_file.exists():
            mtime = ticket_file.stat().st_mtime
            if time.time() - mtime < max_age_seconds:
                return True
    except Exception:
        pass
    return False


def grant_diagnosis_ticket(file_path_str: str):
    """向目标文件发放诊断授权票据"""
    try:
        TICKETS_DIR.mkdir(parents=True, exist_ok=True)
        import hashlib
        fp_hash = hashlib.md5(file_path_str.encode("utf-8")).hexdigest()[:12]
        ticket_file = TICKETS_DIR / f"{fp_hash}.ticket"
        ticket_file.write_text(f"{time.time()}|{file_path_str}", encoding="utf-8")
    except Exception:
        pass


def check_no_diagnosis_edit(
    file_path_str: str,
    is_new_file: bool = False,
    transcript_messages: Optional[List[Dict[str, Any]]] = None,
    cwd: Optional[Path] = None
) -> Tuple[bool, Optional[str]]:
    """核心门禁校验：修改已有核心业务源码前，必须有图谱/调用链诊断证据"""
    # 1. 新建文件无条件放行（尚未生成拓扑）
    if is_new_file:
        grant_diagnosis_ticket(file_path_str)
        return True, None

    # 2. 豁免类型放行
    if is_exempt_file(file_path_str):
        return True, None

    # 3. 若已拥有有效会话诊断票据，直接放行
    if has_diagnosis_ticket(file_path_str):
        return True, None

    # 4. 判断当前仓库是否存在 .codegraph 索引
    base_dir = cwd or Path.cwd()
    has_codegraph = (base_dir / ".codegraph").exists() or (Path(file_path_str).parent / ".codegraph").exists()

    # 5. 审查历史交互流中是否有图谱或调用链检索动作
    has_diagnosis = False
    searched_terms = set()

    if transcript_messages:
        for m in transcript_messages:
            content = str(m.get("message") or m.get("content") or "")
            # 检查是否调用过 codegraph_explore
            if "codegraph_explore" in content or "codegraph" in content.lower():
                has_diagnosis = True
                break
            # 检查是否执行了 grep 或代码查看
            if any(tool_kw in content for tool_kw in ("grep_search", "find_by_name", "view_file", "rg ", "grep ")):
                target_base = Path(file_path_str).name
                stem = Path(file_path_str).stem
                if target_base in content or stem in content:
                    has_diagnosis = True
                    break

    # 6. 若通过诊断，下发票据并放行
    if has_diagnosis:
        grant_diagnosis_ticket(file_path_str)
        return True, None

    # 7. 亮红牌并出具自适应梯子导航
    if has_codegraph:
        return False, (
            f"⛔ [NO_DIAGNOSIS_NO_EDIT] 核心代码盲改硬拦截 (物理化 R14/R15/R36 铁律)！\n"
            f"你正试图直接修改核心源码 `{Path(file_path_str).name}`，但在本轮会话中未曾发现该模块的调用图谱分析记录。\n"
            f"铁律规定：严禁不探拓扑直接打局部补丁！\n"
            f"⇒ 【梯子导航】：当前项目已建立 CodeGraph 索引，请立即调用 `codegraph_explore` 检索该文件/符号的调用拓扑与上下游数据流，"
            f"摸清根因后再行动！"
        )
    else:
        # 平滑降级提示
        return False, (
            f"⛔ [NO_DIAGNOSIS_NO_EDIT] 核心代码盲改硬拦截 (物理化 R14/R15/R36 铁律)！\n"
            f"你正试图直接修改核心源码 `{Path(file_path_str).name}`，但未见对该文件或相关函数的检索/阅读记录。\n"
            f"铁律规定：严禁未查阅源码上下文即盲目打补丁！\n"
            f"⇒ 【梯子导航】：请先使用 `grep_search` 溯源该函数的被调用位置，或使用 `view_file` 查阅完整实现后再提交修改！"
        )
