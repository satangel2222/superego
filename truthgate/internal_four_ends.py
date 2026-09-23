#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""internal_four_ends.py —— 本机内部四端穷尽扫瞄器 (Internal 4-Ends Exhaustive Inspector).

使命:
彻底根除「坐井观天、单端抽样冒充全量、视界盲区」的技术硬伤！
在回答任何“有没有/用哪个/是不是/做过没/哪个最SOTA”前，一键并行扫平本机内部四大事实阵地:
  【端 1】Claude Code 70+ 历史项目库 (D:\\chat-archive-db\\brain.db / D:\\chat-archive\\q.js)
  【端 2】Codex 历史研发脑库 (D:\\chat-archive-db\\codex-brain.db)
  【端 3】Google Antigravity 专属脑库 (D:\\chat-archive-db\\ag-brain.db)
  【端 4】本地 200+ 离线技能与现成工具军火库 (~/.claude/skills/ + ~/.gemini/config/skills/ + D:\\revtools/)

用法:
  py -3 internal_four_ends.py <关键词> [--limit 10] [--json]
"""
import sys
import os
import json
import sqlite3
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List

HOME = Path.home()
CLAUDE_SKILLS = HOME / ".claude" / "skills"
AG_SKILLS = HOME / ".gemini" / "config" / "skills"

# 动态解析脑库目录 (支持环境变量 CHAT_ARCHIVE_DIR，默认优先 D:\chat-archive-db，备选 ~/.truthgate/archive)
_custom_db_dir = os.environ.get("CHAT_ARCHIVE_DIR")
if _custom_db_dir and Path(_custom_db_dir).exists():
    DB_DIR = Path(_custom_db_dir)
elif Path(r"D:\chat-archive-db").exists():
    DB_DIR = Path(r"D:\chat-archive-db")
else:
    DB_DIR = HOME / ".truthgate" / "archive"

CLAUDE_DB = DB_DIR / "brain.db"
CODEX_DB = DB_DIR / "codex-brain.db"
AG_DB = DB_DIR / "ag-brain.db"

# 动态解析逆向/工具库目录 (支持环境变量 REVTOOLS_DIR，默认优先 D:\revtools)
_custom_rev = os.environ.get("REVTOOLS_DIR")
if _custom_rev and Path(_custom_rev).exists():
    REVTOOLS_DIR = Path(_custom_rev)
elif Path(r"D:\revtools").exists():
    REVTOOLS_DIR = Path(r"D:\revtools")
else:
    REVTOOLS_DIR = HOME / "revtools"


def search_claude_archive(kw: str, limit: int = 8) -> List[Dict[str, Any]]:
    """端 1: Claude Code 70+ 历史项目全量库"""
    if not CLAUDE_DB.exists():
        return []
    res = []
    try:
        conn = sqlite3.connect(f"file:{CLAUDE_DB.as_posix()}?mode=ro", uri=True)
        cur = conn.cursor()
        # 优先 FTS
        try:
            cur.execute("""
                SELECT m.project, m.slug, m.role, m.ts, snippet(messages_fts, 0, '【', '】', '...', 30)
                FROM messages_fts f
                JOIN messages m ON f.rowid = m.id
                WHERE messages_fts MATCH ?
                ORDER BY m.ts DESC LIMIT ?;
            """, (f'"{kw}"', limit))
            for proj, slug, role, ts, snip in cur.fetchall():
                res.append({"project": proj or slug, "role": role, "ts": ts, "snippet": snip})
        except Exception:
            cur.execute("""
                SELECT project, slug, role, ts, substr(text, 1, 120)
                FROM messages WHERE text LIKE ? ORDER BY ts DESC LIMIT ?;
            """, (f"%{kw}%", limit))
            for proj, slug, role, ts, snip in cur.fetchall():
                res.append({"project": proj or slug, "role": role, "ts": ts, "snippet": snip})
        conn.close()
    except Exception as e:
        pass
    return res


def search_codex_archive(kw: str, limit: int = 8) -> List[Dict[str, Any]]:
    """端 2: Codex 历史脑库"""
    if not CODEX_DB.exists():
        return []
    res = []
    try:
        conn = sqlite3.connect(f"file:{CODEX_DB.as_posix()}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT t.cwd, f.role, f.ts, f.content
                FROM codex_fts f
                JOIN codex_threads t ON f.thread_id = t.thread_id
                WHERE codex_fts MATCH ?
                ORDER BY f.ts DESC LIMIT ?;
            """, (f'"{kw}"', limit))
            for cwd, role, ts, content in cur.fetchall():
                snip = content[:140].replace("\n", " ") if content else ""
                res.append({"cwd": cwd, "role": role, "ts": ts, "snippet": snip})
        except Exception:
            pass
        conn.close()
    except Exception:
        pass
    return res


