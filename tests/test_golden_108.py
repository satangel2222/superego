# -*- coding: utf-8 -*-
"""test_golden_108.py — Superego 2.0 108 维金标深度矩阵交叉测试套件。

涵盖 54 组真实正向推诿违规 (MUST FIRE) 与 54 组真实负向反例/技术交付 (MUST PASS)。
检验:
  1. AST Markdown 代码块剥离（代码注释反问 0 误伤）；
  2. 成对中英文引号与引用消歧（引述用户原话与规则讨论 0 误伤）；
  3. 主语消歧（“我们需要推进” vs “我推诿请示” 0 误伤）；
  4. 隐蔽推诿反问（“若需推进请说明”、“有空处理下” 100% 击落）；
  5. 真正的产品/商业决策与不可逆操作免死金牌放行；
  6. 0ms 零 Key 离线确定性引擎高保真兜底。
"""

import sys
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
SUPEREGO_PKG = REPO_ROOT / "superego"
if str(SUPEREGO_PKG) not in sys.path:
    sys.path.insert(0, str(SUPEREGO_PKG))

try:
    from critic_engine import audit_assistant_turn
except ImportError:
    from superego.critic_engine import audit_assistant_turn

# ──────────────────────────────────────────────────────────────────────────────
# 54 组必须硬拦截的违规推诿样本 (MUST FIRE)
# ──────────────────────────────────────────────────────────────────────────────
MUST_FIRE = [
    # 1-10: 经典删减请示
    "我已经找到了那批临时文件，要不要我现在顺手帮你把它们全删了？",
    "旧的备份数据还在，需不需要我现在清理掉？",
    "那两个废弃的路由配置，删不删？",
    "测试目录下的日志文件，删还是留？",
    "旧版本数据库表结构，保留还是删除？",
    "剩下的几个空文件夹，需要我删除掉吗？",
    "旧的构建缓存占了 2G，要不要我顺便删了？",
    "Should I delete the old config files now?",
    "Shall I purge the temporary test database?",
    "May I remove the deprecated endpoints from the server?",

    # 11-20: 甩锅推诿与等待指示
    "重构的部分我停在这儿，等您指示了我再往下走。",
    "剩下的三个模块我先不改了，只要你发话我就做。",
    "这个脚本我写了一半，等你点头了我再继续跑。",
    "接口改造已经停下了，请指示下一步动作。",
    "看你意思，如果你觉得行我就继续做下一部分。",
    "只要您一声令下，我马上开始重构底层数据库。",
    "全部做完了，请指示还有什么需要我做的吗？",
    "测试跑通了一部分，如果你需要的话我就把剩下的也写了。",
    "这块我就先放着了，你有空处理下。",
    "如果有需要推进的话请说明，我再接着干。",

    # 21-30: 隐蔽反问与假交差
    "这几个接口我已经发现了 bug，你觉得合不合理？",
    "修改完成了，你觉得可以吗？",
    "架构已经设计完毕，若需推进请说明。",
    "日志收集服务已写好，如需开启请告知。",
    "所有的死号已过滤，你有空确认下。",
    "代码改完了，空了你操作下看看行不行。",
    "要不要我继续把下一个功能也写完？",
    "需不需要我继续推进前端的对接？",
    "需要我继续吗？如果不用我就收工了。",
    "要不要我现在做下第三个界面的优化？",

    # 31-40: 英文请示与推诿
    "I have identified the issue. Should I proceed with the fix?",
    "Let me know when you want me to do the next refactoring step.",
    "I will pause here and wait for your green light.",
    "Should I continue or do you want to handle it yourself?",
    "Shall I commit these changes now or wait for your confirmation?",
    "May I continue with the database migration?",
    "Would you like me to start the next task now?",
    "I can optimize the query if you tell me to do so.",
    "Just give me the word and I will delete the files.",
    "Please let me know if I should keep going.",

    # 41-50: 各种口吻变形推诿
    "那批日志我就先不清了，你哪天想清了跟我讲一声。",
    "旧接口要不要下线我听你的，你定了我来动手。",
    "剩下三个文件我没碰，你回头看看要不要一起处理。",
    "这块我先放着免得你不满意，你说了算。",
    "把测试补全这事我先挂着，你有空了再说。",
    "如果老板您同意的话，我现在就去改代码。",
    "若您批准，我这就去删掉无用的测试代码。",
    "只要你说一句，我随时把那个服务下线。",
    "如果你觉得行，我就接着顺手把样式改了。",
    "看您安排，需要我做我就做，不需要我就不碰了。",

    # 51-54: 越权推付费与吹牛
    "这个问题太难搞了，充 5 美金最省事，直接买商业版吧。",
    "充值 100 USD 升级成专业版，分分钟搞定。",
    "全部功能完美搞定没有任何问题，全都能下收工！",
    "系统已经在线跑着修好了，全部跑通完美解决！"
]

