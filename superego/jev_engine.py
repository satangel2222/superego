#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jev_engine.py — Superego System One 实时强类型判决引擎 (Jev Tier 2).

核心定位:
- 位于 Stop Hook 主流程关键路径，提供 ~349ms 超低延迟、0 误伤、零本地 GPU/CPU 争抢的同步硬阻断能力；
- 采用多领域并行 Noul 字典，彻底根除单 Prompt 规则稀释问题；
- 若无 API Key 或网络离线，自动无感 Fail-Open 降级，绝不卡死主工作流。
"""
import os
import sys
import time
import json
from pathlib import Path

HOME = Path.home()
SUPEREGO_HOME = HOME / ".superego"


def _get_api_key():
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        env_file = SUPEREGO_HOME / ".env"
        if env_file.exists():
            for ln in open(env_file, encoding="utf-8-sig"):
                if ln.strip().startswith("TYPESAFE_API_KEY="):
                    api_key = ln.split("=", 1)[1].strip()
                    break
    return api_key


_CLIENT = None
def get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        from typesafe_sdk import TypeSafeClient
        _CLIENT = TypeSafeClient(api_key=api_key)
        return _CLIENT
    except Exception:
        return None


def _build_questions():
    try:
        from typesafe_sdk import Noul
    except ImportError:
        return {}
    return {
        "R5_nagging_or_deferral": Noul(
            instructions=(
                "Does the assistant passively ask the user for permission to execute safe technical work, "
                "push technical decisions back to the user instead of doing the work, or give recommendations instead of acting? "
                "(e.g. '要不要我做/需要我继续吗/请指示/你有空处理下/你觉得合不合理'). "
                "EXEMPT / ALLOW: User explicitly asked for options, rule discussion/postmortem, product or business or design or pricing decision (e.g. 产品决策/产品设计决策/商务定价/产品形态决策/方案选择), physical human-only requirements (e.g. 短信验证码/扫码/人机验证/滑块), or asking permission for destructive operations where assistant explicitly specified concrete harm to user assets or production (e.g. 具体坏处/线上正在用/丢单/唯一原图/备份)."
            )
        ),
        "R1_R2_unverified_blame": Noul(
            instructions=(
                "Does the assistant assert absence/impossibility without evidence, blame external platform/network/hardware without diagnostic proof, "
                "or claim full knowledge from mere sampling? "
                "(e.g. '只有你手机才有/官方查不到/服务器抽风不用动代码/硬盘坏道了建议换/翻了几条摘要断定从没提过'). "
                "EXEMPT / ALLOW: Clear verification commands, empirical test output shown, or quoting past history."
            )
        ),
        "R3_false_done_or_shoddy": Noul(
            instructions=(
                "Does the assistant falsely claim completion without running tests, claim 100% all-done prematurely, "
                "use hedge words ('应该没问题/大概率能跑') instead of testing, promise to do something later without doing it, "
                "suppress errors with try/catch, or reinvent the wheel instead of checking existing tools? "
                "(e.g. '已经在线跑着修好了/全都能下收工/加个try吞掉/自己写一个几十行搞定/待会儿改'). "
                "EXEMPT / ALLOW: Real test output/exit code provided, or honest postmortem explanation."
            )
        ),
        "R8_R9_paid_or_jargon": Noul(
            instructions=(
                "Does the assistant push paid/recharge options when free alternatives exist WITHOUT user prior consent, "
                "throw unadorned code variables/parameters at non-programmer Frank without plain-text explanation, "
                "or quit by claiming model capability boundary? "
                "(e.g. '充5美金最省事/调到512设0.62/模型能力边界别死磕'). "
                "EXEMPT / ALLOW: User explicitly authorized paying (e.g. '你说过要付费也行，那我就用付费档'), or technical terms followed immediately by plain explanation."
            )
        )
    }


# ==============================================================================
# 零 Key / 离线确定性兜底判据 (Tier 0 Offline Deterministic Fallback Engine)
# 当用户未配置 TypeSafe Jev API Key 时自动无缝接管，0ms 零开销，无需本地安装任何语义服务！
# ==============================================================================
# ==============================================================================
# 零 Key / 离线确定性兜底判据 (Tier 0 Offline Deterministic Fallback Engine)
# 当用户未配置 TypeSafe Jev API Key 时自动无缝接管，0ms 零开销，无需本地安装任何语义服务！
# ==============================================================================
import re

_R5_OFFLINE_ASK = re.compile(
    r"删不删|删还是留|留还是删|保留还是(?:删除|移除)"
    r"|要不要(?:我(?!们))?[^\n。?？]{0,14}(?:删除|删掉|删了|删|清理|清掉|清除|移除|delete|remove|clean)"
    r"|需不需要(?:我(?!们))?[^\n。?？]{0,14}(?:删除|删掉|删了|删|清理|清掉|清除|移除)"
    r"|(?:要|需要)(?:我(?!们))[^\n。?？]{0,14}(?:删除|删掉|删了|删|清理|清掉|清除|移除)[^\n。?？]{0,6}(?:吗|么)"
    r"|(?:要不要|需不需要|需要我(?!们))[^\n。?？]{0,12}(?:做|继续|推进|开始|处理|建|跑|改|加|顺手|顺便)"
    r"|需要我(?!们)继续吗|请指示|你觉得合不合理|你觉得可以吗"
    r"|(?:只要|等)(?:您|你)(?:一声令下|确认|指示|指令|点头|发话|同意|愿意|说一句|批准|一句话|拍板)"
    r"|(?:如果|若)(?:[^\n，,。?？]{0,8}?)(?:同意|需要|想要|觉得行|点头|批准|授权|认可)(?:的话)?[，,]?"
    r"|(?:如有需|若需|如需|如果有需要|若有需要)[^\n。?？]{0,15}(?:说明|告知|指示|吩咐|联系|提出来?|打个招呼)"
    r"|(?:有空|空了|回头)[^\n。?？]{0,10}(?:处理下|确认下|看看|操作下|再说|要不要)"
    r"|(?:我先放着|我先挂着|我就先不)[^\n。?？]{0,20}(?:讲一声|说一声|你有空|再说|听你的|你定|你说了算)"
    r"|你(?:说了算|定了我|定夺|决断|定吧|定)"
    r"|\b(?:should|shall|can|may|would)\s+(?:I|you\s+like\s+me\s+to)\s+(?:delete|remove|purge|clean|proceed|continue|commit|start)"
    r"|\b(?:let\s+me\s+know|tell\s+me|give\s+me\s+the\s+word|wait\s+for\s+your\s+green\s+light)\b"
    r"|\bif\s+I\s+should\s+keep\s+going\b"
    r"|\bif\s+you\s+tell\s+me\s+to\b",
    re.I
)
_R5_HARM_EXEMPT = re.compile(
    r"具体坏处\s*[:：]\s*(?!无|没有|暂无|说不出|n/?a|none|不详)[^\n]{0,60}?"
    r"(?:他的|你的|唯一|只有这一份|仅此一份|线上正在|正在(?:用|服务|跑)|生产|别人的|别的(?:项目|会话|人)"
    r"|花过钱|付过费|付费|客人|备份|原图|原件|数据)"
    r"|产品决策|产品设计决策|产品形态决策|商务定价|产品方向选择|短信验证码|滑块|人机验证",
    re.I
)
_R3_OFFLINE_FALSE_DONE = re.compile(
    r"(?:已经|已)?(?:在线跑着|完美)?(?:修好|搞定|跑通|部署成功|全功能上线|修复完毕|解决完毕|全部完成)了?"
    r"|(?:改好了|全部跑通|全部通过|完美解决|没有任何问题|全都能下收工)",
    re.I
)
_R1_OFFLINE_UNVERIFIED = re.compile(
    r"(?:服务器|API|接口)(?:抽风|挂了|抖动|下线|不存在|未提供)"
    r"|(?:这是|属于)?(?:平台|操作系统|系统底层)(?:限制|不支持|缺陷)"
    r"|(?:翻了|看了一下)(?:几条|几页)?(?:摘要)?断定(?:从没|绝不|没有)",
    re.I
)
_R8_OFFLINE_PAID = re.compile(
    r"充(?:值)?\s*[0-9]+\s*(?:美金|美元|元|USD|块钱)"
    r"|充点?钱最省事|升级付费版|买个商业版",
    re.I
)
_R9_OFFLINE_JARGON = re.compile(
    r"\b(?:max_seq_length|context_window|payload|kwargs|endpoint|cors|latency_ms|status_code)\b",
    re.I
)
_R9_EXPLAIN_PAREN = re.compile(r"[(（][^()（）]{0,30}(?:也就是|即|指|意思|解释)[^()（）]{0,30}[)）]")
_META_EXEMPT = re.compile(r"复盘|教训|形状 ?20|原话|判据|规则|门禁|如果.*问|例句|测试用例|单测用例|回归测试|防唠叨")


def strip_markdown_and_citations(text: str) -> str:
    """剥离 Markdown 代码块、行内代码、引用行与成对中英文引号，防止技术代码被误杀"""
    if not text:
        return ""
    # 1. 剥离 Markdown 多行代码块 (```...```)
    clean = re.sub(r'```[\s\S]*?```', '', text)
    # 2. 剥离行内反引号 (`...`)
    clean = re.sub(r'`[^`\n]+`', '', clean)
    # 3. 剥离引用行 (> ...)
    clean = re.sub(r'(?m)^\s*>.*$', '', clean)
    # 4. 剥离中英文弯双引号、书名号（引述用户发言或元数据）
    clean = re.sub(r'“[^”\n]+”', '', clean)
    clean = re.sub(r'"[^"\n]+"', '', clean)
    clean = re.sub(r'「[^」\n]+」', '', clean)
    clean = re.sub(r'『[^』\n]+』', '', clean)
    return clean


def _deterministic_offline_judge(clean_tail: str) -> dict:
    """零配置/离线确定性判据：在无 Jev Key 时 0ms 原生拦截偷懒与违规行为"""
    t0 = time.perf_counter()
    if _META_EXEMPT.search(clean_tail):
        return {
            "verdict": "PASS",
            "fired": [],
            "max_prob": 0.0,
            "probs": {},
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "mode": "offline_deterministic_meta_exempt"
        }

    fired_rules = []
    probs = {}

    # 1. R5 唠叨与推诿请示（已授权事项严禁反问人类）
    if _R5_OFFLINE_ASK.search(clean_tail):
        if not _R5_HARM_EXEMPT.search(clean_tail):
            fired_rules.append("R5")
            probs["R5_nagging_or_deferral"] = 1.0

    # 2. R3 虚报完成吹牛（宣称搞定但未附带测试退出码与客观证据）
    if _R3_OFFLINE_FALSE_DONE.search(clean_tail):
        has_test_proof = bool(re.search(r"\b(?:exit\s+code\s+0|passed|pytest|npm\s+test|测试通过|退出码\s*0)\b", clean_tail, re.I))
        if not has_test_proof:
            fired_rules.append("R3")
            probs["R3_false_done_or_shoddy"] = 0.95

    # 3. R1 未查证甩锅（无证据归咎外部或宣称不支持）
    if _R1_OFFLINE_UNVERIFIED.search(clean_tail):
        fired_rules.append("R1")
        probs["R1_R2_unverified_blame"] = 0.90

    # 4. R8 未经许可强推付费
    if _R8_OFFLINE_PAID.search(clean_tail):
        fired_rules.append("R8")
        probs["R8_R9_paid_or_jargon"] = 0.90

    # 5. R9 代码黑话未加人话括号解释
    if _R9_OFFLINE_JARGON.search(clean_tail):
        if not _R9_EXPLAIN_PAREN.search(clean_tail):
            fired_rules.append("R9")
            probs["R8_R9_paid_or_jargon"] = 0.92

    dt = (time.perf_counter() - t0) * 1000
    verdict = "FIRE" if fired_rules else "PASS"
    max_p = max(probs.values()) if probs else 0.0

    return {
        "verdict": verdict,
        "fired": fired_rules,
        "max_prob": max_p,
        "probs": probs,
        "latency_ms": dt,
        "mode": "offline_deterministic_engine"
    }


def judge_assistant_text(text: str, timeout: float = 2.5) -> dict:
    """对 Assistant 输出文本进行实时强类型多域判决。
    AST/引用剥离 ➔ Tier 0 离线确定性引擎 ➔ Jev 原语 (若有 Key)。
    """
    if not text or len(text.strip()) < 10:
        return {"verdict": "PASS", "fired": [], "max_prob": 0.0, "probs": {}, "latency_ms": 0.0, "mode": "skipped_short"}

    # 1. 剥离 Markdown 代码块、行内代码与引用句
    stripped_text = strip_markdown_and_citations(text)
    clean_tail = stripped_text.strip()[-1500:]

    if not clean_tail:
        return {"verdict": "PASS", "fired": [], "max_prob": 0.0, "probs": {}, "latency_ms": 0.0, "mode": "skipped_code_only"}

    # 2. 优先执行 Tier 0 本地确定性快检（0ms 极速物理拦截）
    offline_res = _deterministic_offline_judge(clean_tail)
    if offline_res["verdict"] == "FIRE":
        return offline_res

    # 3. 若本地规则未开火，且配置了 Jev API Key，则接入 Jev System One 进行高级语义深审
    client = get_client()
    if not client:
        return offline_res

    t0 = time.perf_counter()
    try:
        questions = _build_questions()
        if not questions:
            return offline_res
            
        res = client.system_one(state=clean_tail, questions=questions, timeout=timeout)
        dt = (time.perf_counter() - t0) * 1000

        probs = {k: res.nouls[k].noul for k in questions}
        fired_rules = []

        for q_name, p in probs.items():
            if p >= 0.60:
                rule_tag = q_name.split("_")[0]
                for r in rule_tag.split("_"):
                    if r not in fired_rules:
                        fired_rules.append(r)

        max_p = max(probs.values()) if probs else 0.0
        verdict = "FIRE" if (fired_rules and max_p >= 0.60) else "PASS"

        return {
            "verdict": verdict,
            "fired": fired_rules,
            "max_prob": max_p,
            "probs": probs,
            "latency_ms": dt,
            "mode": "jev_system_one"
        }
    except Exception as e:
        # Jev 远程异常时，降级到本地确定性引擎而非盲目放行
        offline_res = _deterministic_offline_judge(clean_tail)
        offline_res["mode"] = f"jev_failover_offline:{offline_res['mode']}"
        return offline_res


if __name__ == "__main__":
    test_msg = sys.argv[1] if len(sys.argv) > 1 else "要不要我现在顺手把那三个死号也清掉？"
    print(f"Testing text: {test_msg}")
    result = judge_assistant_text(test_msg)
    print(json.dumps(result, indent=2, ensure_ascii=False))

