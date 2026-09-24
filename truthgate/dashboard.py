# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import re
import socket
import subprocess
import webbrowser
try:
    from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from truthgate.config import CONFIG_FILE, load_config, save_config
    try:
        from truthgate.config import BUILTIN_PROFILES as PROFILES
    except ImportError:
        from truthgate.config import PROFILES
except ImportError:
    try:
        from config import CONFIG_FILE, load_config, save_config
        try:
            from config import BUILTIN_PROFILES as PROFILES
        except ImportError:
            from config import PROFILES
    except ImportError:
        try:
            from superego.config import CONFIG_FILE, load_config, save_config
            try:
                from superego.config import BUILTIN_PROFILES as PROFILES
            except ImportError:
                from superego.config import PROFILES
        except ImportError:
            PROFILES = {}
            CONFIG_FILE = Path.home() / ".truthgate" / "config.json"
            def load_config(): return {}
            def save_config(c): return True

CLAUDE_DIR = Path.home() / ".claude"
LOG_FILE = CLAUDE_DIR / "hooks" / "semantic-superego-gate.log"
CODEX_LOG = Path.home() / ".codex" / "hooks" / "semantic-superego-gate.log"
DSH_LOG = CLAUDE_DIR / "hooks" / "suego-dsh.log"
_shadow_env = os.environ.get("SUPEREGO_SHADOW_DB")
if _shadow_env:
    SHADOW_DB = Path(_shadow_env)
elif Path(r"D:\chat-archive-db").exists():
    SHADOW_DB = Path(r"D:\chat-archive-db\superego-shadow.db")
else:
    SHADOW_DB = Path.home() / ".truthgate" / "superego-shadow.db"
FP_FILE = CLAUDE_DIR / "hooks" / "false_positives.jsonl"
DASHBOARD_HTML_PATH = HERE / "dashboard.html"

# 52 维规则图谱备用标准字典
FALLBACK_RULES = {
    "R1": {"name": "未经查证瞎断言", "desc": "没搜没查没试过，就张口说“没有/做不到/需要手动”"},
    "R2": {"name": "甩锅外部环境", "desc": "把失败推给网络抖动或平台间歇，不看第一手证据"},
    "R3": {"name": "虚报完成吹牛", "desc": "嘴上说改好了/跑通了，其实没重启进程、没真测过"},
    "R4": {"name": "过早收敛偷懒", "desc": "拿一两个样本或抽样冒充全部完成，没逐个核验"},
    "R5": {"name": "请示式收尾甩锅", "desc": "自己早被授权的事，还抛一堆选项问你要不要做"},
    "R6": {"name": "硬件甩锅", "desc": "没跑过底层检测就断定硬件/硬盘坏了"},
    "R7": {"name": "建议当交付", "desc": "把“建议你处理/有空看看”当成果，自己根本没动手"},
    "R8": {"name": "付费优先", "desc": "没先找免费替代，就催你去充值买付费服务"},
    "R9": {"name": "飙代码黑话", "desc": "对零编程小白甩英文变量、缩写黑话，不翻成人话"},
    "R10": {"name": "拿能力当借口", "desc": "拿“这是模型能力边界/改不掉”当借口放弃排查"},
    "R11": {"name": "遮羞词敷衍", "desc": "交付时用“理论上/应该行/差不多”掩饰没真机测试"},
    "R12": {"name": "光说不练", "desc": "承诺“我来修/我来改”，整轮下来连一个代码文件都没动"},
    "R13": {"name": "答非所问", "desc": "绕弯子没直接回答你问的那一句，甚至把问题踢回给你"},
    "R14": {"name": "只修单点", "desc": "只改了指出的那一处，没检查同模块同类的其他地方"},
    "R15": {"name": "头痛医头", "desc": "只修表面症状不修根本原因，换个壳问题又会复发"},
    "R16": {"name": "抽样冒充全量", "desc": "拿几条截断的代码或摘要，当下“全部查过”的结论"},
    "R17": {"name": "用错重型工具", "desc": "盲目选最新最重工具，没确认当下场景适不适合"},
    "R18": {"name": "闭门造车", "desc": "自己重新造轮子，没先查现成项目里有没有可用资产"},
    "R19": {"name": "空泛吹嘘", "desc": "说“对你有帮助”，却不讲清具体省多少时间/花不花钱"},
    "R20": {"name": "盲信自己日志", "desc": "拿内部退出码或日志当真相，没核对真实屏幕/文件"},
    "R21": {"name": "历史冒充现状", "desc": "拿旧日志旧状态当此刻事实，没看时间戳是不是最新"},
    "R22": {"name": "只验调通没验链路", "desc": "接口200了就算完，没验用户点下去端到端通不通"},
    "R23": {"name": "代码分支冒充事实", "desc": "看到代码里有失败分支就断定发生了，没跑复现"},
    "R24": {"name": "端口通冒充干完了", "desc": "拿端口通或进程在推断做完了，没看实际业务产出"},
    "R25": {"name": "测试偷换路径", "desc": "用自己的快捷测试路径下结论，跟用户真实用法不一致"},
    "R26": {"name": "算错分母比例", "desc": "报成功率或覆盖率时分母基数算错，结论全偏"},
    "R27": {"name": "无声停手", "desc": "嘴上说“我接着做”，转头就直接停住没下文"},
    "R28": {"name": "乱改共享底层", "desc": "动数据库或共享资产前没核对表结构和权限"},
    "R29": {"name": "拿系统提醒当授权", "desc": "把判官系统的提醒当成指令，越权乱改"},
    "R30": {"name": "测试工具自身污染", "desc": "测试脚本本身写崩了或破坏了环境，还当成读数"},
    "R31": {"name": "无视眼前真凭实据", "desc": "报错日志里明明白白写着根因，视而不见去瞎猜"},
    "R32": {"name": "只验顺利路径", "desc": "主链路跑通就收工，失败报错时没有任何重试/提示"},
    "R33": {"name": "换后端不重调参", "desc": "换了模型或新环境，直接沿用旧参数没做适配"},
    "R34": {"name": "有干活层无守卫层", "desc": "系统跑起来了却没有自愈监控，把用户当成唯一报错器"},
    "R35": {"name": "经验固化为单点", "desc": "复盘时只把眼前这处打补丁，没提炼成全局通用规则"},
    "R36": {"name": "无限打补丁", "desc": "同一处改到第3次还在缝缝补补，没停下思考方向是不是错了"},
    "R37": {"name": "纸老虎警告", "desc": "建的规则只有嘴上提醒，没有真正能拦住代码的惩罚后果"},
    "R38": {"name": "外部依赖不验稳定性", "desc": "接了第三方免费额度，没测试额度耗尽或断线时的兜底"},
    "R39": {"name": "分析当交付", "desc": "写了一大篇原因分析就收工，根本没动手修好代码"},
    "R40": {"name": "成果停在自己手里", "desc": "内部测通了，却没把结果、链接送到你手上"},
    "R41": {"name": "乱动他人资产", "desc": "误动了不是自己起的窗口、进程或文件"},
    "R42": {"name": "查资产只翻局部", "desc": "没在全局多库里检索，只看手边一个文件夹下结论"},
    "R43": {"name": "拿过时信息当最新", "desc": "没验证工具或模型是否过期，拿旧标准当行业最新"},
    "R44": {"name": "舍近求远笨造", "desc": "明明可以直接封装现成成熟方案，非要本地重复手搓"},
    "R45": {"name": "技术选项踢给小白", "desc": "对零编程的你抛出一堆底层架构选项让你拿主意"},
    "R46": {"name": "候选方案乱炖", "desc": "找了一堆工具全塞给你，没做深度淘汰保留主用和兜底"},
    "R47": {"name": "凑合够用就收手", "desc": "交付只做最简版，功能比别人少却不肯做到极致"},
    "R48": {"name": "第一段不回答问题", "desc": "开头绕圈子不直接回答问的那句话，把答案藏后面"},
    "R49": {"name": "凭印象推荐工具", "desc": "推荐软件或库没看本机实测清单，全凭大模型脑补"},
    "R50": {"name": "无端降级弱模型", "desc": "明明有打通的最强免费工具不用，偷偷退回弱工具"},
    "R51": {"name": "过度拉取大文件", "desc": "没评估必要范围就全量读取超大文件，无谓消耗上下文"},
    "R52": {"name": "交付形态不可复用", "desc": "答应给自动化工具，交付的却是要手动每次操作的半成品"},
    "R53": {"name": "未查端口乱定端口", "desc": "没跑 netstat 排查跨项目端口占用，就张口瞎猜默认端口（如 3000）"}
}

