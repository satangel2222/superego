# -*- coding: utf-8 -*-
"""visual_proof_gate.py —— 桌面视窗真实性与视觉自证门禁 (Visual Proof & Desktop Reality Gate).

核心使命:
  彻底解决「桌面幽灵弹窗欺诈 (desktop-window-phantom)」与「无头爬虫假截图 (headless-mock-fraud)」：
  当 Agent 宣称“已在系统默认浏览器中打开页面 / 视窗已在桌面弹出”，
  Stop 门禁强行枚举物理主桌面 (WinSta0\\default) 可见视窗句柄；
  若物理桌面未检测到浏览器或目标端口视窗，物理硬拦截并给出前台拉起梯子！
"""
import os
import re
import sys
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

DESKTOP_POPUP_CLAIM = re.compile(
    r"(?:已(?:在[^\n，。！？]{0,15}?(?:浏览器|桌面|前台|视窗|系统)[^\n，。！？]{0,15}?(?:中|里)?)?(?:为您|为你|帮您|帮你)?(?:弹出|弹出了|打开了|打开|直接打开|拉起|唤起|启动了|显示在)|"
    r"在你的桌面上直接弹出|弹出了浏览器|为你打开了|帮您打开了|切换到刚弹出来的|已调用系统默认浏览器|已在[^\n，。！？]{0,10}?浏览器中[^\n，。！？]{0,6}?(?:打开|弹出)|"
    r"在浏览器中(?:为你|为您)?打开).*?(?:浏览器|控制台|窗口|视窗|页面|localhost|http|https)?",
    re.I
)

_QUOTING_HISTORIC = re.compile(r"(?:^#\s*教训|教训案例库|【形状 20\d\d|历史案卷|历史教训|复盘)")

# 常见浏览器窗口关键词
BROWSER_WINDOW_KEYWORDS = ("chrome", "edge", "msedge", "firefox", "brave", "safari", "opera", "browser")


def get_default_desktop_windows() -> List[str]:
    """枚举物理主桌面 (WinSta0\\default) 上所有真实可见视窗的标题列表"""
    if os.name != "nt":
        return []
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if not hdesk:
            return []
        titles = []

        def callback(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    titles.append(buff.value)
            return True

        EnumDesktopWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumDesktopWindows(hdesk, EnumDesktopWindowsProc(callback), 0)
        user32.CloseDesktop(hdesk)
        return titles
    except Exception:
        return []


def check_desktop_popup_reality(
    text: str,
    tool_history: Optional[List[Dict[str, Any]]] = None,
    mock_desktop_windows: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """核验桌面弹窗真实性：声称在桌面弹出浏览器时，物理桌面必须存在真实视窗"""
    if not text or _QUOTING_HISTORIC.search(text):
        return True, None

    m_desk = DESKTOP_POPUP_CLAIM.search(text)
    if not m_desk:
        return True, None

    claim_snippet = m_desk.group(0)

    # 获取物理桌面可见窗口列表（支持测试时注入 mock）
    desk_wins = mock_desktop_windows if mock_desktop_windows is not None else get_default_desktop_windows()

    has_matched_window = False
    ports = re.findall(r':(\d{4,5})\b', text)

    # 1. 检查窗口标题中是否包含具体端口或 URL 标识
    if ports:
        for p in ports:
            if any(p in w.lower() for w in desk_wins):
                has_matched_window = True
                break

    # 2. 检查是否有任何活跃的可见浏览器视窗
    if not has_matched_window:
        for b in BROWSER_WINDOW_KEYWORDS:
            if any(b in w.lower() for w in desk_wins):
                has_matched_window = True
                break

    # 3. 检查本轮工具流中是否真有全屏真机截屏凭证 (real_screen / desktop_shot)
    has_real_screenshot = False
    if tool_history:
        for t in tool_history:
            args_str = str(t.get("args") or t.get("input") or "").lower()
            if any(kw in args_str for kw in ("real_screen", "desktop_shot", "fullscreen", "screen_bounds")):
                has_real_screenshot = True
                break

    if has_matched_window or has_real_screenshot:
        return True, None

    # 未检测到真实可见视窗，亮红牌并出具前台唤起梯子导航
    port_hint = ports[0] if ports else "3000"
    win_samples = [w[:25] for w in desk_wins[:5]] if desk_wins else ["(当前桌面无可见应用窗口)"]

    return False, (
        f"⛔ [DESKTOP_WINDOW_PHANTOM] 桌面幽灵弹窗与假打开硬拦截！\n"
        f"检测到在回复中宣称了「{claim_snippet}」（已在浏览器打开/已在桌面弹出），\n"
        f"但当前物理主桌面 (WinSta0\\default) 真实窗口枚举中【查无对应可见浏览器视窗】！\n"
        f"  • 当前桌面可见视窗样例: {win_samples}\n"
        f"铁律规定：严禁将后台无头沙盒执行脑补为前台真机弹窗！\n"
        f"─" * 60 + "\n"
        f"🧗 【梯子导航 (Next Action)】:\n"
        f"  1. 物理桌面未见浏览器视窗，请勿空口宣称已弹出！\n"
        f"  2. 请立即在终端执行 Windows 原生前台唤起命令:\n"
        f"     cmd.exe /c start http://localhost:{port_hint}\n"
        f"     或调用 Python 原语: import webbrowser; webbrowser.open('http://localhost:{port_hint}')\n"
        f"  3. 确认用户物理桌面上弹出真实浏览器窗口后，方可完成交付！\n"
        f"─" * 60
    )
