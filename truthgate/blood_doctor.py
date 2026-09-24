# -*- coding: utf-8 -*-
"""blood_doctor.py —— TruthGate 1.0 满血度诊断与核心器官体检引擎 (Full-Blood Health Doctor).

核心使命:
1. 终结「假健康」与「静默降级」:
   - 过去无 Key 或离线时，系统静默降级到 Tier 0 正则保底，但在 doctor 中仍显示 100 分通过；
   - 导致用户/外部参赛者以为跑的是满血 TruthGate，实际处于 0% Jev / 0% CodeGraph / 0% 外审的「残血版」！
2. 明确定义 6 大核心器官 (The 6 Vital Organs):
   - 【器官 1】TypeSafe Jev System-1 意图快车道 (25分): 349ms 结构化拦截反问与甩锅
   - 【器官 2】外审模型深度裁判 (Agnes / DeepSeek / Gemini) (20分): 深度语义行为对齐
   - 【器官 3】CodeGraph 拓扑图谱分析引擎 (20分): 根因排查双向 Callers/Callees 诊断
   - 【器官 4】17911 司法裁决与全景大盘中枢 (15分): 向量语义召回与 Web 实时大盘
   - 【器官 5】多端物理门禁挂载 (Claude/Codex/Antigravity) (10分): 原生进程接管
   - 【器官 6】假阴性漏判元监控 (False Negative Meta-Monitor) (10分): 漏判自愈数据库完整性
3. 满血度评分:
   - 100/100: 🩸 满血旗舰版 (Full-Blooded Mode) —— 具备最强紧箍咒与自愈防御力
   - < 100: ⚠️ 残血保底版 (Degraded Mode) —— 仅靠离线正则兜底，给出精准缺损清单与 1 键修复命令
"""
import os
import sys
import json
import shutil
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

HOME = Path.home()
TRUTHGATE_HOME = HOME / ".truthgate"
SUPEREGO_HOME = HOME / ".superego"
CLAUDE_HOME = HOME / ".claude"
CODEX_HOME = HOME / ".codex"
GEMINI_HOME = HOME / ".gemini"

try:
    from config import load_config, get_critic_config, CONFIG_FILE
except ImportError:
    try:
        from truthgate.config import load_config, get_critic_config, CONFIG_FILE
    except ImportError:
        def load_config(): return {}
        def get_critic_config(): return {}
        CONFIG_FILE = TRUTHGATE_HOME / "config.json"


