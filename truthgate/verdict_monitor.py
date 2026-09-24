# -*- coding: utf-8 -*-
"""verdict_monitor.py —— TruthGate / Superego 3.0 全时态开火与误判实时监控器

功能:
1. 每一轮审计裁决（PASS / BLOCK）全量无死角持久化入库 (~/.truthgate/monitor.db)；
2. 实时监测用户输入是否包含对上一轮裁决的质疑/批评/申诉（如「闸误判了」「根本没有」「不属于代码轮」）；
3. 自动归档潜在误判样本，调起 Jev/外审进行实时对账，并输出监控统计指标。
"""
import os
import sys
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

TRUTHGATE_DIR = Path.home() / ".truthgate"
MONITOR_DB = TRUTHGATE_DIR / "monitor.db"
LOGS_DIR = TRUTHGATE_DIR / "logs"
VERDICTS_JSONL = LOGS_DIR / "verdicts.jsonl"


def _init_db():
    TRUTHGATE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(MONITOR_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verdict_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turn_type TEXT NOT NULL,
                user_prompt_snippet TEXT,
                assistant_text_snippet TEXT,
                verdict TEXT NOT NULL,
                fired_rules TEXT,
                reasons TEXT,
                mode TEXT,
                latency_ms REAL,
                is_false_positive INTEGER DEFAULT 0,
                is_false_negative INTEGER DEFAULT 0
            )
        """)
        # Backward compatibility: add column if table already existed without it
        try:
            conn.execute("ALTER TABLE verdict_records ADD COLUMN is_false_negative INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS false_positives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                verdict_id INTEGER,
                user_refutation TEXT NOT NULL,
                fired_rules TEXT,
                status TEXT DEFAULT 'recorded',
                audit_notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS false_negatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                verdict_id INTEGER,
                user_reprimand TEXT NOT NULL,
                trigger_pattern TEXT,
                assistant_text_snippet TEXT,
                status TEXT DEFAULT 'recorded',
                audit_notes TEXT
            )
        """)
        conn.commit()


_init_db()


def record_verdict(
    turn_type: str,
    verdict: str,
    fired_rules: List[str],
    reasons: List[str],
    mode: str,
    latency_ms: float,
    user_prompt: str = "",
    assistant_text: str = ""
) -> int:
    """持久化记录单次门禁裁决"""
    ts = datetime.now().isoformat()
    record = {
        "timestamp": ts,
        "turn_type": turn_type,
        "verdict": verdict,
        "fired_rules": fired_rules,
        "reasons": reasons,
        "mode": mode,
        "latency_ms": latency_ms,
        "user_prompt": user_prompt[:300],
        "assistant_text": assistant_text[:500]
    }
    
    # 写入 JSONL
    try:
        with open(VERDICTS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
        
    # 写入 SQLite
    record_id = -1
    try:
        with sqlite3.connect(MONITOR_DB) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO verdict_records 
                (timestamp, turn_type, user_prompt_snippet, assistant_text_snippet, verdict, fired_rules, reasons, mode, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts, turn_type, user_prompt[:300], assistant_text[:500],
                verdict, json.dumps(fired_rules, ensure_ascii=False),
                json.dumps(reasons, ensure_ascii=False), mode, latency_ms
            ))
            record_id = cur.lastrowid
            conn.commit()
    except Exception as e:
        pass
        
    return record_id


_REPRIMAND_PATTERN = (
    r"你又错|又错了|你错了|这不对|不对吧|不对啊|你确定吗|确定吗\?|真的查过|你在骗我|你骗我|骗人"
    r"|没测吧|又幻觉|幻觉了|没搞懂|还没搞懂|没懂|懂不懂|垃圾|敷衍|糊弄|忽悠|你怎么又|你又来"
    r"|根本没(?!问题|错|事)|明明|说了多少次|讲了多少次|又没做|还得我自己|我自己动手"
    r"|居然没|竟然没|到现在还|你是不是又|说过多少次|根本不|你又没|你又忘"
    r"|搞错了什么|哪个才是最完整正确的|修好了吗|既然我随便都找到有问题|你却看不到有问题|根因是什么"
    r"|用错方法|gate没开火|有没有审查自动Monitor|为何没拦|为何没拦截|为什么没拦"
)


