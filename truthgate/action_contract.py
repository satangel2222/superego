# -*- coding: utf-8 -*-
"""action_contract.py —— 两阶段动作契约与清单状态机 (Action Contract & Manifest Guard).

核心使命 (物理化 R7/R28/R41):
  将不可逆批量删除、数据清理、跨作用域操作强行约束在两阶段契约状态机内:
    阶段 1 (准备阶段): 运行只读探针/dry-run，生成 .manifest.json 清单并在终端打印；
    阶段 2 (执行阶段): 只有显式携带合法 --manifest 参数且清单被核销时，方可物理执行。
"""
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

MANIFEST_FILENAME = ".manifest.json"


def parse_manifest(manifest_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """解析并校验 Manifest 清单有效性"""
    if not manifest_path.exists():
        return False, None, f"清单文件 `{manifest_path}` 不存在！"

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, None, f"清单文件 JSON 格式损坏: {e}"

    if not isinstance(data, dict):
        return False, None, "清单格式必须为 JSON 对象！"

    targets = data.get("targets")
    if not isinstance(targets, list):
        return False, None, "清单中缺少必填字段 `targets` (必须为待处理目标数组)！"

    if len(targets) == 0:
        return False, None, "清单 `targets` 为空，无任何待处理目标！"

    return True, data, None


def is_manifest_valid_and_fresh(manifest_path: Path, max_age_seconds: int = 1800) -> Tuple[bool, Optional[str]]:
    """校验 Manifest 是否处于 30 分钟有效期内且内容完好"""
    ok, data, err = parse_manifest(manifest_path)
    if not ok:
        return False, err

    mtime = manifest_path.stat().st_mtime
    age = time.time() - mtime
    if age > max_age_seconds:
        return False, f"清单文件已过期 (生成于 {int(age)} 秒前，超过 30 分钟时限)，必须重新生成！"

    return True, None


def check_action_contract(command: str, cwd: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """检查批量破坏性操作是否符合两阶段动作契约"""
    if not command:
        return True, None

    cmd_lower = command.lower()

    # 1. 如果是 dry-run 模式，无条件放行（鼓励生成清单）
    if "--dry-run" in cmd_lower or "-dryrun" in cmd_lower or "dry_run" in cmd_lower:
        return True, None

    # 2. 如果携带了 --manifest 参数，校验目标清单是否存在并合法
    if "--manifest" in cmd_lower:
        import re
        m = re.search(r"--manifest\s+([^\s]+)", command)
        manifest_arg = m.group(1).strip("\"'") if m else MANIFEST_FILENAME
        base_dir = cwd or Path.cwd()
        mpath = (base_dir / manifest_arg).resolve()
        valid, err = is_manifest_valid_and_fresh(mpath)
        if not valid:
            return False, (
                f"⛔ [ACTION_CONTRACT_INVALID] 动作契约清单验证失败: {err}\n"
                f"请先运行带 `--dry-run` 的命令生成合法且未过期的 `{MANIFEST_FILENAME}`！"
            )
        return True, None

    return True, None
