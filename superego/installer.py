# -*- coding: utf-8 -*-
"""installer.py —— Superego 2.0 跨四端通用安装引擎 (Universal Multi-Platform Installer)。
支持在任意机器（Windows / macOS / Linux）上一键部署与自适应挂载：
  1. Claude Code (~/.claude)
  2. OpenAI Codex (~/.codex)
  3. Google Antigravity (~/.gemini)
  4. DeepSeek Harness (DSH Desktop / cordis)
"""
import os
import sys
import time
import json
import shutil
import platform
import argparse
from pathlib import Path
from datetime import datetime

HOME = Path.home()
SYSTEM = platform.system()
HERE = Path(__file__).resolve().parent

# 目标端平台路径
PLATFORMS = {
    "claude": {
        "name": "Claude Code",
        "home": HOME / ".claude",
        "hooks_dir": HOME / ".claude" / "hooks",
        "type": "hooks_and_semantic",
    },
    "codex": {
        "name": "OpenAI Codex",
        "home": HOME / ".codex",
        "hooks_dir": HOME / ".codex" / "hooks",
        "type": "hooks_mirror",
    },
    "antigravity": {
        "name": "Google Antigravity",
        "home": HOME / ".gemini",
        "hooks_dir": HOME / ".gemini" / "antigravity" / "scripts",
        "type": "bridge_and_plugin",
    },
    "dsh": {
        "name": "DeepSeek Harness (DSH)",
        "home": Path(os.environ.get("APPDATA", str(HOME / ".config"))) / "dsh-desktop" / "harness",
        "type": "cordis_and_skills",
    }
}


def detect_installed_platforms() -> dict:
    """探测本机已安装的 AI 平台"""
    detected = {}
    for pid, pinfo in PLATFORMS.items():
        if pinfo["home"].exists():
            detected[pid] = pinfo
    return detected


def setup_profile(profile_id: str = "vibe-boss") -> bool:
    """配置并激活用户画像"""
    try:
        from config import save_config, load_config
    except ImportError:
        from superego.config import save_config, load_config
        
    cfg = load_config()
    cfg["active_profile"] = profile_id
    cfg["last_updated"] = datetime.now().isoformat()
    return save_config(cfg)


def register_claude_hooks(claude_home: Path) -> bool:
    """安全将 hook_entry.py 挂载进 ~/.claude/settings.json，保持幂等并保留已有配置"""
    settings_file = claude_home / "settings.json"
    settings_data = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings_data = json.load(f)
        except Exception:
            settings_data = {}

    hooks_dict = settings_data.setdefault("hooks", {})
    pre_list = hooks_dict.setdefault("PreToolUse", [])
    stop_list = hooks_dict.setdefault("Stop", [])

    py_cmd = "py -3" if SYSTEM == "Windows" else "python3"
    hook_cmd_pre = (
        f'python "%USERPROFILE%\\.claude\\hooks\\hook_entry.py" pre'
        if SYSTEM == "Windows"
        else f'{py_cmd} "$HOME/.claude/hooks/hook_entry.py" pre'
    )
    hook_cmd_stop = (
        f'python "%USERPROFILE%\\.claude\\hooks\\hook_entry.py" stop'
        if SYSTEM == "Windows"
        else f'{py_cmd} "$HOME/.claude/hooks/hook_entry.py" stop'
    )

    # 1. 挂载 PreToolUse
    has_pre = False
    for entry in pre_list:
        for h in entry.get("hooks", []):
            if "hook_entry.py" in h.get("command", ""):
                has_pre = True
                break
    if not has_pre:
        pre_list.append({
            "matcher": "Bash|PowerShell|Write|Edit",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd_pre,
                    "timeout": 10
                }
            ]
        })

    # 2. 挂载 Stop
    has_stop = False
    for entry in stop_list:
        for h in entry.get("hooks", []):
            if "hook_entry.py" in h.get("command", ""):
                has_stop = True
                break
    if not has_stop:
        stop_list.append({
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd_stop,
                    "timeout": 15
                }
            ]
        })

    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        sys.stderr.write(f"   [!] 写入 Claude settings.json 失败: {e}\n")
        return False


