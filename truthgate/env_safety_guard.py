# -*- coding: utf-8 -*-
"""env_safety_guard.py —— 环境与依赖防踩踏安全门禁 (Environment & Dependency Guard).

核心使命:
  1. 阻止在非虚拟环境下对全局 Python 解释器进行污染破坏性安装 (pip install --break-system-packages)；
  2. 阻止强制全局覆盖 Node.js 模块 (npm install -g --force)；
  3. 阻止私自删除/破坏项目锁定文件 (package-lock.json / poetry.lock / pnpm-lock.yaml)。
"""
import os
import re
from pathlib import Path
from typing import Tuple, Optional

# 锁定文件模式
_LOCKFILE_DELETE_RE = re.compile(
    r"\b(?:rm|del|remove-item|unlink)\b.*?\b(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock)\b",
    re.I
)

# 全局 pip 暴力安装模式
_GLOBAL_PIP_DANGEROUS = re.compile(
    r"\bpip(?:3)?\s+install\b.*?(?:--break-system-packages|--target\s+/[a-zA-Z]*)",
    re.I
)

# 暴力 npm 全局安装
_NPM_FORCE_GLOBAL = re.compile(
    r"\bnpm\s+(?:i|install)\b.*?(?:-g|--global)\b.*?(?:-f|--force)\b",
    re.I
)


def is_in_virtual_env() -> bool:
    """探测当前是否处于活跃的 Python 虚拟环境 (venv / conda)"""
    return bool(os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_PREFIX"))


def check_env_safety(command: str) -> Tuple[bool, Optional[str]]:
    """检查终端命令是否会造成环境踩踏或锁定文件损毁"""
    if not command:
        return True, None

    # 1. 检查私自删除锁定文件
    m_lock = _LOCKFILE_DELETE_RE.search(command)
    if m_lock:
        lock_name = m_lock.group(1)
        return False, (
            f"⛔ [LOCKFILE_DESTRUCTION_BLOCKED] 严禁直接删除依赖锁定文件 `{lock_name}`！\n"
            f"铁律规定：依赖锁定文件是保障生产构建一致性的核心基石，严禁为图省事随手删除重新生成。\n"
            f"请先排查依赖版本冲突的具体包名并对症解决！"
        )

    # 2. 检查全局危险 pip
    if _GLOBAL_PIP_DANGEROUS.search(command):
        return False, (
            "⛔ [GLOBAL_ENV_POLLUTION_BLOCKED] 检测到针对系统全局 Python 环境的强行破坏性安装 (--break-system-packages)！\n"
            "严禁污染宿主系统底层 Python 环境，必须在虚拟环境 (.venv) 中安全安装！"
        )

    # 3. 检查 npm -g --force
    if _NPM_FORCE_GLOBAL.search(command):
        return False, (
            "⛔ [NPM_GLOBAL_FORCE_BLOCKED] 严禁使用 npm -g --force 强制覆盖全局模块！"
        )

    return True, None