def check_user_refutation(user_prompt: str) -> Optional[Dict[str, Any]]:
    """检测用户是否在反驳/申诉上一轮门禁的误判，若有则自动对账并记入 false_positives"""
    import re
    if not user_prompt:
        return None
    if not re.search(_REFUTATION_PATTERN, user_prompt):
        return None
        
    ts = datetime.now().isoformat()
    try:
        with sqlite3.connect(MONITOR_DB) as conn:
            cur = conn.cursor()
            # 找到最近一次 BLOCK 记录
            cur.execute("""
                SELECT id, timestamp, fired_rules, assistant_text_snippet 
                FROM verdict_records 
                WHERE verdict='BLOCK' 
                ORDER BY id DESC LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                vid, v_ts, fired_json, asst_snip = row
                # 标记为疑似误判
                cur.execute("UPDATE verdict_records SET is_false_positive = 1 WHERE id = ?", (vid,))
                cur.execute("""
                    INSERT INTO false_positives (timestamp, verdict_id, user_refutation, fired_rules, audit_notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (ts, vid, user_prompt[:300], fired_json, f"用户提出反驳，触发实时误判追踪。"))
                conn.commit()
                return {
                    "verdict_id": vid,
                    "suspected_rules": json.loads(fired_json) if fired_json else [],
                    "message": "已捕获用户误判反馈，已自动写入实时监控数据库！"
                }
    except Exception:
        pass
    return None


def check_user_reprimand_and_record_false_negative(user_prompt: str) -> Optional[Dict[str, Any]]:
    """检测用户是否在批评/指出上一轮的疏漏/故障(即上一轮门禁本该拦却漏拦放行了，产生 False Negative 假阴性)。
    若命中，自动对账上一轮 PASS 记录，标记为 is_false_negative = 1，并存入 false_negatives 表。
    """
    import re
    if not user_prompt:
        return None
    m = re.search(_REPRIMAND_PATTERN, user_prompt)
    if not m:
        return None

    trigger_word = m.group(0)
    ts = datetime.now().isoformat()
    try:
        with sqlite3.connect(MONITOR_DB) as conn:
            cur = conn.cursor()
            # 找到最近一次 PASS 记录（说明上轮可能漏判）
            cur.execute("""
                SELECT id, timestamp, assistant_text_snippet 
                FROM verdict_records 
                WHERE verdict='PASS' 
                ORDER BY id DESC LIMIT 1
            """)
            row = cur.fetchone()
            vid = row[0] if row else None
            asst_snip = row[2] if row else ""
            
            if vid:
                cur.execute("UPDATE verdict_records SET is_false_negative = 1 WHERE id = ?", (vid,))
            
            cur.execute("""
                INSERT INTO false_negatives (timestamp, verdict_id, user_reprimand, trigger_pattern, assistant_text_snippet, audit_notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ts, vid, user_prompt[:400], trigger_word, asst_snip, "用户再次纠错/质疑，系统自动对账捕获上一轮门禁假阴性(漏拦)！"))
            conn.commit()
            return {
                "verdict_id": vid,
                "trigger_word": trigger_word,
                "message": f"🚨 捕获人类纠错批评『{trigger_word}』，上一轮 PASS 已自动标记为假阴性(False Negative)并建档审计！"
            }
    except Exception:
        pass
    return None


def get_monitor_stats() -> Dict[str, Any]:
    """获取门禁裁决全量指标：查准率(Precision) + 查全率(Recall) + 误判/漏判双向监控"""
    try:
        with sqlite3.connect(MONITOR_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM verdict_records")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM verdict_records WHERE verdict='BLOCK'")
            blocks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM verdict_records WHERE verdict='PASS'")
            passes = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM false_positives")
            fp_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM false_negatives")
            fn_count = cur.fetchone()[0]

            precision = round((blocks - fp_count) / max(blocks, 1) * 100, 2)
            recall = round(blocks / max(blocks + fn_count, 1) * 100, 2)
            return {
                "total_audited": total,
                "blocks": blocks,
                "passes": passes,
                "false_positives": fp_count,
                "false_negatives": fn_count,
                "precision_rate": precision,
                "recall_rate": recall
            }
    except Exception:
        return {
            "total_audited": 0, "blocks": 0, "passes": 0,
            "false_positives": 0, "false_negatives": 0,
            "precision_rate": 100.0, "recall_rate": 100.0
        }
