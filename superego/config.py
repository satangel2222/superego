# -*- coding: utf-8 -*-
"""config.py —— Superego 2.0 统一动态配置与用户画像引擎 (Profile Engine)。
彻底解耦写死的盘符与用户名，实现跨平台（Windows / macOS / Linux）自适应。
"""
import os
import sys
import json
import platform
from pathlib import Path

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

HOME = Path.home()
SUPEREGO_HOME = HOME / ".superego"
CONFIG_FILE = SUPEREGO_HOME / "config.json"

PROFILES = {
    "vibe-boss": {
        "id": "vibe-boss",
        "name": "👑 老板 / Vibe Coder 模式 (Frank 旗舰版)",
        "description": "严禁飙技术术语（必须人话括号解释）；严禁向用户请示（全自动推进干完）；死磕免费优先。",
        "persona_title": "零编程的业务主管/指挥者",
        "rules_override": {
            "R9_strict_jargon_ban": True,
            "R9_require_renhua_brackets": True,
            "R5_strict_no_asking": True,
            "R5_auto_proceed_authorized": True,
            "R8_free_open_source_first": True,
        },
        "allowed_jargon": False,
        "destructive_confirm_only_real_harm": True,
    },
    "engineer": {
        "id": "engineer",
        "name": "💻 资深工程师模式 (Engineer Mode)",
        "description": "放行代码变量与架构术语；强化单元测试与覆盖率；严谨排查根因。",
        "persona_title": "资深软件架构师/开发工程师",
        "rules_override": {
            "R9_strict_jargon_ban": False,
            "R9_require_renhua_brackets": False,
            "R5_strict_no_asking": False,
            "R5_auto_proceed_authorized": True,
            "R8_free_open_source_first": False,
        },
        "allowed_jargon": True,
        "destructive_confirm_only_real_harm": False,
    },
    "safe": {
        "id": "safe",
        "name": "🛡️ 稳健防误触模式 (Cautious Mode)",
        "description": "任何改动、删除前必须经人类二次确认；严禁任何自作主张的激进优化。",
        "persona_title": "安全审计员/新手用户",
        "rules_override": {
            "R9_strict_jargon_ban": True,
            "R9_require_renhua_brackets": True,
            "R5_strict_no_asking": False,
            "R5_auto_proceed_authorized": False,
            "R8_free_open_source_first": True,
        },
        "allowed_jargon": False,
        "destructive_confirm_only_real_harm": False,
    }
}

DEFAULT_CONFIG = {
    "version": "2.0.0",
    "active_profile": "vibe-boss",
    "custom_brain_dir": str(SUPEREGO_HOME / "archive"),
    "security": {
        "anti_prompt_injection": True,
        "data_overwrite_guard": True,
        "supply_chain_ast_scan": True,
        "process_leak_guard": True
    },
    "engine": {
        "fast_path_jev": True,
        "async_deep_judge": True,
        "max_fast_latency_ms": 600
    }
}


def load_config() -> dict:
    """动态加载全局配置，若不存在则使用安全默认值"""
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                cfg.update(user_cfg)
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> bool:
    """持久化保存配置到 ~/.superego/config.json"""
    try:
        SUPEREGO_HOME.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        sys.stderr.write(f"[superego_config] 保存配置失败: {e}\n")
        return False


def get_active_profile() -> dict:
    """获取当前激活的 Profile 配置"""
    cfg = load_config()
    pid = cfg.get("active_profile", "vibe-boss")
    return PROFILES.get(pid, PROFILES["vibe-boss"])


def get_brain_archive_dir() -> Path:
    """获取对话档案库路径，智能适配自定义配置或默认目录"""
    cfg = load_config()
    custom_dir = cfg.get("custom_brain_dir")
    if custom_dir and Path(custom_dir).exists():
        return Path(custom_dir)
    p = SUPEREGO_HOME / "archive"
    p.mkdir(parents=True, exist_ok=True)
    return p


if __name__ == "__main__":
    p = get_active_profile()
    print(f"Loaded Superego Profile: {p['name']} ({p['id']})")
    print(f"Archive Directory: {get_brain_archive_dir()}")
    print(f"System: {SYSTEM}")