def _probe_url(url: str, timeout: float = 1.5, headers: Optional[dict] = None) -> tuple:
    """探测 HTTP 接口连通性，返回 (status_code, latency_ms, error_msg)"""
    t0 = time.perf_counter()
    h = {"User-Agent": "TruthGate-BloodDoctor/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dt = (time.perf_counter() - t0) * 1000
            return resp.status, round(dt, 1), None
    except urllib.error.HTTPError as e:
        dt = (time.perf_counter() - t0) * 1000
        return e.code, round(dt, 1), f"HTTP {e.code}"
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return 0, round(dt, 1), str(e)


def check_organ_codegraph() -> Dict[str, Any]:
    """【器官 3】CodeGraph 拓扑图谱分析引擎体检 (20分)"""
    res = {
        "id": "codegraph",
        "name": "CodeGraph 拓扑图谱引擎",
        "weight": 20,
        "score": 0,
        "healthy": False,
        "status": "MISSING",
        "path": None,
        "detail": "",
        "fix_cmd": "npm install -g @codegraph/cli 或配置 PATH"
    }

    # 1. 检查环境变量 PATH 中是否有 codegraph 可执行文件
    for name in ["codegraph", "codegraph.cmd", "codegraph.ps1", "codegraph.exe"]:
        p = shutil.which(name)
        if p:
            res["path"] = p
            res["healthy"] = True
            res["status"] = "HEALTHY"
            res["score"] = 20
            res["detail"] = f"发现 CLI 可执行文件: {p}"
            return res

    # 2. Windows 常见 Node 全局目录探查
    candidate_paths = [
        HOME / "bin" / "nodejs" / "codegraph.ps1",
        HOME / "bin" / "nodejs" / "codegraph.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "codegraph.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "codegraph.ps1",
        Path(r"C:\Program Files\nodejs\codegraph.cmd"),
    ]
    for cp in candidate_paths:
        if cp.exists():
            res["path"] = str(cp)
            res["healthy"] = True
            res["status"] = "HEALTHY"
            res["score"] = 20
            res["detail"] = f"发现本地安装: {cp} (建议将其所在目录加入 PATH)"
            return res

    # 3. 检查当前或父目录是否已构建 .codegraph 索引
    cur = Path.cwd()
    for p in [cur] + list(cur.parents)[:3]:
        if (p / ".codegraph").exists():
            res["healthy"] = True
            res["status"] = "HEALTHY"
            res["score"] = 20
            res["detail"] = f"当前工程包含 .codegraph 索引目录 ({p / '.codegraph'})"
            return res

    res["detail"] = "未在系统 PATH 中找到 codegraph，无法执行双向调用链核验（Callers/Callees）"
    return res


def check_organ_jev() -> Dict[str, Any]:
    """【器官 1】TypeSafe Jev System One 毫秒意图快车道体检 (25分)"""
    res = {
        "id": "jev",
        "name": "TypeSafe Jev System-1 毫秒意图快车道",
        "weight": 25,
        "score": 0,
        "healthy": False,
        "status": "MISSING",
        "api_latency_ms": 0.0,
        "detail": "",
        "fix_cmd": "tg setup --typesafe-key <KEY> (获取地址: https://typesafe.ai)"
    }

    # 读取 API Key
    api_key = os.environ.get("TYPESAFE_API_KEY", "")
    if not api_key:
        cfg = load_config()
        api_key = cfg.get("typesafe_api_key") or cfg.get("jev_api_key") or ""
        if not api_key:
            for d in [TRUTHGATE_HOME, SUPEREGO_HOME]:
                env_f = d / ".env"
                if env_f.exists():
                    try:
                        for ln in env_f.read_text(encoding="utf-8-sig").splitlines():
                            if ln.strip().startswith("TYPESAFE_API_KEY="):
                                api_key = ln.split("=", 1)[1].strip()
                                break
                    except Exception:
                        pass
                if api_key:
                    break

    if not api_key:
        res["detail"] = "未配置 TYPESAFE_API_KEY，系统已静默退回 Tier 0 正则保底（失去 349ms 结构化拦截能力）"
        return res

    # 探查 Console 与网关
    c_code, c_lat, _ = _probe_url("https://console.typesafe.ai", timeout=2.0)
    res["api_latency_ms"] = c_lat

    try:
        try:
            from jev_engine import judge_assistant_text
        except ImportError:
            from truthgate.jev_engine import judge_assistant_text

        t0 = time.perf_counter()
        jres = judge_assistant_text("测试文本：所有修改均已完成并通过测试 exit code 0", sid="blood_probe", timeout=2.5)
        dt = round((time.perf_counter() - t0) * 1000, 1)
        res["api_latency_ms"] = dt

        if jres.get("mode") == "jev_system_one" or not jres.get("error"):
            res["healthy"] = True
            res["status"] = "HEALTHY"
            res["score"] = 25
            res["detail"] = f"满血在线 ({dt}ms, Key 已生效, 强类型结构化阻断开启)"
        else:
            res["status"] = "DEGRADED"
            res["score"] = 10
            res["detail"] = f"API 存在抖动 ({jres.get('mode', 'fallback')})，已启用本地 fail-open 保护"
    except Exception as e:
        res["status"] = "DEGRADED"
        res["score"] = 10
        res["detail"] = f"探针调用异常 ({e})，暂以本地 Tier 0 接管"

    return res


def check_organ_critic() -> Dict[str, Any]:
    """【器官 2】外审模型深度裁判 (Gemini / DeepSeek / OpenAI / Ollama / Agnes) (20分)"""
    res = {
        "id": "critic",
        "name": "外审模型深度裁判 (Gemini / DeepSeek / OpenAI / Ollama / Agnes)",
        "weight": 20,
        "score": 0,
        "healthy": False,
        "status": "MISSING",
        "provider": "unknown",
        "model": "unknown",
        "detail": "",
        "fix_cmd": "tg critic set --provider gemini --api-key <KEY> (或 export GEMINI_API_KEY=... / DEEPSEEK_API_KEY=...)"
    }

    try:
        from semantic_judge import get_critic_endpoint
    except ImportError:
        try:
            from truthgate.semantic_judge import get_critic_endpoint
        except ImportError:
            get_critic_endpoint = None

    ep = get_critic_endpoint() if get_critic_endpoint else None
    if ep:
        res["provider"] = ep.get("provider", "unknown")
        res["model"] = ep.get("model", "unknown")
        res["healthy"] = True
        res["status"] = "HEALTHY"
        res["score"] = 20
        res["detail"] = f"外审就绪 [{ep.get('provider')}] 模型: {ep.get('model')}"
        return res

    critic_cfg = get_critic_config()
    provider = critic_cfg.get("provider", "tiered")
    model = critic_cfg.get("model", "")
    res["provider"] = provider
    res["model"] = model

    try:
        from critic_engine import _resolve_api_key
    except ImportError:
        try:
            from truthgate.critic_engine import _resolve_api_key
        except ImportError:
            _resolve_api_key = lambda s: ""

    key_str = critic_cfg.get("api_key", "")
    key_val = _resolve_api_key(key_str) if key_str else ""
    if not key_val:
        for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "AGNES_API_KEY", "CRITIC_API_KEY"]:
            val = _resolve_api_key(f"env:{k}")
            if val:
                key_val = val
                break

    base_url = critic_cfg.get("base_url", "")
    is_local = "localhost" in base_url or "127.0.0.1" in base_url

    if not key_val and not is_local:
        res["detail"] = "未配置外审 API Key (支持 Gemini / DeepSeek / OpenAI / Ollama / Agnes)，深度行为审判由 Tier 0 本地引擎接管"
        return res

    res["healthy"] = True
    res["status"] = "HEALTHY"
    res["score"] = 20
    res["detail"] = f"外审就绪 [{provider}] 模型: {model or 'default'}"
    return res


