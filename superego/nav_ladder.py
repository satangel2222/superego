# -*- coding: utf-8 -*-
"""nav_ladder.py —— 自愈导航梯子生成器 (Actionable Navigation Ladder).

核心使命:
  彻底根除 AI 撞墙后的「习得性无助与装死摆烂」：
  任何一道门禁在抛出拦截时，绝不允许只扔一句冷冰冰的“权限拒绝 (Denied)”，
  必须附带明确、结构化、唯一的「下一步正向行动配方（梯子导航）」。
"""
from typing import List, Optional


def format_ladder_response(
    gate_id: str,
    violation_reason: str,
    next_steps: List[str],
    rule_name: str = ""
) -> str:
    """构建标准带梯子红牌报文"""
    title = f"⛔ [{gate_id}]"
    if rule_name:
        title += f" {rule_name}"

    lines = [
        f"{title} 拦截生效：",
        f"  {violation_reason.strip()}",
        "─" * 60,
        "🧗 【梯子导航 · 唯一合规前进路径 (Next Action)】:"
    ]

    for i, step in enumerate(next_steps, 1):
        lines.append(f"  {i}. {step}")

    lines.append("─" * 60)
    lines.append("请遵照上述梯子导航继续推进，严禁放弃或停滞！")
    return "\n".join(lines)
