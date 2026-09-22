# -*- coding: utf-8 -*-
"""diff_quality_guard.py —— 代码防劣化与防偷工减料审查门禁 (Diff Quality Guard).

核心使命:
  防止 Agent 在面对复杂技术逻辑时发生「偷工减料/假实现 (Mocking / Slacking)」：
  当旧代码有较为完备的业务逻辑（>40 行），新代码却大段删减并退化为 `pass`、`TODO`、
  `return True` 等伪装占位符时，实施物理硬阻断！
"""
import re
from pathlib import Path
from typing import Tuple, Optional

# 假实现/占位符特征
_MOCK_PLACEHOLDER_RE = re.compile(
    r"^\s*(?:pass|#\s*TODO.*|//\s*TODO.*|raise\s+NotImplementedError.*|return\s+(?:True|False|None|{}|\[\]))\s*$",
    re.M
)

_EXEMPT_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".svg"}


def _count_effective_lines(text: str) -> int:
    """统计代码的有效非空非注释行数"""
    if not text:
        return 0
    lines = 0
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("//"):
            lines += 1
    return lines


def check_diff_dilution(
    file_path: str,
    old_content: str,
    new_content: str
) -> Tuple[bool, Optional[str]]:
    """审查单次代码替换是否存在严重的业务逻辑被删减变假实现"""
    if not file_path or not old_content or not new_content:
        return True, None

    # 豁免文档与配置文件
    if Path(file_path).suffix.lower() in _EXEMPT_EXTS:
        return True, None

    old_eff = _count_effective_lines(old_content)
    # 仅针对原有规模较大 (>40 行有效逻辑) 的代码段进行劣化审查
    if old_eff < 40:
        return True, None

    new_eff = _count_effective_lines(new_content)

    # 检查新代码是否删减了超过 70% 的行数
    if new_eff < old_eff * 0.3:
        # 进一步检查新代码中是否充斥占位符或极简假实现
        has_placeholder = bool(_MOCK_PLACEHOLDER_RE.search(new_content))
        if has_placeholder or new_eff <= 3:
            return False, (
                f"⛔ [DIFF_DILUTION_BLOCKED] 检测到严重代码劣化与偷工减料行为！\n"
                f"在文件 `{Path(file_path).name}` 中，原代码包含 {old_eff} 行完备业务逻辑，"
                f"但替换内容仅保留 {new_eff} 行，且疑似退化为 `pass / TODO / 假常量返回`！\n"
                f"铁律规定：严禁擅自阉割系统异常捕获与核心逻辑。如需重构，必须给出等效完整的真实代码实现！"
            )

    return True, None