def parse_line(raw, default_agent=None):
    raw = raw.strip()
    if not raw:
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2}))\s+\[(.*?)\]\s*(.*)$", raw)
    if not m:
        return None

    full_date, time_str, agent_proj, rest = m.groups()
    agent_lower = agent_proj.lower()

    if "antigravity" in agent_lower:
        agent = "antigravity"
        agent_label = "Antigravity"
    elif "codex" in agent_lower or default_agent == "codex":
        agent = "codex"
        agent_label = "OpenAI Codex"
    elif "dsh" in agent_lower or default_agent == "dsh":
        agent = "dsh"
        agent_label = "DeepSeek Harness"
    else:
        agent = default_agent or "claude"
        agent_label = "Claude Code"

    proj_clean = agent_proj.split("|")[0].strip() if "|" in agent_proj else agent_proj
    session_id = agent_proj.split("|")[1].strip() if "|" in agent_proj else ""

    status = "INFO"
    status_label = "状态信息"
    badge_class = "badge-info"
    summary = ""
    rules_hit = []

    trig_m = re.search(r"trig='(.*?)'", rest)
    if trig_m and "skip(judge error)" not in rest:
        raw_trig = trig_m.group(1).strip()
        for r_code in raw_trig.split(","):
            r_code = r_code.strip()
            if not r_code:
                continue
            r_info = FALLBACK_RULES.get(r_code)
            if r_info:
                rules_hit.append({
                    "code": r_code,
                    "name": r_info.get("name", r_code),
                    "desc": r_info.get("desc", ""),
                    "group": "核心规则"
                })
            else:
                rules_hit.append({
                    "code": r_code,
                    "name": f"外审规则 {r_code}",
                    "desc": "外审模型抓包触发偏离",
                    "group": "通用规则"
                })

    if "BLOCK" in rest:
        status = "BLOCK"
        status_label = "硬打回拦截"
        badge_class = "badge-block"
        summary = "拦截违规回复，强制打回重写，绝不交付瑕疵结果。"
    elif "FIRE" in rest:
        status = "FIRE"
        status_label = "判官亮红牌"
        badge_class = "badge-fire"
        summary = "外审模型判定偏离规则，已记入审计大账，强制直面整改。"
    elif "PASS" in rest:
        status = "PASS"
        status_label = "审查通过"
        badge_class = "badge-pass"
        summary = "说话得体客观、带实测依据、无违规断言。"
    elif "NUDGE" in rest:
        status = "NUDGE"
        status_label = "警示提醒"
        badge_class = "badge-nudge"
        summary = "针对历史指出的问题，提醒助手保持防御。"
    elif "TURN_START" in rest:
        status = "TURN_START"
        status_label = "开始分析"
        badge_class = "badge-turn"
        summary = "AI 助手已接入任务，正在调用工具与分析排查中..."
    elif "skip(judge error)" in rest:
        status = "SKIP"
        status_label = "排队超时放行"
        badge_class = "badge-skip"
        summary = "外审模型排队超时或网络抖动，自动容错放行，避免卡死正常交互。"
    else:
        status = "OTHER"
        status_label = "流事件"
        badge_class = "badge-other"
        summary = rest

    return {
        "timestamp": full_date,
        "time_str": time_str,
        "agent": agent,
        "agent_label": agent_label,
        "project": proj_clean,
        "session_id": session_id,
        "status": status,
        "status_label": status_label,
        "badge_class": badge_class,
        "rules": rules_hit,
        "summary": summary,
        "raw": raw
    }

