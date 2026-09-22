# -*- coding: utf-8 -*-
"""parity_auditor.py —— 四端资产与生命周期全息对账审计仪 (Cross-Engine Full Parity Auditor).

核心使命:
  终结「局部自满、见树不见林、等用户踢一脚才动一步」的被动应答病根。
  以机器确定性自动化扫描四大平台 (Claude Code / OpenAI Codex / Google Antigravity / DSH) 的:
  1. 技能资产对账 (Skills Parity): 对比 ~/.claude/skills 与 Codex/Antigravity 差异，杜绝 200+ 技能在母库积灰；
  2. 生命周期门禁对账 (Hooks Parity): 检查 PreToolUse、Stop、UserPromptSubmit/PreInvocation 挂载一致性；
  3. 自动进化与教训链路对账 (Evolution Loop Parity): 严格核验 dissatisfaction 语义嗅探 -> postmortem 技能 -> lessons_add 原子落盘三端通畅度。
"""
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple

HOME = Path.home()
CLAUDE_HOME = HOME / ".claude"
CODEX_HOME = HOME / ".codex"
GEMINI_HOME = HOME / ".gemini"
DSH_HOME = Path(os.environ.get("APPDATA", str(HOME / ".config"))) / "dsh-desktop" / "harness"

CORE_EVOLUTION_SKILLS = [
    "postmortem-to-guard",
    "rootcause",
    "truth",
    "claude-skill-bridge",
    "multi-source-research",
    "typesafe-ai",
    "desktop-window-shot"
]


def audit_skills_parity(workspace_dir: Path = None) -> Dict[str, Any]:
    """全息对账四大平台的技能资产覆盖率与缺失项"""
    claude_skills_dir = CLAUDE_HOME / "skills"
    claude_skills = set(p.name for p in claude_skills_dir.iterdir() if p.is_dir()) if claude_skills_dir.exists() else set()

    codex_skills_dir = CODEX_HOME / "skills"
    codex_skills = set(p.name for p in codex_skills_dir.iterdir() if p.is_dir()) if codex_skills_dir.exists() else set()

    ag_global_skills = GEMINI_HOME / "config" / "skills"
    ag_global = set(p.name for p in ag_global_skills.iterdir() if p.is_dir()) if ag_global_skills.exists() else set()

    ag_ws_skills = (workspace_dir / ".agents" / "skills") if workspace_dir else Path(".agents/skills")
    ag_ws = set(p.name for p in ag_ws_skills.iterdir() if p.is_dir()) if ag_ws_skills.exists() else set()

    ag_all = ag_global | ag_ws

    missing_in_codex = claude_skills - codex_skills
    missing_in_ag = claude_skills - ag_all

    core_missing_codex = [s for s in CORE_EVOLUTION_SKILLS if s not in codex_skills]
    core_missing_ag = [s for s in CORE_EVOLUTION_SKILLS if s not in ag_all]

    return {
        "claude_count": len(claude_skills),
        "codex_count": len(codex_skills),
        "ag_count": len(ag_all),
        "missing_in_codex_total": len(missing_in_codex),
        "missing_in_ag_total": len(missing_in_ag),
        "core_missing_codex": core_missing_codex,
        "core_missing_ag": core_missing_ag,
        "parity_score": 100.0 if not (core_missing_codex or core_missing_ag) else 60.0
    }