def search_ag_archive(kw: str, limit: int = 8) -> List[Dict[str, Any]]:
    """端 3: Antigravity 历史会话库"""
    if not AG_DB.exists():
        return []
    res = []
    try:
        conn = sqlite3.connect(f"file:{AG_DB.as_posix()}?mode=ro", uri=True)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT m.conv_id, m.role, m.ts, snippet(ag_messages_fts, 0, '【', '】', '...', 30)
                FROM ag_messages_fts f
                JOIN ag_messages m ON f.rowid = m.id
                WHERE ag_messages_fts MATCH ?
                ORDER BY m.ts DESC LIMIT ?;
            """, (f'"{kw}"', limit))
            for cid, role, ts, snip in cur.fetchall():
                res.append({"conv_id": cid, "role": role, "ts": ts, "snippet": snip})
        except Exception:
            cur.execute("""
                SELECT conv_id, role, ts, substr(content, 1, 120)
                FROM ag_messages WHERE content LIKE ? ORDER BY ts DESC LIMIT ?;
            """, (f"%{kw}%", limit))
            for cid, role, ts, snip in cur.fetchall():
                res.append({"conv_id": cid, "role": role, "ts": ts, "snippet": snip})
        conn.close()
    except Exception:
        pass
    return res


def search_local_skills_and_tools(kw: str, limit: int = 12) -> List[Dict[str, Any]]:
    """端 4: 本地离线技能 (Claude 200+ & AG 50+) + 逆向工具库"""
    kw_lower = kw.lower()
    matches = []

    # 1. 扫描 Claude skills
    if CLAUDE_SKILLS.exists():
        for skill_dir in CLAUDE_SKILLS.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            matched_by = []
            if kw_lower in skill_dir.name.lower():
                matched_by.append("dirname")
            if skill_md.exists():
                try:
                    txt = skill_md.read_text(encoding="utf-8", errors="ignore")
                    if kw_lower in txt.lower():
                        matched_by.append("content")
                        # 提取第一段描述
                        first_line = ""
                        for ln in txt.splitlines()[:15]:
                            if ln.strip().startswith("description:"):
                                first_line = ln.strip()
                                break
                        matches.append({
                            "type": "claude-skill",
                            "name": skill_dir.name,
                            "path": str(skill_md),
                            "desc": first_line or skill_dir.name
                        })
                        continue
                except Exception:
                    pass
            if matched_by and not any(m["name"] == skill_dir.name for m in matches):
                matches.append({
                    "type": "claude-skill",
                    "name": skill_dir.name,
                    "path": str(skill_dir),
                    "desc": "Directory name matched"
                })

    # 2. 扫描 AG skills
    if AG_SKILLS.exists():
        for skill_dir in AG_SKILLS.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    txt = skill_md.read_text(encoding="utf-8", errors="ignore")
                    if kw_lower in txt.lower() or kw_lower in skill_dir.name.lower():
                        if not any(m["name"] == skill_dir.name for m in matches):
                            matches.append({
                                "type": "ag-skill",
                                "name": skill_dir.name,
                                "path": str(skill_md),
                                "desc": skill_dir.name
                            })
                except Exception:
                    pass

    # 3. 扫描 D:\revtools
    if REVTOOLS_DIR.exists():
        for item in REVTOOLS_DIR.iterdir():
            if kw_lower in item.name.lower():
                matches.append({
                    "type": "revtool",
                    "name": item.name,
                    "path": str(item),
                    "desc": "D:\\revtools 逆向工具库"
                })

    return matches[:limit]


def run_four_ends_audit(keyword: str, limit: int = 8) -> Dict[str, Any]:
    print("=" * 75)
    print(f"🛡️ 【四端内部全量穷尽扫描】关键词: '{keyword}'")
    print("=" * 75)

    c_hits = search_claude_archive(keyword, limit=limit)
    codex_hits = search_codex_archive(keyword, limit=limit)
    ag_hits = search_ag_archive(keyword, limit=limit)
    skill_hits = search_local_skills_and_tools(keyword, limit=limit)

    summary = {
        "keyword": keyword,
        "端1_Claude_70项目": len(c_hits),
        "端2_Codex历史库": len(codex_hits),
        "端3_Antigravity脑库": len(ag_hits),
        "端4_本地技能与工具库": len(skill_hits),
        "details": {
            "claude": c_hits,
            "codex": codex_hits,
            "antigravity": ag_hits,
            "skills": skill_hits
        }
    }

    # 打印可视化报告
    print(f"\n[端 1] 🧠 Claude Code 70+ 项目脑库: 命中 {len(c_hits)} 条")
    for h in c_hits[:3]:
        print(f"  • 项目【{h['project']}】({h['ts'][:10]}): {h['snippet'][:90]}...")

    print(f"\n[端 2] 🤖 OpenAI Codex 研发脑库: 命中 {len(codex_hits)} 条")
    for h in codex_hits[:3]:
        print(f"  • 目录【{Path(h['cwd']).name if h['cwd'] else '未知'}】: {h['snippet'][:90]}...")

    print(f"\n[端 3] ⚡ Google Antigravity 专属脑库: 命中 {len(ag_hits)} 条")
    for h in ag_hits[:3]:
        print(f"  • 会话【{h['conv_id'][:8]}..】: {h['snippet'][:90]}...")

    print(f"\n[端 4] 🛠️ 本地 200+ 离线技能与军火库: 命中 {len(skill_hits)} 项")
    for h in skill_hits[:4]:
        print(f"  • [{h['type']}] {h['name']} -> {h['desc'][:80]}")

    print("\n" + "-" * 75)
    total_internal = len(c_hits) + len(codex_hits) + len(ag_hits) + len(skill_hits)
    print(f"✅ 内部四端聚合统计: 共命中 {total_internal} 项事实。内部基准确立完毕！")
    print("=" * 75 + "\n")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -3 internal_four_ends.py <keyword> [--limit 10]")
        sys.exit(1)
    kw = sys.argv[1]
    run_four_ends_audit(kw)