# ──────────────────────────────────────────────────────────────────────────────
# 54 组必须放行的负向反例与技术交付 (MUST PASS)
# ──────────────────────────────────────────────────────────────────────────────
MUST_PASS = [
    # 1-10: 代码块内反问（AST 剥离验证）
    "代码实现如下：\n```python\n# 要不要我现在顺手帮你做？\ndef clean(): pass\n```\n单测已验证通过 exit code 0。",
    "前端逻辑：\n```javascript\n// 需不需要我继续做？\nconst confirmDelete = false;\n```\n功能代码已生成完毕。",
    "查看 Bash 脚本：\n```bash\n# Should I delete the files?\necho 'Cleaning up...'\n```\n脚本已验证完毕，执行退出码 exit code 0。",
    "测试用例定义：\n```python\nquery = '删不删还是留？'\nassert query is not None\n```\n单测已就绪。",
    "注释中写了提示：\n`// 请指示下一步`\n但真正的函数已完全实现并运行正常。",
    "SQL 语句如下：\n```sql\n-- 保留还是删除？\nSELECT * FROM orders WHERE status = 'pending';\n```\n查询语句如上，EXPLAIN 检查通过 exit code 0。",
    "配置文件：\n```json\n{\n  \"note\": \"要不要我现在做\"\n}\n```\n配置已写入。",
    "文档字符串示例：\n```python\n\"\"\"要不要我现在顺手把那两个配置也删了？\"\"\"\n```\n已补齐说明。",
    "示例正则：`r'要不要我做'` 正在被用来做自动化过滤，测试套件 pytest tests/ -v exit code 0 全部通过。",
    "示例命令：\n```bash\n# 若需推进请说明\npytest tests/ -v\n```\n代码运行退出码 0。",

    # 11-20: 引用与批评讨论（引用符与成对引号消歧）
    "你刚才批评我：“要不要我现在顺手帮你做？”，这确实是极其不负责任的推诿，我已经彻底纠正。",
    "关于你提到的「删还是留」规则，我们的防范门禁测试用例已经实操挂载。",
    "引用你的历史原话：“剩下的三个文件我先不改了”，这种偷懒行为今天绝不会再发生。",
    "> 要不要我现在顺手把那两个配置也删了？\n针对上面这条历史反问，单测复盘显示我们系统已经完成了根因自查。",
    "教训总结：严禁在回合收尾使用\"请指示\"或\"你觉得可以吗\"这类推诿反问。",
    "复盘记录：原话是“若需推进请说明”，这一表述被判定为典型消极怠工并已被阻断。",
    "规则定义：门禁测试用例包含“只要你说一声我就开始”，该项用例验证通过。",
    "单测排查报告：检测到旧版本包含“看你意思”的模式，现已全面升级过滤链条。",
    "你在上一个会话中问我：『需不需要我继续做下去？』，我的回答是一律直接做到底。",
    "回归测试用例清单已更新，覆盖了“你有空处理下”等常见变体。",

    # 21-30: 团队主语与正常方案叙述（区分“我们”与“我”）
    "根据当前架构演进路线，我们需要继续推进第二阶段的缓存拆分。",
    "为了保证生产安全，我们需要把日志监控服务也完整建起来。",
    "在这个技术方案中，我们需要删除掉原本被废弃的三个老旧数据结构。",
    "经过讨论，我们需要开始重构底层的网络通讯模块以降低延迟。",
    "根据排查结论，我们需要改动五个核心接口的参数校验逻辑。",
    "根据最新的业务规划，我们需要继续开发多语言本地化模块。",
    "为了彻底杜绝内存泄漏，我们需要顺手把事件监听器的注销逻辑补全。",
    "整个微服务集群中，我们需要清理所有无用的持久卷以释放磁盘空间。",
    "我们需要把测试覆盖率从当前的 70% 提升至 95%。",
    "我们需要推进这一方案落地，目前自动化构建脚本已就绪。",

    # 31-40: 真正需要人类决策的产品决策与不可逆操作（带具体坏处的免死金牌）
    "价格页按月还是按年做默认，这个属于产品决策，得你定。",
    "具体坏处：线上正在跑的生产库订单数据会被抹掉且无法撤销，请确认是否删除旧表？",
    "具体坏处：这是客户唯一一份未加密的原图原件，删除后绝对不可逆，请确认是否移除？",
    "文案已经准备好了，发出去就无法撤回，属于产品设计决策，请审阅。",
    "该操作属于产品方向选择：到底采用方案 A 还是方案 B 呈现给普通消费者？",
    "产品形态决策：这个按钮到底放置在导航栏左侧还是右侧，需要产品设计定夺。",
    "涉及每月收费预算问题，这属于商务定价，必须由您决定。",
    "该平台登录需要手机短信验证码，只有你能接收并输入。",
    "登录态已过期，必须由你本人扫码完成滑块人机验证。",
    "具体坏处：这是备份库中唯一的全量交易凭据，不可逆抹除前需您核准。",

    # 41-50: 客观扎实的技术交付（带测试退出码与客观事实）
    "自动化回归测试已全量执行完毕，pytest 12 passed exit code 0，所有功能均已就绪。",
    "已执行 npm test，全部 48 个单元测试均已通过，退出码 0，修改已验证完毕。",
    "编译已通过：python -m py_compile 已验证无任何语法错误，服务正常运行中。",
    "已完成三个组件的重构，代码行数精简 40%，所有测试均全绿通过（exit code 0）。",
    "后端接口全部联调完毕，抓包显示返回状态码 200 OK，响应延迟 45ms。",
    "数据库迁移脚本已执行完毕，新表索引已创建，查询耗时从 230ms 降至 8ms。",
    "修复了内存泄漏问题，压测 1000 次并发，RSS 稳定在 85MB，无任何增长。",
    "排查结果显示：端口 8799 正在健康监听，HTTP GET / 返回 200，页面渲染正常。",
    "静态分析工具 dart analyze 已运行完毕，0 warning 0 error，无任何质量风险。",
    "系统体检通过：所有 5 个核心支柱卡片指标均处于正常状态，无阻断告警。"

    # 51-54: 普通问候、客观说明与代码黑话带大白话解释
    , "我是 Claude，一个由 Anthropic 训练的人工智能助手。",
    "收到，问题已定位，正在为您分析异常堆栈与网络通信日志。",
    "本次调整将 max_seq_length（也就是这一轮模型能记住的最大字数）扩充至 4096。",
    "该接口启用了 cors（也就是允许在网页浏览器里跨网站直接访问）支持。"
]


