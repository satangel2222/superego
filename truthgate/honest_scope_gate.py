# -*- coding: utf-8 -*-
"""honest_scope_gate.py —— 诚实履职与执行范围对账门禁 (Honest Scope Gate).

核心使命 (物理化 R16 / 最高第一铁律):
  严惩「用局部抽样冒充全量穷尽」的欺诈谎言！
  当 Agent 宣称“已逐页看完所有文档 / 全部测试全部跑通”，
  自动对账实际工具执行流水（Execution Telemetry）。
  若未真正穷尽，强制要求出具【定量对账单】（明确说明仅查阅了 M 篇，尚有 N 篇未读）。
"""
import re
from typing import Tuple, Optional, List, Dict, Any

EXHAUSTIVE_READ_CLAIM_RE = re.compile(
    r"(?:已(?:遵照|按照|根据).*?(?:全部|所有).*?(?:调阅|阅读|看[完了过]|完成)|"
    r"(?:全部|所有|每一个|各个).*?(?:文档|页面|网页|链接|接口|源码|Cookbook|手册).*?(?:逐[页篇个条]|都已|都已经|全部|都看[完了过]|都调阅|都执行|都跑通|都覆盖)|"
    r"逐[页篇个条](?:调阅|阅读|看[完了过]|分析|拆解)|"
    r"遍历了(?:所有|全部)|"
    r"把(?:所有|全部|每一个).*?(?:看[完了过]|读[完了过]|调阅|研读))",
    re.I
)

EXHAUSTIVE_TEST_CLAIM_RE = re.compile(
    r"(?:全部|所有|全量).*?(?:测试|门禁|单测|回归).*?(?:通过|跑通|全绿|完成|跑过)|"
    r"(?:已全量|全部).*?(?:回归|跑了一遍|测试了一遍)",
    re.I
)

HONEST_DISCLOSURE_RE = re.compile(
    r"(?:仅调阅|只调阅|仅阅读|只阅读|只看了|仅看了|抽样调阅|部分调阅|未读清单|尚未调阅|尚有.*?未读|实际调阅了?\s*\d+|实际精读了?\s*\d+)",
    re.I
)

HISTORIC_RE = re.compile(r"(?:^#\s*教训|教训案例库|【形状 20\d\d|历史案卷|历史教训)")


def check_honest_scope(
    text: str,
    tool_history: Optional[List[Dict[str, Any]]] = None,
    user_prompt: str = ""
) -> Tuple[bool, Optional[str]]:
    """审查模型回复中的穷尽式声明是否与实际工具流水对账吻合"""
    if not text or HISTORIC_RE.search(text):
        return True, None

    tools = tool_history or []

    # 1. 审核穷尽调阅断言
    m_read = EXHAUSTIVE_READ_CLAIM_RE.search(text)
    if m_read:
        # 若有诚实免责定量说明（如：实际仅调阅了 5 篇），予以放行
        if not HONEST_DISCLOSURE_RE.search(text):
            read_count = 0
            for t in tools:
                tname = (t.get("name") or t.get("tool_name") or "").lower()
                if tname in ("read_url_content", "view_file", "view"):
                    read_count += 1

            user_demanded_all = bool(re.search(r"(?:每一个|全部|所有).*?(?:文档|网页|页面|链接).*?(?:看完|读完|看过了|阅读完)", user_prompt))
            min_expected = 30 if user_demanded_all else 15

            if read_count < min_expected:
                matched = m_read.group(0)[:30]
                return False, (
                    f"⛔ [HONEST_SCOPE_VIOLATION] 严禁虚假履职与抽样夸大 (物理化 R16 铁律)！\n"
                    f"检测到回复中断言了穷尽调阅（命中:「{matched}」），\n"
                    f"但当前回合工具执行流水显示：实际仅查阅了 {read_count} 处文档/代码！\n"
                    f"铁律规定：\n"
                    f"① 严禁用局部抽样冒充全量完成，做多少说多少！\n"
                    f"② 若未穷尽阅读，必须在交付开头诚实出具【定量对账单】（如说明仅查阅了 M 篇，尚有 N 篇未读）；\n"
                    f"③ 若用户明确要求「每一个必须看完才准回答」，必须在后台继续调用工具逐一读完，严禁中途糊弄！"
                )

    # 2. 审核全量测试通过断言
    m_test = EXHAUSTIVE_TEST_CLAIM_RE.search(text)
    if m_test:
        has_test_run = False
        for t in tools:
            tname = (t.get("name") or t.get("tool_name") or "").lower()
            args_str = str(t.get("args") or t.get("input") or "").lower()
            if any(kw in args_str for kw in ("test", "pytest", "regression", "run_test")):
                has_test_run = True
                break

        if not has_test_run:
            matched = m_test.group(0)[:30]
            return False, (
                f"⛔ [HONEST_TEST_VIOLATION] 虚假测试断言拦截！\n"
                f"检测到在回复中断言了全量测试通过（命中:「{matched}」），\n"
                f"但本轮工具流水中【零次执行测试命令】（未运行 pytest/test 测试）！\n"
                f"必须在当前轮次实际运行全量回归命令并取得 exit code 0 后方可放行！"
            )

    return True, None