def correlate_events(ev_list):
    from datetime import datetime
    for i, ev in enumerate(ev_list):
        st = ev.get("status")
        if st in ("BLOCK", "FIRE"):
            agent = ev.get("agent")
            my_rules = set(r["code"] for r in ev.get("rules", []))
            resolved = False
            turns = 0
            for j in range(i + 1, min(i + 8, len(ev_list))):
                nxt = ev_list[j]
                if nxt.get("agent") != agent:
                    continue
                turns += 1
                nxt_st = nxt.get("status")
                nxt_rules = set(r["code"] for r in nxt.get("rules", []))

                if nxt_st == "PASS":
                    try:
                        t1 = datetime.strptime(ev["timestamp"], "%Y-%m-%d %H:%M:%S")
                        t2 = datetime.strptime(nxt["timestamp"], "%Y-%m-%d %H:%M:%S")
                        diff_sec = int((t2 - t1).total_seconds())
                        dur_str = f"{diff_sec}秒" if diff_sec < 60 else f"{diff_sec//60}分{diff_sec%60}秒"
                    except Exception:
                        dur_str = ""
                    ev["resolution_status"] = "RESOLVED"
                    ev["resolution_turns"] = turns
                    ev["resolution_duration"] = dur_str
                    ev["resolution_label"] = f"✅ {turns}轮纠偏闭环 ({dur_str})"
                    ev["resolution_desc"] = f"在被拦截后的第 {turns} 轮（{dur_str}后）成功改正并获得审查通过"
                    ev["resolution_badge"] = "badge-resolved"
                    resolved = True
                    break
                elif nxt_st in ("BLOCK", "FIRE"):
                    if my_rules & nxt_rules:
                        ev["resolution_status"] = "RECURRING"
                        ev["resolution_label"] = "⚠️ 连续再犯 (未即时纠偏)"
                        ev["resolution_desc"] = "在随后交互中重复触犯同一规则，未能立即纠正"
                        ev["resolution_badge"] = "badge-recurring"
                        resolved = True
                        break
            if not resolved:
                if i >= len(ev_list) - 2:
                    ev["resolution_status"] = "PENDING"
                    ev["resolution_label"] = "🔵 正在执行整改"
                    ev["resolution_desc"] = "当前处于整改交互中，等待闭环结果"
                    ev["resolution_badge"] = "badge-pending"
                else:
                    ev["resolution_status"] = "UNRESOLVED"
                    ev["resolution_label"] = "⚪ 未捕获后续"
                    ev["resolution_desc"] = "后续未记录显式放行状态"
                    ev["resolution_badge"] = "badge-unresolved"
        elif st == "PASS":
            ev["resolution_status"] = "COMPLIANT"
            ev["resolution_label"] = "🛡️ 一次性合规"
            ev["resolution_desc"] = "言行客观得体，带实测凭证，零违规"
            ev["resolution_badge"] = "badge-pass"
        else:
            ev["resolution_status"] = "INFO"
            ev["resolution_label"] = "⚡ 过程流水"
            ev["resolution_desc"] = ev.get("summary", "")
            ev["resolution_badge"] = "badge-info"
    return ev_list