def check_organ_daemon() -> Dict[str, Any]:
    """【器官 4】17911 司法裁决与全景大盘守护进程 (15分)"""
    res = {
        "id": "daemon",
        "name": "17911 司法裁决与全景大盘守护进程",
        "weight": 15,
        "score": 0,
        "healthy": False,
        "status": "OFFLINE",
        "port": 17911,
        "detail": "",
        "fix_cmd": "tg service start (或运行 start-dissat-service.ps1)"
    }

    # 探查 17911 /health
    code, lat, err = _probe_url("http://127.0.0.1:17911/health", timeout=1.0)
    if code == 200:
        res["healthy"] = True
        res["status"] = "HEALTHY"
        res["score"] = 15
        res["detail"] = f"常驻运行中 (响应: {lat}ms, 大盘: http://127.0.0.1:17911/dashboard)"
        return res

    # 备选探查 17911 /dashboard
    code_dash, lat_dash, _ = _probe_url("http://127.0.0.1:17911/dashboard", timeout=1.0)
    if code_dash == 200:
        res["healthy"] = True
        res["status"] = "HEALTHY"
        res["score"] = 15
        res["detail"] = f"大盘服务运行中 (响应: {lat_dash}ms)"
        return res

    res["detail"] = "17911 端口未响应或已离线，大盘界面与向量语义召回不可用"
    return res


def check_organ_hooks() -> Dict[str, Any]:
    """【器官 5】多端物理门禁挂载 (Claude / Codex / Antigravity) (10分)"""
    res = {
        "id": "hooks",
        "name": "多端物理门禁与钩子挂载",
        "weight": 10,
        "score": 0,
        "healthy": False,
        "status": "MISSING",
        "platforms": [],
        "detail": "",
        "fix_cmd": "tg install"
    }

    mounted = []
    # 1. Claude
    c_set = CLAUDE_HOME / "settings.json"
    if c_set.exists():
        try:
            txt = c_set.read_text(encoding="utf-8", errors="ignore")
            if "hook_entry.py" in txt:
                mounted.append("Claude Code")
        except Exception:
            pass

    # 2. Codex
    x_hooks = CODEX_HOME / "hooks.json"
    if x_hooks.exists():
        try:
            txt = x_hooks.read_text(encoding="utf-8", errors="ignore")
            if "hook_entry.py" in txt:
                mounted.append("OpenAI Codex")
        except Exception:
            pass

    # 3. Antigravity
    ag_script = GEMINI_HOME / "antigravity" / "scripts" / "ag_superego_bridge.py"
    if ag_script.exists():
        mounted.append("Google Antigravity")

    res["platforms"] = mounted
    if len(mounted) >= 2:
        res["healthy"] = True
        res["status"] = "HEALTHY"
        res["score"] = 10
        res["detail"] = f"已挂载接管: {', '.join(mounted)}"
    elif len(mounted) == 1:
        res["healthy"] = False
        res["status"] = "PARTIAL"
        res["score"] = 5
        res["detail"] = f"部分挂载: {', '.join(mounted)}"
    else:
        res["detail"] = "未检测到已挂载的 AI 宿主钩子 (需运行 tg install)"

    return res


def check_organ_monitor() -> Dict[str, Any]:
    """【器官 6】假阴性漏判自愈元监控 (10分)"""
    res = {
        "id": "monitor",
        "name": "假阴性漏判元监控 (False Negative Meta-Monitor)",
        "weight": 10,
        "score": 0,
        "healthy": False,
        "status": "MISSING",
        "detail": "",
        "fix_cmd": "tg doctor --heal"
    }

    import sqlite3
    db_candidates = [
        TRUTHGATE_HOME / "monitor.db",
        SUPEREGO_HOME / "monitor.db"
    ]
    found_db = None
    for cand in db_candidates:
        if cand.exists():
            found_db = cand
            break

    if not found_db:
        res["detail"] = "未初始化 monitor.db 审计数据库"
        return res

    try:
        conn = sqlite3.connect(str(found_db))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='false_negatives'")
        has_fn = cur.fetchone() is not None
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verdict_records'")
        has_vr = cur.fetchone() is not None
        conn.close()

        if has_fn and has_vr:
            res["healthy"] = True
            res["status"] = "HEALTHY"
            res["score"] = 10
            res["detail"] = f"监控数据库健全 ({found_db.name}: false_negatives + verdict_records 完整)"
        else:
            res["status"] = "DEGRADED"
            res["score"] = 5
            res["detail"] = f"数据库缺少假阴性表结构 (has_fn={has_fn}, has_vr={has_vr})"
    except Exception as e:
        res["detail"] = f"检查数据库异常: {e}"

    return res