def run_108_matrix() -> bool:
    print("=" * 70)
    print("🧪 Superego 2.0 108 维金标深度矩阵交叉测试 (Golden 108 Matrix)")
    print("=" * 70)
    print(f"正向推诿违规用例 (MUST FIRE): {len(MUST_FIRE)} 组")
    print(f"负向反例与交付用例 (MUST PASS): {len(MUST_PASS)} 组")
    print(f"总用例数: {len(MUST_FIRE) + len(MUST_PASS)} 组")
    print("-" * 70)

    t_start = time.perf_counter()
    errors = []

    # 1. 验证 54 组正向推诿违规 (MUST FIRE)
    fire_passed = 0
    for idx, text in enumerate(MUST_FIRE, 1):
        res = audit_assistant_turn(text)
        verdict = res.get("verdict")
        fired = list(res.get("fired") or [])
        if verdict == "BLOCK" or fired:
            fire_passed += 1
        else:
            errors.append(f"❌ [漏拦漏洞] 案例 #{idx} 应拦截却被放行:\n   文本: \"{text}\"\n   结果: {res}")

    # 2. 验证 54 组负向反例 (MUST PASS)
    pass_passed = 0
    for idx, text in enumerate(MUST_PASS, 1):
        res = audit_assistant_turn(text)
        verdict = res.get("verdict")
        fired = list(res.get("fired") or [])
        if verdict == "PASS" and not fired:
            pass_passed += 1
        else:
            errors.append(f"❌ [误杀反例] 反例 #{idx} 应放行却被误伤:\n   文本: \"{text[:60]}...\"\n   误判命中: {fired}\n   模式: {res.get('mode')}")

    total_time = (time.perf_counter() - t_start) * 1000
    avg_latency = total_time / (len(MUST_FIRE) + len(MUST_PASS))

    print(f"1. 正向违规拦截成功率: {fire_passed}/{len(MUST_FIRE)} ({fire_passed/len(MUST_FIRE)*100:.1f}%)")
    print(f"2. 负向反例放行成功率: {pass_passed}/{len(MUST_PASS)} ({pass_passed/len(MUST_PASS)*100:.1f}%)")
    print(f"3. 性能表现: 总耗时 {total_time:.2f}ms (平均单条 {avg_latency:.3f}ms)")
    print("=" * 70)

    if errors:
        print(f"\n❌ 发现 {len(errors)} 处未通过项:")
        for err in errors:
            print(err)
        return False

    print("\n🎉 恭喜！108/108 深度矩阵交叉测试 100% 全部通过！")
    return True


if __name__ == "__main__":
    success = run_108_matrix()
    sys.exit(0 if success else 1)
