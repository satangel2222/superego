# -*- coding: utf-8 -*-
"""burst_limiter.py —— 单轮工具风暴限频与 2-Strike 死锁熔断器 (Burst Limiter & Deadlock Fuse).

核心使命:
  1. 局内风暴限频 (Intra-turn Burst Protection):
     防范 Agent 在单回合内疯狂连续尝试失败的工具调用，在几秒内打满上下文、焚烧巨量 Token；
     单轮连续 3 次工具失败/拦截，硬性熔断当前工具链执行。
  2. 跨轮 2-Strike 死锁熔断 (Cross-turn 2-Strike Fuse):
     同一门禁连续命中 2 次时，主动介入接管，向用户交出控制权并打印退出建议，杜绝装死循环。
"""
import time
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

STATE_DIR = Path.home() / ".superego" / "state"


def _get_state_file(conv_id: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    cid = (conv_id or "global")[:16]
    return STATE_DIR / f"burst_{cid}.json"


def load_turn_state(conv_id: str) -> Dict[str, Any]:
    f = _get_state_file(conv_id)
    if not f.exists():
        return {"consecutive_failures": 0, "gate_strikes": {}, "last_updated": time.time()}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        # 若记录超过 1 小时，自动重置
        if time.time() - data.get("last_updated", 0) > 3600:
            return {"consecutive_failures": 0, "gate_strikes": {}, "last_updated": time.time()}
        return data
    except Exception:
        return {"consecutive_failures": 0, "gate_strikes": {}, "last_updated": time.time()}


def save_turn_state(conv_id: str, state: Dict[str, Any]):
    f = _get_state_file(conv_id)
    try:
        state["last_updated"] = time.time()
        f.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def record_strike(conv_id: str, gate_id: str) -> int:
    """记录某道门禁被触发的次数，返回当前累计 strike 计数"""
    st = load_turn_state(conv_id)
    st["consecutive_failures"] = st.get("consecutive_failures", 0) + 1
    strikes = st.setdefault("gate_strikes", {})
    count = strikes.get(gate_id, 0) + 1
    strikes[gate_id] = count
    save_turn_state(conv_id, st)
    return count


def record_success(conv_id: str):
    """工具成功执行后重置连续失败计数器"""
    st = load_turn_state(conv_id)
    st["consecutive_failures"] = 0
    save_turn_state(conv_id, st)


def check_pre_tool_burst(conv_id: str) -> Tuple[bool, Optional[str]]:
    """在 PreToolUse 执行前检查当前回合是否已触发连续失控风暴"""
    st = load_turn_state(conv_id)
    consec = st.get("consecutive_failures", 0)
    if consec >= 3:
        return False, (
            "⛔ [BURST_LIMIT_TRIPPED] 局内工具调用风暴硬熔断！\n"
            f"检测到当前单轮回合内已连续发生 {consec} 次工具拦截或执行失败！\n"
            "为防止模型陷入盲目试错死循环并无谓焚烧上下文 Token，系统已主动切断工具链。\n"
            "⇒ 请停止尝试，梳理当前遇到的真实阻碍，如实向用户说明现状并寻求人类确认！"
        )
    return True, None


def reset_conv_state(conv_id: str):
    """新回合开始时重置状态"""
    f = _get_state_file(conv_id)
    try:
        if f.exists():
            f.unlink()
    except Exception:
        pass
