# -*- coding: utf-8 -*-
"""config.py —— Superego 2.0 统一动态配置与用户画像/规则包元框架 (Meta-Harness Config & Profile Engine).

核心理念:
  1. 冷热加载分离 (Cold/Hot Separation):
     - 冷层 (Tier 1 硬安全): 物理原生阻断反弹 Shell、注入与破坏性数据覆盖 (security_core.py)；
     - 热层 (Tier 2 行为外审): 规则包 (RulePacks) 与用户画像 (Profiles) 动态热插拔、热合并；
  2. 去个人法则化 (Decoupled User Sovereignty):
     - 任何人均可卸载 @frank/vibe-boss，使用自己的规则包搭建专属版本的 Superego；
     - 支持 profile init / merge / switch，支持自定义 ~/.superego/profiles 与 ~/.superego/rulepacks；
  3. CC-Switch 风格多模型外审路由器配置:
     - 兼容 OpenAI 格式端点 (DeepSeek, Qwen, Ollama, GPT, Claude 等)；
     - 兼容 TypeSafe Jev 强类型原语；
     - 零 Key 自动降级至 Tier 0 本地确定性引擎。
"""

import os
import sys
import json
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"

HOME = Path.home()
TRUTHGATE_HOME = HOME / ".truthgate"
SUPEREGO_HOME = HOME / ".superego"

# 优先使用 .truthgate，若存在旧的 .superego 则平滑兼容读取
APP_HOME = TRUTHGATE_HOME if TRUTHGATE_HOME.exists() else (SUPEREGO_HOME if SUPEREGO_HOME.exists() else TRUTHGATE_HOME)
CONFIG_FILE = APP_HOME / "config.json"
CUSTOM_PROFILES_DIR = APP_HOME / "profiles"
CUSTOM_RULEPACKS_DIR = APP_HOME / "rulepacks"

PACKAGE_DIR = Path(__file__).resolve().parent
BUILTIN_RULEPACKS_DIR = PACKAGE_DIR / "rulepacks"

# 内置核心预置画像 (Built-in Archetype Profiles)
BUILTIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "vibe-boss": {
        "id": "vibe-boss",
        "name": "👑 老板 / Vibe Coder 模式 (Frank 旗舰版)",
        "description": "严禁飙技术术语（必须人话括号解释）；严禁向用户请示（自作主张干到底）；死磕免费优先。",
        "persona_title": "业务主管 / 零代码产品指挥者",
        "rulepacks": [
            "@security/core-safe",
            "@frank/vibe-boss"
        ],
        "allowed_jargon": False,
        "destructive_confirm_only_real_harm": True,
        "rules_override": {
            "R9_strict_jargon_ban": True,
            "R9_require_renhua_brackets": True,
            "R5_strict_no_asking": True,
            "R5_auto_proceed_authorized": True,
            "R8_free_open_source_first": True,
        }
    },
    "engineer": {
        "id": "engineer",
        "name": "💻 资深工程师模式 (Engineer Mode)",
        "description": "放行代码变量与架构术语；强化单元测试与退出码验证；严控交付质量；严禁甩锅。",
        "persona_title": "资深软件架构师 / 开发工程师",
        "rulepacks": [
            "@security/core-safe",
            "@standard/engineer"
        ],
        "allowed_jargon": True,
        "destructive_confirm_only_real_harm": False,
        "rules_override": {
            "R9_strict_jargon_ban": False,
            "R9_require_renhua_brackets": False,
            "R5_strict_no_asking": False,
            "R5_auto_proceed_authorized": True,
            "R8_free_open_source_first": False,
        }
    },
    "safe": {
        "id": "safe",
        "name": "🛡️ 稳健防误触模式 (Cautious Mode)",
        "description": "任何改动、删除前必须经人类二次确认；严禁任何自作主张的激进优化。",
        "persona_title": "安全审计员 / 新手用户",
        "rulepacks": [
            "@security/core-safe",
            "@cautious/safe"
        ],
        "allowed_jargon": False,
        "destructive_confirm_only_real_harm": False,
        "rules_override": {
            "R9_strict_jargon_ban": True,
            "R9_require_renhua_brackets": True,
            "R5_strict_no_asking": False,
            "R5_auto_proceed_authorized": False,
            "R8_free_open_source_first": True,
        }
    }
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "3.0.0",
    "active_profile": "vibe-boss",
    "custom_brain_dir": str(SUPEREGO_HOME / "archive"),
    "security": {
        "anti_prompt_injection": True,
        "data_overwrite_guard": True,
        "supply_chain_ast_scan": True,
        "process_leak_guard": True
    },
    "critic": {
        "provider": "tiered",  # "tiered" | "agnes" | "jev" | "openai_compatible" | "local_heuristic"
        "base_url": "https://apihub.agnes-ai.com/v1",
        "model": "agnes-3.0-flash",
        "api_key": "env:AGNES_API_KEY",
        "timeout": 4.0
    },
    "engine": {
        "fast_path_jev": True,
        "async_deep_judge": True,
        "max_fast_latency_ms": 600
    },
    "ui": {
        "auto_open_dashboard": True
    }
}