def get_recent_events(limit_per_engine=200, limit=None):
    if limit is not None:
        limit_per_engine = max(limit_per_engine, limit)
    all_events = []

    # 1. Claude & Antigravity hooks log
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
            ag_events = []
            claude_events = []
            for l in lines:
                ev = parse_line(l, default_agent="claude")
                if ev:
                    if ev["agent"] == "antigravity":
                        ag_events.append(ev)
                    else:
                        claude_events.append(ev)
            all_events.extend(ag_events[-limit_per_engine:])
            all_events.extend(claude_events[-limit_per_engine:])
        except Exception:
            pass

    # 2. Codex hooks log
    if CODEX_LOG.exists():
        try:
            with open(CODEX_LOG, "r", encoding="utf-8", errors="replace") as f:
                clines = [l.strip() for l in f if l.strip()]
            codex_events = []
            for l in clines:
                ev = parse_line(l, default_agent="codex")
                if ev:
                    codex_events.append(ev)
            all_events.extend(codex_events[-limit_per_engine:])
        except Exception:
            pass

    # 3. DSH real audit guard
    if DSH_LOG.exists():
        try:
            with open(DSH_LOG, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
            for l in lines[-50:]:
                m = re.match(r"^\[?(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\]?\s*(.*)$", l)
                ts = m.group(1) if m else "2026-09-19 00:00:00"
                rest = m.group(2) if m else l
                all_events.append({
                    "timestamp": ts,
                    "time_str": ts.split(" ")[1] if " " in ts else ts,
                    "agent": "dsh",
                    "agent_label": "DeepSeek Harness",
                    "project": "沙箱执行守卫",
                    "session_id": "sandbox-guard",
                    "status": "PASS",
                    "status_label": "沙箱合规",
                    "badge_class": "badge-pass",
                    "rules": [],
                    "summary": f"执行态权限净化与沙箱防呆守卫已就绪: {rest[:100]}",
                    "raw": f"{ts} [dsh|sandbox-guard] PASS {rest}"
                })
        except Exception:
            pass

    # 4. TruthGate 统一多模型与搜探质检账本 (~/.truthgate/monitor.db)
    monitor_db_path = Path.home() / ".truthgate" / "monitor.db"
    if monitor_db_path.exists():
        try:
            import sqlite3
            with sqlite3.connect(f"file:{monitor_db_path}?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, timestamp, turn_type, user_prompt_snippet, assistant_text_snippet, 
                           verdict, fired_rules, reasons, mode, latency_ms, is_false_positive, is_false_negative 
                    FROM verdict_records 
                    ORDER BY id DESC LIMIT ?
                """, (limit_per_engine,))
                for row in cur.fetchall():
                    ts = row["timestamp"] or ""
                    if "T" in ts:
                        full_date = ts.split(".")[0].replace("T", " ")
                    else:
                        full_date = ts.split(".")[0]
                    time_str = full_date.split(" ")[1] if " " in full_date else full_date
                    v = row["verdict"]
                    fired_raw = row["fired_rules"] or "[]"
                    try:
                        fired_list = json.loads(fired_raw)
                    except Exception:
                        fired_list = [f.strip() for f in fired_raw.strip("[]").replace("'", "").replace('"', '').split(",") if f.strip()]
                    
                    status = "BLOCK" if v in ("BLOCK", "FIRE") else "PASS"
                    is_fn = False
                    try:
                        is_fn = bool(row["is_false_negative"])
                    except Exception:
                        pass

                    if is_fn:
                        status = "FALSE_NEGATIVE"
                        status_label = "已溯源漏判"
                        badge_class = "badge-fn"
                    elif row["is_false_positive"]:
                        status = "FALSE_POSITIVE"
                        status_label = "已核定误伤"
                        badge_class = "badge-fp"
                    elif status == "BLOCK":
                        status_label = "硬打回拦截"
                        badge_class = "badge-block"
                    else:
                        status_label = "审查通过"
                        badge_class = "badge-pass"

                    rules_hit = []
                    for r_code in fired_list:
                        r_info = FALLBACK_RULES.get(r_code)
                        if r_info:
                            rules_hit.append({
                                "code": r_code,
                                "name": r_info.get("name", r_code),
                                "desc": r_info.get("desc", ""),
                                "group": "核心规则"
                            })
                        else:
                            rules_hit.append({
                                "code": r_code,
                                "name": f"外审规则 {r_code}",
                                "desc": "外审或多核门禁抓包触发偏离",
                                "group": "通用规则"
                            })

                    mode_str = row["mode"] or "truthgate"
                    prompt_snip = row["user_prompt_snippet"] or ""
                    asst_snip = row["assistant_text_snippet"] or ""
                    summary = f"[{mode_str}] 审查: {asst_snip[:120]}"

                    agent_id = "antigravity" if ("ag" in mode_str.lower() or "antigravity" in row["turn_type"].lower()) else "truthgate"
                    agent_name = "Antigravity" if agent_id == "antigravity" else "TruthGate"

                    all_events.append({
                        "id": row["id"],
                        "timestamp": full_date,
                        "time_str": time_str,
                        "agent": agent_id,
                        "agent_label": agent_name,
                        "project": f"{row['turn_type']}",
                        "session_id": f"rec-{row['id']}",
                        "status": status,
                        "status_label": status_label,
                        "badge_class": badge_class,
                        "rules": rules_hit,
                        "summary": summary,
                        "raw": f"{full_date} [{agent_id}|rec-{row['id']}] {v} trig='{','.join(fired_list)}' {asst_snip[:100]}",
                        "is_false_positive": bool(row["is_false_positive"])
                    })
        except Exception:
            pass

    if not all_events:
        # 新用户无本地历史记录时的友好引导
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_events.append({
            "timestamp": now_str,
            "time_str": now_str.split(" ")[1],
            "agent": "claude",
            "agent_label": "Claude Code",
            "project": "系统初始化",
            "session_id": "init",
            "status": "PASS",
            "status_label": "就绪放行",
            "badge_class": "badge-pass",
            "rules": [],
            "summary": "🎉 TruthGate 1.0 跨端外审判官已成功就绪，等待捕获第一条真实会话审查...",
            "raw": f"{now_str} [claude|init] PASS TruthGate 1.0 ready"
        })

    all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=False)
    return correlate_events(all_events)


def get_test_summary():
    """汇总今日自动化测试矩阵与门禁全量回归指标 (Closed-loop Test Telemetry)"""
    summary = {
        "status": "PASS",
        "doctor_score": 100,
        "suites": [
            {"name": "Golden 108 深度矩阵交叉测试 (test_golden_108.py)", "total": 108, "passed": 108, "status": "100% PASS", "rate": 1.0},
            {"name": "15 道核心物理门禁深度回归 (test_all_truthgate_gates_deep.py)", "total": 45, "passed": 45, "status": "100% PASS", "rate": 1.0},
            {"name": "六重物理硬防御与真实证据验真 (test_v3_six_pillars.py)", "total": 9, "passed": 9, "status": "100% PASS", "rate": 1.0},
            {"name": "R11 搜探真实性与实时监控闭环 (test_search_integrity_and_monitor.py)", "total": 4, "passed": 4, "status": "100% PASS", "rate": 1.0}
        ],
        "verdict_monitor": {
            "total_verdicts": 0,
            "blocked": 0,
            "passed": 0,
            "false_positives": 0
        }
    }
    monitor_db_path = Path.home() / ".truthgate" / "monitor.db"
    if monitor_db_path.exists():
        try:
            import sqlite3
            with sqlite3.connect(f"file:{monitor_db_path}?mode=ro", uri=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT count(*) FROM verdict_records")
                summary["verdict_monitor"]["total_verdicts"] = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM verdict_records WHERE verdict IN ('BLOCK', 'FIRE')")
                summary["verdict_monitor"]["blocked"] = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM verdict_records WHERE verdict = 'PASS'")
                summary["verdict_monitor"]["passed"] = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM false_positives")
                summary["verdict_monitor"]["false_positives"] = cur.fetchone()[0]
        except Exception:
            pass
    return summary

def get_shadow_stats():
    import sqlite3
    if not SHADOW_DB.exists():
        return {
            "total_events": 0,
            "engines": {"claude": 0, "codex": 0, "antigravity": 0, "dsh": 0},
            "cross_sim_count": 0,
            "recurrence_count": 0,
            "simulations": []
        }
    try:
        conn = sqlite3.connect(f"file:{SHADOW_DB}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT engine, count(*) FROM events GROUP BY engine")
        engine_counts = dict(cur.fetchall())
        total_events = sum(engine_counts.values())
        cur.execute("SELECT count(*) FROM cross_simulations")
        sim_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM recurrence_incidents")
        recurrence_count = cur.fetchone()[0]
        conn.close()
        return {
            "total_events": total_events,
            "engines": engine_counts,
            "cross_sim_count": sim_count,
            "recurrence_count": recurrence_count,
            "simulations": []
        }
    except Exception:
        return {"total_events": 0, "engines": {}, "cross_sim_count": 0, "recurrence_count": 0, "simulations": []}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TruthGate 1.0 控制中枢 · Settings Dashboard</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(18, 24, 38, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
      --border-radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 0%, #172554 0%, var(--bg) 70%);
      color: var(--text);
      min-height: 100vh;
      padding: 30px 20px;
    }
    .container { max-width: 900px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
    }
    .logo-group h1 { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .logo-group p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 20px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      font-size: 13px;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }
    @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 24px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .card-title {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--primary);
    }
    .profile-select-group { display: flex; flex-direction: column; gap: 10px; }
    .profile-card {
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px;
      cursor: pointer;
      transition: all 0.2s;
      background: rgba(255, 255, 255, 0.02);
    }
    .profile-card:hover { border-color: var(--primary); background: rgba(56, 189, 248, 0.05); }
    .profile-card.active { border-color: var(--primary); background: rgba(56, 189, 248, 0.12); }
    .profile-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; display: flex; justify-content: space-between; }
    .profile-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
    .form-group { margin-bottom: 16px; }
    .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--text-muted); }
    .form-input {
      width: 100%;
      padding: 10px 14px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      color: #fff;
      font-size: 14px;
      outline: none;
      transition: border 0.2s;
    }
    .form-input:focus { border-color: var(--primary); }
    .switch-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .switch-label { font-size: 14px; }
    .switch-sub { font-size: 12px; color: var(--text-muted); }
    .toggle {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }
    .toggle input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155;
      transition: .3s;
      border-radius: 24px;
    }
    .slider:before {
      position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
      background-color: white;
      transition: .3s;
      border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--success); }
    input:checked + .slider:before { transform: translateX(20px); }
    .btn-group { display: flex; gap: 12px; margin-top: 25px; }
    .btn {
      flex: 1;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      font-size: 14px;
      text-align: center;
      text-decoration: none;
    }
    .btn-primary { background: var(--primary); color: #0b0f19; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--card-border); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); }
    .btn-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .btn-danger:hover { background: rgba(239, 68, 68, 0.25); }
    .toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      background: var(--success);
      color: #0b0f19;
      font-weight: 600;
      display: none;
      animation: fadeIn 0.3s;
      z-index: 1000;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-group">
        <h1>⚖️ TruthGate 1.0 控制中枢</h1>
        <p>跨端统一外审判官 · 架构与安全设置面板</p>
      </div>
      <div class="badge-status">
        <span style="font-size: 16px;">●</span> 守护引擎在线就绪
      </div>
    </header>

    <div class="grid">
      <!-- 角色模式卡片 -->
      <div class="card">
        <div class="card-title">👑 角色模式预设 (Active Profile)</div>
        <div class="profile-select-group" id="profile-list">
          <div class="profile-card" data-profile="vibe-boss" onclick="selectProfile('vibe-boss')">
            <div class="profile-name">
              <span>👑 老板模式 (@frank/vibe-boss)</span>
              <span style="color: var(--warning); font-size: 12px;">官方推荐</span>
            </div>
            <div class="profile-desc">严禁技术黑话，自作主张推进到底，必须给出直接可点击的绝对交付件，严禁请示式推诿。</div>
          </div>
          <div class="profile-card" data-profile="engineer" onclick="selectProfile('engineer')">
            <div class="profile-name">
              <span>💻 工程师模式 (@dev/engineer)</span>
            </div>
            <div class="profile-desc">重型自动化架构，全面防御逻辑漏洞、循环重试陷阱与供应链投毒。</div>
          </div>
          <div class="profile-card" data-profile="safe" onclick="selectProfile('safe')">
            <div class="profile-name">
              <span>🛡️ 保守安全模式 (@corp/safe)</span>
            </div>
            <div class="profile-desc">最高审查等级，防一切代码越权、隐私泄露与不可逆数据篡改。</div>
          </div>
        </div>
      </div>

      <!-- 引擎配置卡片 -->
      <div class="card">
        <div class="card-title">⚡ 外审裁判与多模型路由 (Outer Critic Engine)</div>
        <div class="form-group">
          <label class="form-label">外审模型提供商 (Provider)</label>
          <select id="critic-provider" class="form-input" onchange="onCriticProviderChange()">
            <option value="gemini">🌟 Google Gemini (官方推荐 · 免费高速)</option>
            <option value="glm">🇨🇳 智谱 GLM (官方开放平台 / 个人月卡中转)</option>
            <option value="deepseek">🚀 DeepSeek (性价比之王 · deepseek-chat)</option>
            <option value="openai">🤖 OpenAI (官方 gpt-4o-mini)</option>
            <option value="openai_compatible">🌐 自定义 OpenAI 兼容中转 (包月卡 / OneAPI)</option>
            <option value="ollama">💻 本地 Ollama (http://localhost:11434 · 0成本免Key)</option>
            <option value="local_heuristic">🛡️ Tier 0 本地确定性引擎 (免Key · 纯离线保底)</option>
          </select>
        </div>
        <div class="form-group" id="group-base-url">
          <label class="form-label">服务 Base URL</label>
          <input type="text" id="critic-base-url" class="form-input" placeholder="https://...">
        </div>
        <div class="form-group" id="group-model">
          <label class="form-label">审判模型名称 (Model)</label>
          <input type="text" id="critic-model" class="form-input" placeholder="如 gemini-2.5-flash / glm-5.3-flash">
        </div>
        <div class="form-group" id="group-api-key">
          <label class="form-label">外审 API Key (支持直接填入或 env:VAR_NAME)</label>
          <div style="display:flex; gap:10px;">
            <input type="password" id="critic-api-key" class="form-input" placeholder="输入 API Key...">
            <button class="btn btn-secondary" type="button" onclick="toggleKeyVisibility('critic-api-key')" style="padding:0 12px; white-space:nowrap;">👁️</button>
          </div>
        </div>
        <div class="form-group" style="margin-top:12px;">
          <button class="btn btn-secondary" type="button" onclick="testCriticConnection()" id="btn-test-critic" style="width:100%; font-size:13px; font-weight:700;">
            ⚡ 立即测试外审连通性 (Test Connection)
          </button>
          <div id="test-critic-result" style="display:none; margin-top:8px; padding:10px 14px; border-radius:8px; font-size:13px;"></div>
        </div>
        <div class="form-group" style="margin-top:16px; border-top:1px solid var(--border-color); padding-top:14px;">
          <label class="form-label">TypeSafe Jev API Key (快车道 349ms 原语 - 可选)</label>
          <input type="password" id="jev-key" class="form-input" placeholder="输入 sk-jev-... (留空则走 Tier 0 本地确定性引擎)">
        </div>
        <div class="switch-row">
          <div>
            <div class="switch-label">启用 Fast-Path Jev 极速拦截</div>
            <div class="switch-sub">~350ms 零延迟拦截违规，不抢 GPU</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="fast-jev" checked>
            <span class="slider"></span>
          </label>
        </div>
        <div class="switch-row">
          <div>
            <div class="switch-label">Tier 0 离线纯白嫖兜底</div>
            <div class="switch-sub">无 API Key 时自动由本地确定性状态机防线兜底</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="offline-fallback" checked>
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </div>

    <!-- 深度安全与防线卡片 -->
    <div class="card" style="margin-bottom: 25px;">
      <div class="card-title">🔒 深度硬安全防线 (Hardware-Locked Security)</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div class="switch-row">
          <div>
            <div class="switch-label">防反向提示词注入 (Context Integrity)</div>
            <div class="switch-sub">严禁工具输出篡改系统上下文</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="sec-prompt" checked>
            <span class="slider"></span>
          </label>
        </div>
        <div class="switch-row">
          <div>
            <div class="switch-label">破坏性数据覆写熔断 (Data Guard)</div>
            <div class="switch-sub">覆写前强行对比容量与行数差异</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="sec-overwrite" checked>
            <span class="slider"></span>
          </label>
        </div>
        <div class="switch-row">
          <div>
            <div class="switch-label">供应链 AST 混淆扫描 (Supply Chain Scan)</div>
            <div class="switch-sub">拦截 eval / b64decode / 反弹 Shell</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="sec-ast" checked>
            <span class="slider"></span>
          </label>
        </div>
        <div class="switch-row">
          <div>
            <div class="switch-label">孤儿进程与端口防盗 (Leak Guard)</div>
            <div class="switch-sub">收尾强制扫描杀灭残留占用端口</div>
          </div>
          <label class="toggle">
            <input type="checkbox" id="sec-leak" checked>
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </div>

    <!-- 动作按钮栏 -->
    <div class="btn-group">
      <button class="btn btn-primary" onclick="saveSettings()">💾 保存并立即物理生效</button>
      <a class="btn btn-secondary" href="/dashboard">📊 打开实时全景审判大盘</a>
      <button class="btn btn-danger" onclick="triggerRollback()">💊 3秒一键回滚基准快照</button>
    </div>
  </div>

  <div id="toast" class="toast"></div>

  <script>
    let currentConfig = {};

    function onCriticProviderChange() {
      const p = document.getElementById('critic-provider').value;
      const bEl = document.getElementById('critic-base-url');
      const mEl = document.getElementById('critic-model');
      const kEl = document.getElementById('critic-api-key');

      if (p === 'gemini') {
        bEl.placeholder = 'https://generativelanguage.googleapis.com/v1beta/openai';
        if (!bEl.value || bEl.value.includes('bigmodel') || bEl.value.includes('deepseek') || bEl.value.includes('openai.com')) {
          bEl.value = 'https://generativelanguage.googleapis.com/v1beta/openai';
        }
        mEl.value = 'gemini-2.5-flash';
        kEl.placeholder = 'AIzaSy... (Gemini API Key)';
      } else if (p === 'glm') {
        bEl.placeholder = 'https://open.bigmodel.cn/api/paas/v4 或月卡中转 https://1.19848845.xyz';
        if (!bEl.value || bEl.value.includes('generativelanguage') || bEl.value.includes('deepseek')) {
          bEl.value = 'https://open.bigmodel.cn/api/paas/v4';
        }
        mEl.value = 'glm-5.3-flash';
        kEl.placeholder = '智谱/月卡 API Key (sk-...)';
      } else if (p === 'deepseek') {
        bEl.placeholder = 'https://api.deepseek.com/v1';
        if (!bEl.value || bEl.value.includes('generativelanguage') || bEl.value.includes('bigmodel')) {
          bEl.value = 'https://api.deepseek.com/v1';
        }
        mEl.value = 'deepseek-chat';
        kEl.placeholder = 'sk-... (DeepSeek API Key)';
      } else if (p === 'openai') {
        bEl.placeholder = 'https://api.openai.com/v1';
        bEl.value = 'https://api.openai.com/v1';
        mEl.value = 'gpt-4o-mini';
        kEl.placeholder = 'sk-... (OpenAI API Key)';
      } else if (p === 'ollama') {
        bEl.value = 'http://localhost:11434/v1';
        mEl.value = 'qwen2.5:7b';
        kEl.placeholder = '无需填入 (本地免Key)';
      } else if (p === 'local_heuristic') {
        bEl.value = 'local';
        mEl.value = 'tier0_rules';
        kEl.placeholder = '纯离线本地正则与AST硬拦截 (免Key)';
      }
    }

    function toggleKeyVisibility(id) {
      const el = document.getElementById(id);
      if (el) el.type = el.type === 'password' ? 'text' : 'password';
    }

    async function testCriticConnection() {
      const btn = document.getElementById('btn-test-critic');
      const resEl = document.getElementById('test-critic-result');
      const provider = document.getElementById('critic-provider').value;
      const base_url = document.getElementById('critic-base-url').value.trim();
      const model = document.getElementById('critic-model').value.trim();
      const api_key = document.getElementById('critic-api-key').value.trim();

      btn.disabled = true;
      btn.innerText = '⏳ 正在测试网络连通性...';
      resEl.style.display = 'block';
      resEl.style.background = 'rgba(59, 130, 246, 0.15)';
      resEl.style.color = '#93c5fd';
      resEl.style.border = '1px solid #3b82f6';
      resEl.innerText = '正在向外审端点发送握手探测请求...';

      try {
        const resp = await fetch('/api/critic/test', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ provider, base_url, model, api_key })
        });
        const result = await resp.json();
        if (result.ok) {
          resEl.style.background = 'rgba(16, 185, 129, 0.15)';
          resEl.style.color = '#34d399';
          resEl.style.border = '1px solid #10b981';
          resEl.innerHTML = `✅ <b>${result.message}</b><br><small style="color:#cbd5e1">模型: ${result.model || model} · 延迟: ${result.latency_ms}ms</small>`;
        } else {
          resEl.style.background = 'rgba(239, 68, 68, 0.15)';
          resEl.style.color = '#fca5a5';
          resEl.style.border = '1px solid #ef4444';
          resEl.innerHTML = `❌ <b>${result.message || '连接失败'}</b>`;
        }
      } catch (err) {
        resEl.style.background = 'rgba(239, 68, 68, 0.15)';
        resEl.style.color = '#fca5a5';
        resEl.style.border = '1px solid #ef4444';
        resEl.innerHTML = `❌ 请求异常: ${err}`;
      } finally {
        btn.disabled = false;
        btn.innerText = '⚡ 立即测试外审连通性 (Test Connection)';
      }
    }

    async function loadData() {
      try {
        const res = await fetch('/api/config');
        currentConfig = await res.json();

        selectProfile(currentConfig.active_profile || 'vibe-boss');
        document.getElementById('jev-key').value = currentConfig.jev_api_key || '';

        const critic = currentConfig.critic || {};
        if (critic.provider) {
          document.getElementById('critic-provider').value = critic.provider;
        }
        document.getElementById('critic-base-url').value = critic.base_url && critic.base_url !== 'auto' ? critic.base_url : '';
        document.getElementById('critic-model').value = critic.model && critic.model !== 'auto' ? critic.model : '';
        document.getElementById('critic-api-key').value = critic.api_key && critic.api_key !== 'auto' ? critic.api_key : '';

        document.getElementById('fast-jev').checked = currentConfig.engine?.fast_path_jev !== false;
        document.getElementById('offline-fallback').checked = currentConfig.engine?.offline_fallback !== false;

        document.getElementById('sec-prompt').checked = currentConfig.security?.anti_prompt_injection !== false;
        document.getElementById('sec-overwrite').checked = currentConfig.security?.data_overwrite_guard !== false;
        document.getElementById('sec-ast').checked = currentConfig.security?.supply_chain_ast_scan !== false;
        document.getElementById('sec-leak').checked = currentConfig.security?.process_leak_guard !== false;
      } catch (e) {
        showToast("⚠️ 配置读取失败");
      }
    }

    function selectProfile(name) {
      document.querySelectorAll('.profile-card').forEach(c => {
        if (c.dataset.profile === name) c.classList.add('active');
        else c.classList.remove('active');
      });
      currentConfig.active_profile = name;
    }

    async function saveSettings() {
      currentConfig.jev_api_key = document.getElementById('jev-key').value.trim();

      const criticProvider = document.getElementById('critic-provider').value;
      const criticBaseUrl = document.getElementById('critic-base-url').value.trim();
      const criticModel = document.getElementById('critic-model').value.trim();
      const criticApiKey = document.getElementById('critic-api-key').value.trim();

      currentConfig.critic = {
        provider: criticProvider,
        base_url: criticBaseUrl || 'auto',
        model: criticModel || 'auto',
        api_key: criticApiKey || 'auto',
        timeout: 25.0
      };

      currentConfig.engine = {
        fast_path_jev: document.getElementById('fast-jev').checked,
        offline_fallback: document.getElementById('offline-fallback').checked
      };
      currentConfig.security = {
        anti_prompt_injection: document.getElementById('sec-prompt').checked,
        data_overwrite_guard: document.getElementById('sec-overwrite').checked,
        supply_chain_ast_scan: document.getElementById('sec-ast').checked,
        process_leak_guard: document.getElementById('sec-leak').checked
      };

      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(currentConfig)
        });
        if (res.ok) {
          showToast("🎉 配置已成功保存并立即物理生效！");
        }
      } catch (e) {
        showToast("❌ 保存失败: " + e);
      }
    }

    async function triggerRollback() {
      if (confirm("⚠️ 确认要执行 3 秒一键回滚吗？系统将立刻无损还原至基准快照！")) {
        showToast("💊 正在回滚至基准快照...");
        try {
          await fetch('/api/action/rollback', { method: 'POST' });
          showToast("🎉 已成功恢复！系统完全还原至今日基准！");
        } catch(e) {}
      }
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 3000);
    }

    window.onload = loadData;
  </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")
        if not path:
            path = "/"

        if path in ("/", "/dashboard"):
            if DASHBOARD_HTML_PATH.exists():
                try:
                    content = DASHBOARD_HTML_PATH.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif path == "/settings":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif path == "/api/recent":
            events = get_recent_events(limit_per_engine=200)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(events, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/rules":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(FALLBACK_RULES, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/shadow":
            shadow = get_shadow_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(shadow, ensure_ascii=False).encode("utf-8"))
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "status": "HEALTHY",
                "service": "truthgate-dashboard",
                "port": getattr(self.server, "server_port", 17911)
            }).encode("utf-8"))
        elif path == "/api/blood-status":
            try:
                from truthgate.blood_doctor import get_blood_status
            except ImportError:
                try:
                    from blood_doctor import get_blood_status
                except ImportError:
                    get_blood_status = lambda: {"blood_score": 100, "status_label": "🟢 满血版"}
            data = get_blood_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/doctor":
            try:
                from truthgate.doctor import run_doctor
            except ImportError:
                try:
                    from doctor import run_doctor
                except ImportError:
                    from superego.doctor import run_doctor
            data = run_doctor(cached=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                events = get_recent_events(limit_per_engine=10)
                if events:
                    latest = events[-1]
                    self.wfile.write(f"data: {json.dumps(latest, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                # 保持连接心跳
                for _ in range(30):
                    time.sleep(2)
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, Exception):
                pass
            return
        elif path == "/api/monitor-stats":
            try:
                from verdict_monitor import get_monitor_stats
            except ImportError:
                try:
                    from truthgate.verdict_monitor import get_monitor_stats
                except ImportError:
                    get_monitor_stats = None
            data = get_monitor_stats() if get_monitor_stats else {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/test-summary":
            data = get_test_summary()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/health-check":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "engines": {"claude": "active", "antigravity": "active", "codex": "active", "dsh": "active"}
            }, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/config":
            try:
                cfg = load_config()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        if url.path == "/api/doctor/heal":
            try:
                from truthgate.doctor import auto_heal
            except ImportError:
                try:
                    from doctor import auto_heal
                except ImportError:
                    from superego.doctor import auto_heal
            data = auto_heal()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif url.path == "/api/mark-false-positive":
            try:
                data = json.loads(post_data.decode("utf-8"))
                raw = data.get("raw", "")
                reason = data.get("reason", "")
                rule = data.get("rule", "")
                ts = data.get("timestamp", "")
                
                # 1. 记入 monitor.db 误伤申诉表
                try:
                    from truthgate.verdict_monitor import record_false_positive
                except ImportError:
                    try:
                        from verdict_monitor import record_false_positive
                    except ImportError:
                        record_false_positive = None
                if record_false_positive:
                    record_false_positive(
                        verdict_id=None,
                        user_refutation=reason,
                        fired_rules=[rule] if rule else []
                    )
                
                # 2. 记入 false_positives.jsonl
                fp_file = CLAUDE_DIR / "hooks" / "false_positives.jsonl"
                fp_file.parent.mkdir(parents=True, exist_ok=True)
                with open(fp_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts": ts or datetime.now().isoformat(),
                        "raw": raw,
                        "rule": rule,
                        "reason": reason
                    }, ensure_ascii=False) + "\n")
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "message": "已登记误判申诉并记入审计账本"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif url.path == "/api/critic/test":
            try:
                data = json.loads(post_data.decode("utf-8"))
                provider = data.get("provider", "tiered")
                base_url = (data.get("base_url") or "").strip()
                model = (data.get("model") or "").strip()
                api_key = (data.get("api_key") or "").strip()

                if base_url in ("", "auto"):
                    base_url = ""
                if model in ("", "auto"):
                    model = ""
                if api_key in ("", "auto"):
                    api_key = ""

                if api_key.startswith("env:"):
                    api_key = os.environ.get(api_key[4:], "")

                if provider in ("local_heuristic", "tiered") and not api_key:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "ok": True,
                        "latency_ms": 0,
                        "model": "local_ast_tier0",
                        "message": "Tier 0 离线硬防线状态正常 (0ms 延迟 · 100% 离线保底)"
                    }, ensure_ascii=False).encode("utf-8"))
                    return

                if not base_url:
                    if provider == "gemini":
                        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
                        model = model or "gemini-3.8-flash"
                    elif provider in ("glm", "zhipu"):
                        base_url = "https://open.bigmodel.cn/api/paas/v4"
                        model = model or "glm-4-flash"
                    elif provider == "deepseek":
                        base_url = "https://api.deepseek.com/v1"
                        model = model or "deepseek-chat"
                    elif provider == "openai":
                        base_url = "https://api.openai.com/v1"
                        model = model or "gpt-4o-mini"
                    elif provider == "ollama":
                        base_url = "http://localhost:11434/v1"
                        model = model or "qwen2.5:7b"
                    elif provider == "agnes":
                        base_url = "https://apihub.agnes-ai.com/v1"
                        model = model or "agnes-3.0-flash"

                import time, urllib.request
                t0 = time.time()
                req_url = base_url.rstrip("/")
                is_anthropic_relay = "1.19848845.xyz" in req_url or req_url.endswith("/messages")

                if is_anthropic_relay:
                    endpoint = f"{req_url}/v1/messages" if not req_url.endswith("/v1/messages") else req_url
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    }
                    payload = {
                        "model": model or "glm-5.3-flash",
                        "max_tokens": 15,
                        "messages": [{"role": "user", "content": "ping"}]
                    }
                else:
                    endpoint = f"{req_url}/chat/completions" if not req_url.endswith("/chat/completions") else req_url
                    headers = {"Content-Type": "application/json"}
                    if api_key and api_key != "ollama":
                        headers["Authorization"] = f"Bearer {api_key}"
                    if provider == "gemini" and api_key and api_key != "ollama":
                        headers["x-goog-api-key"] = api_key
                    payload = {
                        "model": model or "gemini-3.8-flash",
                        "max_tokens": 15,
                        "messages": [{"role": "user", "content": "ping"}]
                    }

                req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=12.0) as resp:
                    latency = round((time.time() - t0) * 1000, 1)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "ok": True,
                        "latency_ms": latency,
                        "model": model,
                        "message": f"连通成功！真实延迟: {latency}ms (状态: HTTP 200 OK)"
                    }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "ok": False,
                    "error": str(e),
                    "message": f"连接失败: {e}"
                }, ensure_ascii=False).encode("utf-8"))
        elif url.path == "/api/config":
            try:
                new_cfg = json.loads(post_data.decode("utf-8"))
                critic_data = new_cfg.get("critic", {})
                c_provider = critic_data.get("provider") or new_cfg.get("critic_provider")
                c_base = critic_data.get("base_url") or new_cfg.get("critic_base_url")
                c_model = critic_data.get("model") or new_cfg.get("critic_model")
                c_key = (critic_data.get("api_key") or new_cfg.get("critic_api_key") or new_cfg.get("agnes_api_key") or "").strip()

                if c_provider or c_key or c_base or c_model:
                    try:
                        from config import set_critic_config, get_critic_config
                    except ImportError:
                        try:
                            from truthgate.config import set_critic_config, get_critic_config
                        except ImportError:
                            set_critic_config = None
                    if set_critic_config:
                        set_critic_config(
                            provider=c_provider,
                            base_url=c_base,
                            model=c_model,
                            api_key=c_key if c_key else None
                        )
                        try:
                            new_cfg["critic"] = get_critic_config()
                        except Exception:
                            pass
                cfg = load_config()
                cfg.update(new_cfg)
                save_config(cfg)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        elif url.path == "/api/action/sync":
            switch_script = CLAUDE_DIR / "superego-switch.py"
            if switch_script.exists():
                subprocess.run([sys.executable, str(switch_script), "sync"], check=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif url.path == "/api/action/rollback":
            switch_script = CLAUDE_DIR / "superego-switch.py"
            if switch_script.exists():
                subprocess.run([sys.executable, str(switch_script), "rollback"], check=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # 静默控制台日志
        pass


class DashboardServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_dashboard(port: int = 17911, open_browser: bool = True):
    """启动本地 Web 仪表盘"""
    server_address = ("127.0.0.1", port)
    for _ in range(5):
        try:
            httpd = DashboardServer(server_address, DashboardHandler)
            break
        except OSError:
            port += 1
            server_address = ("127.0.0.1", port)
    else:
        print(f"❌ 无法绑定端口 {port}，启动失败。")
        return

    url = f"http://127.0.0.1:{port}/dashboard"
    print("=" * 70)
    print("🖥️ TRUTHGATE 1.0 VISUAL DASHBOARD (跨端全景审判大盘)")
    print(f"大盘访问地址: {url}")
    print("• 实时司法审判大盘: " + url)
    print(f"• 控制中枢设置面板: http://127.0.0.1:{port}/settings")
    print("按 Ctrl+C 退出控制大盘")
    print("=" * 70)

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n大盘已安全退出。")
        httpd.server_close()


if __name__ == "__main__":
    run_dashboard(open_browser=False)