def get_blood_status() -> Dict[str, Any]:
    """计算当前系统的满血度评分与 6 大器官完整体检状态"""
    cg = check_organ_codegraph()
    jev = check_organ_jev()
    critic = check_organ_critic()
    daemon = check_organ_daemon()
    hooks = check_organ_hooks()
    monitor = check_organ_monitor()

    organs = {
        "jev": jev,
        "critic": critic,
        "codegraph": cg,
        "daemon": daemon,
        "hooks": hooks,
        "monitor": monitor
    }

    total_score = sum(o["score"] for o in organs.values())
    is_full = total_score == 100

    missing = []
    degraded_reasons = []
    for k, o in organs.items():
        if not o["healthy"]:
            missing.append(o["name"])
            degraded_reasons.append(f"{o['name']}: {o['detail']}")

    status_label = "🩸 满血旗舰版 (Full-Blooded 100%)" if is_full else f"⚠️ 残血保底中 (Degraded Mode: {total_score}%)"

    cfg = load_config()
    auto_open = cfg.get("ui", {}).get("auto_open_dashboard", True)

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "blood_score": total_score,
        "is_full_blooded": is_full,
        "status_label": status_label,
        "auto_open_dashboard": auto_open,
        "organs": organs,
        "missing_organs": missing,
        "degraded_reasons": degraded_reasons,
        "quick_fix": "tg setup" if not is_full else "已满血，无需修复"
    }


def print_blood_report():
    """在终端输出高辨识度的满血度诊断体检卡片"""
    data = get_blood_status()
    score = data["blood_score"]
    is_full = data["is_full_blooded"]

    print("\n" + "=" * 76)
    print("🩸 TRUTHGATE 1.0 满血度诊断报告 (Full-Blood Health Report)")
    print("=" * 76)
    print(f"满血度评分: {score} / 100   [{data['status_label']}]")
    print(f"诊断时间:   {data['timestamp']}  |  大盘自动弹窗: {'开启 (True)' if data['auto_open_dashboard'] else '关闭 (False)'}")
    print("-" * 76)

    organs = data["organs"]
    for idx, key in enumerate(["jev", "critic", "codegraph", "daemon", "hooks", "monitor"], 1):
        o = organs[key]
        tag = "🟢 满血" if o["healthy"] else ("🟡 降级" if o["score"] > 0 else "🔴 残血缺失")
        print(f"  {idx}. {o['name']:<42} : [{tag}] ({o['score']}/{o['weight']}分)")
        print(f"     └─ {o['detail']}")
        if not o["healthy"]:
            print(f"     └─ 🛠️ 修复指令: {o['fix_cmd']}")

    print("-" * 76)
    if is_full:
        print("🎉 恭喜！当前系统为 100% 满血旗舰状态！")
        print("• Jev 349ms 结构化极速快车道: 激活")
        print("• CodeGraph 双向调用拓扑核验: 激活")
        print("• 外部多模型深度裁判与实时大盘: 在线")
        print("• 访问大盘: http://127.0.0.1:17911/dashboard")
    else:
        print("⚠️ 警告：当前系统处于【残血降级模式 (DEGRADED)】！")
        print("在代码比赛、重构或复杂业务场景中，将面临以下致命缺陷：")
        if not organs["jev"]["healthy"]:
            print("  ❌ [缺少 Jev 引擎]: 无法在 349ms 内拦截反问/甩锅/代码黑话，容易产生无效请示")
        if not organs["codegraph"]["healthy"]:
            print("  ❌ [缺少 CodeGraph]: 无法在排查故障时强制双向图谱核验，容易引发治标不治本盲改")
        if not organs["critic"]["healthy"]:
            print("  ❌ [缺少外审模型]: 无法进行深层语义判决，仅依赖脆弱的纯文本正则")
        if not organs["daemon"]["healthy"]:
            print("  ❌ [后台守护离线]: 实时审判大盘与向量语义召回不可用")
        print("\n👉 立即升级至满血版:")
        print("   终端运行: tg setup (或一键升级: tg upgrade)")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    print_blood_report()