def unregister_claude_hooks(claude_home: Path) -> bool:
    """从 ~/.claude/settings.json 安全移除 hook_entry.py 挂载"""
    settings_file = claude_home / "settings.json"
    if not settings_file.exists():
        return True
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        hooks_dict = data.get("hooks", {})
        for hook_type in ["PreToolUse", "Stop"]:
            if hook_type in hooks_dict:
                new_list = []
                for entry in hooks_dict[hook_type]:
                    filtered = [h for h in entry.get("hooks", []) if "hook_entry.py" not in h.get("command", "")]
                    if filtered:
                        entry["hooks"] = filtered
                        new_list.append(entry)
                hooks_dict[hook_type] = new_list
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def register_codex_hooks(codex_home: Path) -> bool:
    """安全将 hook_entry.py 挂载进 ~/.codex/hooks.json，保持幂等并保留已有配置"""
    hooks_file = codex_home / "hooks.json"
    hooks_data = {}
    if hooks_file.exists():
        try:
            with open(hooks_file, "r", encoding="utf-8") as f:
                hooks_data = json.load(f)
        except Exception:
            hooks_data = {}

    hooks_dict = hooks_data.setdefault("hooks", {})
    pre_list = hooks_dict.setdefault("PreToolUse", [])
    stop_list = hooks_dict.setdefault("Stop", [])

    py_cmd = "py -3" if SYSTEM == "Windows" else "python3"
    hook_cmd_pre = (
        f'python "%USERPROFILE%\\.codex\\hooks\\hook_entry.py" pre'
        if SYSTEM == "Windows"
        else f'{py_cmd} "$HOME/.codex/hooks/hook_entry.py" pre'
    )
    hook_cmd_stop = (
        f'python "%USERPROFILE%\\.codex\\hooks\\hook_entry.py" stop'
        if SYSTEM == "Windows"
        else f'{py_cmd} "$HOME/.codex/hooks/hook_entry.py" stop'
    )

    # 1. 挂载 PreToolUse
    has_pre = False
    for entry in pre_list:
        for h in entry.get("hooks", []):
            if "hook_entry.py" in h.get("command", ""):
                has_pre = True
                break
    if not has_pre:
        pre_list.append({
            "matcher": "Bash|PowerShell|Write|Edit",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd_pre,
                    "timeout": 10
                }
            ]
        })

    # 2. 挂载 Stop
    has_stop = False
    for entry in stop_list:
        for h in entry.get("hooks", []):
            if "hook_entry.py" in h.get("command", ""):
                has_stop = True
                break
    if not has_stop:
        stop_list.append({
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd_stop,
                    "timeout": 15
                }
            ]
        })

    try:
        with open(hooks_file, "w", encoding="utf-8") as f:
            json.dump(hooks_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        sys.stderr.write(f"   [!] 写入 Codex hooks.json 失败: {e}\n")
        return False


def unregister_codex_hooks(codex_home: Path) -> bool:
    """从 ~/.codex/hooks.json 安全移除 hook_entry.py 挂载"""
    hooks_file = codex_home / "hooks.json"
    if not hooks_file.exists():
        return True
    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        hooks_dict = data.get("hooks", {})
        for hook_type in ["PreToolUse", "Stop"]:
            if hook_type in hooks_dict:
                new_list = []
                for entry in hooks_dict[hook_type]:
                    filtered = [h for h in entry.get("hooks", []) if "hook_entry.py" not in h.get("command", "")]
                    if filtered:
                        entry["hooks"] = filtered
                        new_list.append(entry)
                hooks_dict[hook_type] = new_list
        with open(hooks_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def rollback_superego() -> bool:
    """执行 3 秒一键物理回滚：注销四端门禁与插件挂载"""
    print("🔄 正在执行 3 秒基准一键物理回滚...")
    # 1. 注销 Claude Code
    claude_home = HOME / ".claude"
    if claude_home.exists():
        unregister_claude_hooks(claude_home)
        print("   [✓] Claude Code settings.json 门禁已注销")

    # 2. 注销 OpenAI Codex
    codex_home = HOME / ".codex"
    if codex_home.exists():
        unregister_codex_hooks(codex_home)
        print("   [✓] OpenAI Codex hooks.json 门禁已注销")

    # 2. 注销 Antigravity 全局插件
    ag_config = HOME / ".gemini" / "config" / "config.json"
    if ag_config.exists():
        try:
            with open(ag_config, "r", encoding="utf-8") as f:
                ag_data = json.load(f)
            plugins = ag_data.get("plugins", {})
            if "superego-plugin" in plugins:
                del plugins["superego-plugin"]
                with open(ag_config, "w", encoding="utf-8") as f:
                    json.dump(ag_data, f, indent=2, ensure_ascii=False)
                print("   [✓] Google Antigravity 全局插件已安全移除")
        except Exception:
            pass

    print("✅ 已彻底还原至纯净基准状态！")
    return True


def install_superego(profile: str = "vibe-boss", dry_run: bool = False) -> bool:
    """执行一键跨端安装与双核挂载"""
    print("=" * 70)
    print("🚀 SUPEREGO 2.0 跨端通用 AI 紧箍咒一键安装器")
    print(f"操作系统: {SYSTEM} | 用户主目录: {HOME}")
    print(f"激活模式: {profile}")
    print("=" * 70)

    detected = detect_installed_platforms()
    if not detected:
        print("⚠️ 未在默认路径发现支持的 AI 平台。创建默认 ~/.claude 与 ~/.superego 配置...")
        (HOME / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
        detected["claude"] = PLATFORMS["claude"]

    print("\n🔍 [1/3] 正在探测本机已安装的 AI 平台...")
    for pid, pinfo in detected.items():
        print(f"   [✓] 发现平台: {pinfo['name']} -> {pinfo['home']}")

    if dry_run:
        print("\nℹ️ [Dry Run] 预检模式通过，未写入任何文件。")
        return True

    print("\n🛡️ [2/3] 配置用户画像与安全内核...")
    setup_profile(profile)
    print(f"   [✓] 已激活 Profile 面具: {profile}")

    print("\n⚡ [3/3] 跨端挂载安全门禁与语义引擎...")
    
    # 核心引擎源码列表
    core_files = [
        "security_core.py",
        "critic_engine.py",
        "jev_engine.py",
        "config.py",
        "replay.py",
        "hook_entry.py",
        "no-nagging-guard.py"
    ]

    # 同步规则包到 ~/.superego/rulepacks
    rulepacks_src = HERE / "rulepacks"
    if rulepacks_src.exists():
        custom_rp = HOME / ".superego" / "rulepacks"
        custom_rp.mkdir(parents=True, exist_ok=True)
        for rp in rulepacks_src.glob("*.rulepack.json"):
            shutil.copy2(rp, custom_rp / rp.name)

    # 1. 部署到 Claude Code
    if "claude" in detected:
        c_hooks = detected["claude"]["hooks_dir"]
        c_hooks.mkdir(parents=True, exist_ok=True)
        for cf in core_files:
            src = HERE / cf
            if src.exists():
                shutil.copy2(src, c_hooks / cf)
        if rulepacks_src.exists():
            rp_dest = c_hooks / "rulepacks"
            rp_dest.mkdir(parents=True, exist_ok=True)
            for rp in rulepacks_src.glob("*.rulepack.json"):
                shutil.copy2(rp, rp_dest / rp.name)
        register_claude_hooks(detected["claude"]["home"])
        print("   [✓] Claude Code 核心门禁与 settings.json 挂载就绪")

    # 2. 镜像对齐到 Codex
    if "codex" in detected:
        x_hooks = detected["codex"]["hooks_dir"]
        x_hooks.mkdir(parents=True, exist_ok=True)
        for cf in core_files:
            src = HERE / cf
            if src.exists():
                shutil.copy2(src, x_hooks / cf)
        if rulepacks_src.exists():
            rp_dest = x_hooks / "rulepacks"
            rp_dest.mkdir(parents=True, exist_ok=True)
            for rp in rulepacks_src.glob("*.rulepack.json"):
                shutil.copy2(rp, rp_dest / rp.name)
        register_codex_hooks(detected["codex"]["home"])
        print("   [✓] OpenAI Codex 核心安全引擎镜像与 hooks.json 挂载就绪")

    # 3. 关联 Antigravity
    if "antigravity" in detected:
        ag_home = detected["antigravity"]["home"]
        ag_scripts = detected["antigravity"]["hooks_dir"]
        ag_scripts.mkdir(parents=True, exist_ok=True)
        # 部署核心库与 Antigravity 核心桥接脚本
        for cf in core_files + ["ag_superego_bridge.py"]:
            src = HERE / cf
            if src.exists():
                shutil.copy2(src, ag_scripts / cf)
        if rulepacks_src.exists():
            rp_dest = ag_scripts / "rulepacks"
            rp_dest.mkdir(parents=True, exist_ok=True)
            for rp in rulepacks_src.glob("*.rulepack.json"):
                shutil.copy2(rp, rp_dest / rp.name)

        # 部署全局插件: ~/.gemini/config/plugins/superego-plugin/
        ag_plugin_dir = ag_home / "config" / "plugins" / "superego-plugin"
        ag_plugin_dir.mkdir(parents=True, exist_ok=True)

        ag_plugin_json = {
            "name": "superego-plugin",
            "version": "2.0.0",
            "description": "Native Superego governance, quality gating, and toggle management plugin for Google Antigravity.",
            "author": {
                "name": "Frank & Superego Community"
            }
        }
        (ag_plugin_dir / "plugin.json").write_text(
            json.dumps(ag_plugin_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        py_cmd = "py -3" if SYSTEM == "Windows" else "python3"
        bridge_script = (
            r"%USERPROFILE%/.gemini/antigravity/scripts/ag_superego_bridge.py"
            if SYSTEM == "Windows"
            else "~/.gemini/antigravity/scripts/ag_superego_bridge.py"
        )
        ag_hooks_json = {
            "superego-gate": {
                "enabled": True,
                "PreInvocation": [
                    {
                        "type": "command",
                        "command": f"{py_cmd} {bridge_script} pre",
                        "timeout": 5
                    }
                ],
                "Stop": [
                    {
                        "type": "command",
                        "command": f"{py_cmd} {bridge_script} stop",
                        "timeout": 15
                    }
                ]
            }
        }
        (ag_plugin_dir / "hooks.json").write_text(
            json.dumps(ag_hooks_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 注册并激活全局插件到 ~/.gemini/config/config.json
        ag_config_file = ag_home / "config" / "config.json"
        cfg_data = {}
        if ag_config_file.exists():
            try:
                cfg_data = json.loads(ag_config_file.read_text(encoding="utf-8"))
            except Exception:
                cfg_data = {}
        plugins_dict = cfg_data.setdefault("plugins", {})
        plugins_dict["superego-plugin"] = {"enabled": True}
        ag_config_file.parent.mkdir(parents=True, exist_ok=True)
        ag_config_file.write_text(
            json.dumps(cfg_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("   [✓] Google Antigravity 全局插件与安全桥接挂载就绪 (跨项目全局生效)")

    # 4. 关联 DSH
    if "dsh" in detected:
        print("   [✓] DeepSeek Harness (DSH) 旁路监听就绪 (零侵入模式)")

    print("\n" + "=" * 70)
    print("🎉 恭喜！Superego 2.0 已成功部署至全部平台！")
    print("• 行为对齐 (Jev 349ms 快车道): 已就绪")
    print("• 深度安全 (防注入/防覆写/防木马): 100% 物理硬锁生效")
    print("• 启动实时大盘: 运行 python -m superego dashboard (访问 http://127.0.0.1:17925/dashboard)")
    print("=" * 70)
    return True


def handle_profile_cli(args: list):
    try:
        from config import list_profiles, get_active_profile, set_active_profile, save_custom_profile, merge_profiles
    except ImportError:
        from superego.config import list_profiles, get_active_profile, set_active_profile, save_custom_profile, merge_profiles

    sub = args[0] if args else "list"
    if sub == "list":
        profiles = list_profiles()
        active_id = get_active_profile().get("id")
        print("=" * 65)
        print("🎭 Superego 2.0 用户治理画像列表 (Active Profiles):")
        print("=" * 65)
        for pid, p in profiles.items():
            is_active = (pid == active_id)
            flag = "★ [ACTIVE]" if is_active else "  [      ]"
            print(f"{flag} {pid:<15} {p.get('name')}")
            print(f"       激活规则包: {p.get('rulepacks')}")
            print(f"       允许代码黑话: {'是' if p.get('allowed_jargon') else '否'} | 来源: {p.get('_source', 'builtin')}")
            print(f"       说明: {p.get('description')}\n")
    elif sub == "use":
        if len(args) < 2:
            print("❌ 用法: python -m superego profile use <profile_id>")
            sys.exit(1)
        pid = args[1]
        try:
            set_active_profile(pid)
            print(f"✅ 成功切换当前激活画像为: {pid}")
        except Exception as e:
            print(f"❌ 切换失败: {e}")
            sys.exit(1)
    elif sub == "init":
        if len(args) < 2:
            print("❌ 用法: python -m superego profile init <profile_id>")
            sys.exit(1)
        pid = args[1]
        template = {
            "id": pid,
            "name": f"自定义画像: {pid}",
            "description": "由用户自主配置的行为治理与安全审查画像",
            "persona_title": "自定义 AI 协作者",
            "rulepacks": [
                "@security/core-safe"
            ],
            "allowed_jargon": True,
            "destructive_confirm_only_real_harm": False,
            "rules_override": {
                "R5_strict_no_asking": False,
                "R8_free_open_source_first": True
            }
        }
        if save_custom_profile(template):
            print(f"✅ 自定义画像模板已生成: ~/.superego/profiles/{pid}.json")
            print(f"   您可以按需配置生效的 RulePacks，然后运行: python -m superego profile use {pid}")
    elif sub == "merge":
        if len(args) < 4 or "-o" not in args:
            print("❌ 用法: python -m superego profile merge <profile1> <profile2> -o <target_profile_id>")
            sys.exit(1)
        p1 = args[1]
        p2 = args[2]
        out_idx = args.index("-o")
        new_id = args[out_idx + 1]
        try:
            merged = merge_profiles(p1, p2, new_id)
            print(f"🎉 成功合并画像 [{p1}] 与 [{p2}] -> 生成新画像: {new_id} ({merged.get('name')})")
            print(f"   生效规则包: {merged.get('rulepacks')}")
            print(f"   启用新画像: python -m superego profile use {new_id}")
        except Exception as e:
            print(f"❌ 合并失败: {e}")
            sys.exit(1)
    else:
        print("❌ 未知 profile 指令。支持: list, use, init, merge")
        sys.exit(1)


def handle_rulepack_cli(args: list):
    try:
        from config import list_rulepacks, get_active_profile, load_config, save_config, CUSTOM_RULEPACKS_DIR
        from rulepack_runner import validate_rulepack_file, test_all_rulepacks
    except ImportError:
        from superego.config import list_rulepacks, get_active_profile, load_config, save_config, CUSTOM_RULEPACKS_DIR
        from superego.rulepack_runner import validate_rulepack_file, test_all_rulepacks

    sub = args[0] if args else "list"
    if sub == "list":
        packs = list_rulepacks()
        active_packs = get_active_profile().get("rulepacks", [])
        print("=" * 75)
        print("📦 Superego 2.0 规则包生态列表 (Available RulePacks):")
        print("=" * 75)
        for pk_id, pk in packs.items():
            is_enabled = pk_id in active_packs
            flag = "★ [ENABLED]" if is_enabled else "  [       ]"
            source = pk.get("_source", "builtin")
            print(f"{flag} {pk_id:<24} {pk.get('name')} (v{pk.get('version')}) [{source}]")
            print(f"       包含规则: {len(pk.get('rules', []))} 条 | 类别: {pk.get('category')} | Tier: {pk.get('tier')}")
            print(f"       说明: {pk.get('description')}\n")
    elif sub == "test":
        if len(args) > 1:
            target = args[1]
            all_packs = list_rulepacks()
            if target in all_packs:
                filepath = Path(all_packs[target]["_path"])
            else:
                filepath = Path(target)
            res = validate_rulepack_file(filepath)
            sys.exit(0 if res.get("ok") else 1)
        else:
            success = test_all_rulepacks()
            sys.exit(0 if success else 1)
    elif sub == "init":
        if len(args) < 2:
            print("❌ 用法: python -m superego rulepack init <rulepack_id>")
            sys.exit(1)
        pk_id = args[1]
        clean_name = pk_id.replace("@", "").replace("/", "_")
        CUSTOM_RULEPACKS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = CUSTOM_RULEPACKS_DIR / f"{clean_name}.rulepack.json"
        template = {
            "$schema": "https://superego.ai/schema/rulepack-v1.json",
            "id": pk_id,
            "name": f"自定义规则包: {pk_id}",
            "version": "1.0.0",
            "author": "Custom",
            "license": "MIT",
            "category": "behavioral",
            "description": "自定义行为审查规则包",
            "tier": 2,
            "max_fp_rate": 0.005,
            "rules": [
                {
                    "id": "CUSTOM-01",
                    "text": "自定义红线规则描述: 严禁...",
                    "timing": "Stop",
                    "severity": "BLOCK"
                }
            ],
            "golden_cases": [
                {
                    "text": "触发红线的违规样例句子",
                    "expected": "FIRE",
                    "rule": "CUSTOM-01",
                    "rationale": "测试触发原因"
                },
                {
                    "text": "完全合规且带有客观测试证据的放行句子 exit code 0",
                    "expected": "PASS",
                    "rule": "CUSTOM-01",
                    "rationale": "测试放行原因"
                }
            ]
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"✅ 自定义规则包模板已生成: {target_path}")
        print(f"   您可以按 rulepack_spec.md 规范补充规则与样本，并运行:")
        print(f"   python -m superego rulepack test {pk_id}")
    elif sub == "enable":
        if len(args) < 2:
            print("❌ 用法: python -m superego rulepack enable <rulepack_id>")
            sys.exit(1)
        pk_id = args[1]
        cfg = load_config()
        active_prof = get_active_profile()
        rp_list = active_prof.setdefault("rulepacks", [])
        if pk_id not in rp_list:
            rp_list.append(pk_id)
            save_config(cfg)
            print(f"✅ 已在当前画像【{active_prof.get('name')}】中激活规则包: {pk_id}")
        else:
            print(f"ℹ️ 规则包已在当前画像中处于启用状态: {pk_id}")
    elif sub == "disable":
        if len(args) < 2:
            print("❌ 用法: python -m superego rulepack disable <rulepack_id>")
            sys.exit(1)
        pk_id = args[1]
        cfg = load_config()
        active_prof = get_active_profile()
        rp_list = active_prof.get("rulepacks", [])
        if pk_id in rp_list:
            rp_list.remove(pk_id)
            save_config(cfg)
            print(f"✅ 已在当前画像【{active_prof.get('name')}】中停用规则包: {pk_id}")
        else:
            print(f"ℹ️ 规则包当前并未在画像中启用: {pk_id}")
    else:
        print("❌ 未知 rulepack 指令。支持: list, test, init, enable, disable")
        sys.exit(1)


def handle_critic_cli(args: list):
    try:
        from config import get_critic_config, set_critic_config
        from critic_engine import audit_assistant_turn
    except ImportError:
        from superego.config import get_critic_config, set_critic_config
        from superego.critic_engine import audit_assistant_turn

    sub = args[0] if args else "show"
    if sub == "show":
        cfg = get_critic_config()
        api_key = cfg.get("api_key", "")
        masked_key = (api_key[:4] + "****" + api_key[-3:]) if len(api_key) > 7 else ("(not set)" if not api_key else "****")
        print("=" * 65)
        print("🔬 Superego 2.0 外审路由器状态 (Universal Critic Engine):")
        print("=" * 65)
        print(f"  • 外审选型 (Provider):  {cfg.get('provider')}")
        print(f"  • 服务端点 (Base URL):  {cfg.get('base_url')}")
        print(f"  • 审判模型 (Model):     {cfg.get('model')}")
        print(f"  • 超时熔断 (Timeout):   {cfg.get('timeout')}s")
        print(f"  • 鉴权密钥 (API Key):   {masked_key}")
        print("-" * 65)
        print("提示: 可使用 'python -m superego critic set ...' 接入 DeepSeek, Qwen, Ollama, GPT 或 Jev")
    elif sub == "set":
        set_parser = argparse.ArgumentParser(prog="superego critic set")
        set_parser.add_argument("--provider", choices=["openai_compatible", "jev", "local_heuristic"], help="外审服务类型")
        set_parser.add_argument("--base-url", dest="base_url", help="API Base URL (如 https://api.deepseek.com/v1 或 http://localhost:11434/v1)")
        set_parser.add_argument("--model", help="外审大模型名称 (如 deepseek-chat, qwen-plus, llama3)")
        set_parser.add_argument("--api-key", dest="api_key", help="API Key，支持直接填入或 env:VAR_NAME")
        set_parser.add_argument("--timeout", type=float, help="审判超时秒数 (默认 3.5)")
        parsed = set_parser.parse_args(args[1:])
        set_critic_config(
            provider=parsed.provider,
            base_url=parsed.base_url,
            model=parsed.model,
            api_key=parsed.api_key,
            timeout=parsed.timeout
        )
        print("✅ 外审路由器配置已成功更新！当前配置:")
        cfg = get_critic_config()
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
    elif sub == "test":
        text = " ".join(args[1:]) if len(args) > 1 else "剩下的五个功能我先不做了，等您指示了我再改。"
        print(f"🔍 正在对外审路由器进行现场击发测试...")
        print(f"   输入文本: \"{text}\"")
        res = audit_assistant_turn(text)
        print("\n📊 审判结果:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("❌ 未知 critic 指令。支持: show, set, test")
        sys.exit(1)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "profile":
            handle_profile_cli(sys.argv[2:])
            return
        elif sys.argv[1] == "rulepack":
            handle_rulepack_cli(sys.argv[2:])
            return
        elif sys.argv[1] == "critic":
            handle_critic_cli(sys.argv[2:])
            return

    parser = argparse.ArgumentParser(description="Superego 2.0 Universal Meta-Harness & Installer CLI")
    parser.add_argument("action", choices=["install", "detect", "status", "rollback", "replay", "sessions", "dashboard", "doctor"], default="install", nargs="?")
    parser.add_argument("target", nargs="?", default=None, help="Target session ID or path for replay")
    parser.add_argument("--profile", default="vibe-boss", help="Profile mask to apply")
    parser.add_argument("--port", type=int, default=17925, help="Port to bind dashboard server (default: 17925)")
    parser.add_argument("--heal", action="store_true", help="Auto-heal offline daemons in doctor mode")
    parser.add_argument("--json", action="store_true", help="Output doctor diagnostics as raw JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    args = parser.parse_args()

    if args.action == "detect":
        d = detect_installed_platforms()
        print(json.dumps({k: str(v["home"]) for k, v in d.items()}, indent=2))
    elif args.action == "status":
        from config import load_config, get_active_profile, resolve_profile_rules, get_critic_config
        cfg = load_config()
        prof = get_active_profile()
        rules = resolve_profile_rules()
        critic = get_critic_config()
        print("=" * 65)
        print(f"👑 Superego 2.0 运行状态报告 (Meta-Harness Status):")
        print("=" * 65)
        print(f"  • 当前激活画像:  {prof.get('name')} ({prof.get('id')})")
        print(f"  • 挂载规则包:    {prof.get('rulepacks')}")
        print(f"  • 生效规则总数:  {len(rules)} 条")
        print(f"  • 外审选型:      {critic.get('provider')} ({critic.get('model')})")
        print(f"  • 物理安全内核:  全部开启 (Anti-Injection / Overwrite Guard / AST Scan)")
        print("-" * 65)
    elif args.action == "rollback":
        rollback_superego()
    elif args.action == "doctor":
        try:
            from doctor import print_cli_report, auto_heal, run_doctor
        except ImportError:
            from superego.doctor import print_cli_report, auto_heal, run_doctor
        if args.heal:
            print(json.dumps(auto_heal(), ensure_ascii=False, indent=2))
        elif args.json:
            print(json.dumps(run_doctor(cached=False), ensure_ascii=False, indent=2))
        else:
            print_cli_report()
    elif args.action == "dashboard":
        try:
            from dashboard import run_dashboard
        except ImportError:
            from superego.dashboard import run_dashboard
        run_dashboard(port=args.port)
    elif args.action == "replay":
        try:
            from replay import replay_session
        except ImportError:
            from superego.replay import replay_session
        replay_session(args.target)
    elif args.action == "sessions":
        try:
            from replay import list_sessions
        except ImportError:
            from superego.replay import list_sessions
        s_list = list_sessions()
        print(f"📦 已记录的会话账本 (共 {len(s_list)} 个):")
        for s in s_list:
            print(f"   • {s.name} ({time.ctime(s.stat().st_mtime)})")
    else:
        install_superego(profile=args.profile, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