def load_config() -> dict:
    """动态加载全局配置，若不存在则使用安全默认值"""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                cfg.update(user_cfg)
                if "critic" in user_cfg and isinstance(user_cfg["critic"], dict):
                    cfg["critic"].update(user_cfg["critic"])
                if "security" in user_cfg and isinstance(user_cfg["security"], dict):
                    cfg["security"].update(user_cfg["security"])
                if "ui" in user_cfg and isinstance(user_cfg["ui"], dict):
                    cfg["ui"].update(user_cfg["ui"])
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> bool:
    """持久化保存配置到 ~/.truthgate/config.json 并兼容写入 ~/.superego/config.json"""
    try:
        APP_HOME.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        # 兼容性镜像写入
        alt_home = SUPEREGO_HOME if APP_HOME == TRUTHGATE_HOME else TRUTHGATE_HOME
        try:
            alt_home.mkdir(parents=True, exist_ok=True)
            with open(alt_home / "config.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return True
    except Exception as e:
        sys.stderr.write(f"[truthgate_config] 保存配置失败: {e}\n")
        return False


def get_auto_open_dashboard() -> bool:
    """获取启动时是否自动弹出浏览器大盘"""
    cfg = load_config()
    return cfg.get("ui", {}).get("auto_open_dashboard", True)


def set_auto_open_dashboard(enabled: bool) -> bool:
    """设置启动时是否自动弹出浏览器大盘"""
    cfg = load_config()
    ui = cfg.setdefault("ui", {})
    ui["auto_open_dashboard"] = bool(enabled)
    return save_config(cfg)


def set_typesafe_key(api_key: str) -> bool:
    """配置并保存 TypeSafe Jev API Key"""
    cfg = load_config()
    cfg["typesafe_api_key"] = api_key.strip()
    cfg["jev_api_key"] = api_key.strip()
    # 同时写入 .env 文件
    for d in [TRUTHGATE_HOME, SUPEREGO_HOME]:
        try:
            d.mkdir(parents=True, exist_ok=True)
            env_file = d / ".env"
            lines = []
            if env_file.exists():
                lines = [ln for ln in env_file.read_text(encoding="utf-8-sig").splitlines() if not ln.startswith("TYPESAFE_API_KEY=")]
            lines.append(f"TYPESAFE_API_KEY={api_key.strip()}")
            env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception:
            pass
    return save_config(cfg)


# ──────────────────────────────────────────────────────────────────────────────
# 规则包管理 (RulePack Registry & Discovery)
# ──────────────────────────────────────────────────────────────────────────────

def list_rulepacks() -> Dict[str, dict]:
    """扫描所有可用规则包（内置包 + 用户自定义 ~/.superego/rulepacks/）"""
    packs = {}
    # 1. 扫描内置规则包
    if BUILTIN_RULEPACKS_DIR.exists():
        for p in BUILTIN_RULEPACKS_DIR.glob("*.rulepack.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_source"] = "builtin"
                    data["_path"] = str(p)
                    packs[data.get("id", p.stem)] = data
            except Exception:
                continue

    # 2. 扫描用户自定义规则包
    if CUSTOM_RULEPACKS_DIR.exists():
        for p in CUSTOM_RULEPACKS_DIR.glob("*.rulepack.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_source"] = "custom"
                    data["_path"] = str(p)
                    packs[data.get("id", p.stem)] = data
            except Exception:
                continue

    return packs


def get_rulepack(pack_id: str) -> Optional[dict]:
    """获取单个规则包定义"""
    all_packs = list_rulepacks()
    return all_packs.get(pack_id)


# ──────────────────────────────────────────────────────────────────────────────
# 画像管理 (Profile Registry & Operations)
# ──────────────────────────────────────────────────────────────────────────────

def list_profiles() -> Dict[str, dict]:
    """扫描所有可用画像（内置画像 + 用户自定义 ~/.superego/profiles/）"""
    profiles = dict(BUILTIN_PROFILES)
    if CUSTOM_PROFILES_DIR.exists():
        for p in CUSTOM_PROFILES_DIR.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pid = data.get("id", p.stem)
                    data["_source"] = "custom"
                    data["_path"] = str(p)
                    profiles[pid] = data
            except Exception:
                continue
    return profiles


def get_active_profile() -> dict:
    """获取当前激活的 Profile 配置"""
    cfg = load_config()
    pid = cfg.get("active_profile", "vibe-boss")
    all_profiles = list_profiles()
    return all_profiles.get(pid, BUILTIN_PROFILES["vibe-boss"])


def set_active_profile(profile_id: str) -> bool:
    """切换当前激活的 Profile"""
    all_profiles = list_profiles()
    if profile_id not in all_profiles:
        raise ValueError(f"画像 '{profile_id}' 不存在。可选画像: {list(all_profiles.keys())}")
    cfg = load_config()
    cfg["active_profile"] = profile_id
    return save_config(cfg)


def save_custom_profile(profile_data: dict) -> bool:
    """保存自定义画像至 ~/.superego/profiles/<id>.json"""
    pid = profile_data.get("id")
    if not pid:
        raise ValueError("画像必须包含 'id' 字段")
    CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    target = CUSTOM_PROFILES_DIR / f"{pid}.json"
    try:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        sys.stderr.write(f"[superego_config] 保存画像失败: {e}\n")
        return False


def merge_profiles(
    p1_id: str,
    p2_id: str,
    new_id: str,
    name: str = "",
    desc: str = ""
) -> dict:
    """合并两个画像（Profile Merge），生成并持久化新的画像"""
    all_profiles = list_profiles()
    p1 = all_profiles.get(p1_id)
    p2 = all_profiles.get(p2_id)
    if not p1 or not p2:
        raise ValueError(f"无法合并：找不到画像 {p1_id} 或 {p2_id}")

    # 合并规则包列表 (去重并保持顺序)
    merged_packs = []
    for pk in p1.get("rulepacks", []) + p2.get("rulepacks", []):
        if pk not in merged_packs:
            merged_packs.append(pk)

    # 合并 rules_override
    merged_override = dict(p1.get("rules_override", {}))
    merged_override.update(p2.get("rules_override", {}))

    merged = {
        "id": new_id,
        "name": name or f"🔀 合并画像: {p1.get('name')} + {p2.get('name')}",
        "description": desc or f"由 {p1_id} 与 {p2_id} 融合而成",
        "persona_title": f"{p1.get('persona_title', '')} / {p2.get('persona_title', '')}",
        "rulepacks": merged_packs,
        "allowed_jargon": p1.get("allowed_jargon", False) or p2.get("allowed_jargon", False),
        "destructive_confirm_only_real_harm": p1.get("destructive_confirm_only_real_harm", False) and p2.get("destructive_confirm_only_real_harm", False),
        "rules_override": merged_override
    }
    save_custom_profile(merged)
    return merged


def resolve_profile_rules(profile_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """解析指定画像（默认当前激活画像）激活的全部具体行为规则"""
    if profile_id:
        profile = list_profiles().get(profile_id, get_active_profile())
    else:
        profile = get_active_profile()

    active_rulepack_ids = profile.get("rulepacks", [])
    all_packs = list_rulepacks()

    resolved_rules = []
    seen_rule_ids = set()

    for pack_id in active_rulepack_ids:
        pack = all_packs.get(pack_id)
        if not pack:
            continue
        for r in pack.get("rules", []):
            rid = r.get("id")
            if rid and rid not in seen_rule_ids:
                seen_rule_ids.add(rid)
                rule_item = dict(r)
                rule_item["_pack_id"] = pack_id
                rule_item["_pack_name"] = pack.get("name", pack_id)
                resolved_rules.append(rule_item)

    return resolved_rules


# ──────────────────────────────────────────────────────────────────────────────
# 外审路由器配置 (Critic Config Operations)
# ──────────────────────────────────────────────────────────────────────────────

def get_critic_config() -> dict:
    """获取当前外审路由器配置"""
    cfg = load_config()
    return cfg.get("critic", DEFAULT_CONFIG["critic"])


def set_critic_config(
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None
) -> bool:
    """配置外审模型（类似 CC-Switch，可接入 DeepSeek / Qwen / Claude / 本地 Ollama / Jev）"""
    cfg = load_config()
    critic = cfg.setdefault("critic", dict(DEFAULT_CONFIG["critic"]))
    if provider is not None:
        if provider not in ["openai_compatible", "jev", "local_heuristic"]:
            raise ValueError(f"不支持的 provider: {provider}。支持: openai_compatible, jev, local_heuristic")
        critic["provider"] = provider
    if base_url is not None:
        critic["base_url"] = base_url
    if model is not None:
        critic["model"] = model
    if api_key is not None:
        critic["api_key"] = api_key
    if timeout is not None:
        critic["timeout"] = float(timeout)
    return save_config(cfg)


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
    print(f"Active Rulepacks: {p.get('rulepacks')}")
    print(f"Resolved Rules: {[r['id'] for r in resolve_profile_rules()]}")
    print(f"Critic Config: {get_critic_config()}")
    print(f"Archive Directory: {get_brain_archive_dir()}")