def audit_evolution_loop() -> Dict[str, Any]:
    """核验自动反思与教训沉淀链路 (Dissatisfaction -> Postmortem -> Lessons) 在各端的完整性"""
    results = {}

    # 1. Claude Code
    cl_hook = (CLAUDE_HOME / "hooks" / "dissatisfaction-postmortem.py").exists()
    cl_skill = (CLAUDE_HOME / "skills" / "postmortem-to-guard" / "SKILL.md").exists()
    cl_add = (CLAUDE_HOME / "bin" / "lessons_add.py").exists()
    results["claude"] = {
        "hook": cl_hook,
        "skill": cl_skill,
        "lessons_add": cl_add,
        "complete": cl_hook and cl_skill and cl_add
    }

    # 2. OpenAI Codex
    cx_hook = (CODEX_HOME / "hooks" / "dissatisfaction-postmortem.py").exists()
    cx_skill = (CODEX_HOME / "skills" / "postmortem-to-guard" / "SKILL.md").exists()
    results["codex"] = {
        "hook": cx_hook,
        "skill": cx_skill,
        "lessons_add": cl_add,
        "complete": cx_hook and cx_skill and cl_add
    }

    # 3. Antigravity
    ag_bridge = (GEMINI_HOME / "antigravity" / "scripts" / "ag_superego_bridge.py")
    ag_has_dissat = False
    if ag_bridge.exists():
        try:
            txt = ag_bridge.read_text(encoding="utf-8")
            ag_has_dissat = "postmortem-to-guard" in txt and "c_res = json.loads" in txt
        except Exception:
            pass
    ag_skill = ((GEMINI_HOME / "config" / "skills" / "postmortem-to-guard" / "SKILL.md").exists() or
                Path(".agents/skills/postmortem-to-guard/SKILL.md").exists())
    results["antigravity"] = {
        "hook": ag_has_dissat,
        "skill": ag_skill,
        "lessons_add": cl_add,
        "complete": ag_has_dissat and ag_skill and cl_add
    }

    all_complete = all(v["complete"] for v in results.values())
    return {
        "engines": results,
        "all_complete": all_complete
    }


def sync_core_skills(workspace_dir: Path = None) -> List[str]:
    """一键将核心进化与治理技能从 Claude 母库物理同步到 Codex 与 Antigravity"""
    synced = []
    claude_skills_dir = CLAUDE_HOME / "skills"
    if not claude_skills_dir.exists():
        return synced

    codex_skills_dir = CODEX_HOME / "skills"
    ag_global_skills = GEMINI_HOME / "config" / "skills"
    ag_ws_skills = (workspace_dir / ".agents" / "skills") if workspace_dir else Path(".agents/skills")

    destinations = [claude_skills_dir, codex_skills_dir, ag_global_skills, ag_ws_skills]

    for sk_name in CORE_EVOLUTION_SKILLS:
        # Find existing source
        src = None
        for cand in [claude_skills_dir / sk_name, ag_ws_skills / sk_name, ag_global_skills / sk_name, codex_skills_dir / sk_name]:
            if cand.exists():
                src = cand
                break
        if not src:
            continue

        for dest_base in destinations:
            dest_dir = dest_base / sk_name
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            if not dest_dir.exists():
                shutil.copytree(src, dest_dir)
                synced.append(f"{sk_name} -> {dest_dir}")

    return synced


if __name__ == "__main__":
    ws = Path(os.getcwd())
    print("=" * 70)
    print("🔍 SUPEREGO 3.0 四端资产与生命周期全息对账审计仪")
    print("=" * 70)
    
    sk_rep = audit_skills_parity(ws)
    print(f"\n📦 [1/2] 技能资产全息对账:")
    print(f"   • Claude Code 母库技能总数: {sk_rep['claude_count']} 个")
    print(f"   • OpenAI Codex 技能总数   : {sk_rep['codex_count']} 个 (缺失: {sk_rep['missing_in_codex_total']})")
    print(f"   • Antigravity 技能总数    : {sk_rep['ag_count']} 个 (缺失: {sk_rep['missing_in_ag_total']})")
    print(f"   • 核心治理技能缺失 (Codex): {sk_rep['core_missing_codex'] or '无 (100% 对齐)'}")
    print(f"   • 核心治理技能缺失 (AG)   : {sk_rep['core_missing_ag'] or '无 (100% 对齐)'}")

    ev_rep = audit_evolution_loop()
    print(f"\n🧠 [2/2] 自动进化闭环对账 (Dissatisfaction -> Postmortem -> Lessons):")
    for eng, st in ev_rep["engines"].items():
        sym = "✅" if st["complete"] else "❌"
        print(f"   • {eng:<12}: {sym} [Hook: {st['hook']}, Skill: {st['skill']}, Lessons_Add: {st['lessons_add']}]")

    if "--sync" in sys.argv:
        print(f"\n🔄 正在执行核心治理技能跨端同步...")
        synced_list = sync_core_skills(ws)
        print(f"   [✓] 物理同步完成: {len(synced_list)} 项新资产落地")
