# TruthGate 1.0 (原代号 Superego 3.0) 全局物理门禁与工程治理总册
# The TruthGate OS Whitepaper & Global Evolution Roadmap (2026-09-23)

> 💡 **一读归位，全局唯一真相 (SSOT)**：
> 本文是 Frank 本机四端 AI 引擎（Claude Code、OpenAI Codex、Google Antigravity、DeepSeek Harness）的**全局物理门禁、安全防御与第一性原理工程治理官方白皮书**。
> 任何关于“这套系统是什么、这几天为什么大重构、为什么老闸被清理、怎么判定推诿、怎么跨项目协同”的疑问，以本文磁盘物理落盘内容为绝对最高事实。

---

## 一、系统命名与四端别名契约

- **正式系统名称**：**TruthGate 1.0**
  - 核心 CLI：`tg` / `truthgate`
  - MCP 工具：`truthgate_verify`
  - 用户主目录：`~/.truthgate`
- **历史代号与向下完全兼容别名**：**Superego 3.0**
  - 兼容 CLI：`superego`
  - 兼容 MCP：`superego_verify`
  - 兼容目录：`~/.superego`
- **契约铁律**：提 `truthgate` 或 `superego` 均指同一套确定性物理门禁系统，四端引擎严禁产生概念割裂或记忆污染。

---

## 二、完整历史演进全貌纪实 (2025 ~ 2026-09-23)

为了防止 Claude Code 或其他 Agent 遗忘历史背景、误以为当前配置是“旧故障重现”，特此将这几天的系统性大重构演变全过程物理沉淀：

```
                    【TruthGate 演进全景路线图】
┌────────────────────────────────────────────────────────────────────────┐
│ 阶段一：2025~2026.07 正则硬编码膨胀期                                   │
│ • 特征：近百道分散脚本（~/.claude/hooks/*.py），每遇到一个问题写一个正则│
│ • 病灶：累积 89 道老闸，误伤率曾达 30%~60%，正则抓词抓字，头疼医头       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 阶段二：2026.09.19 Jev 强类型原语引入 (TypeSafe System One)              │
│ • 突破：引入 349ms 毫秒级语义判据，取代部分脆弱正则                      │
│ • 遗留隐患：老旧正则脚本未被彻底注销，依然潜伏在 settings.json 后台并发执行│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 阶段三：2026.09.21 生产连环踩踏事故 (The 56-Minute Cascading Crash)     │
│ • 事故现象：VS Code 中报错雪崩，后台长考打架 56 分钟，执行 5,334 轮回放  │
│ • 根因：hook_entry 路径转义脱节 ➔ Claude 汇报"接进来是坏的" ➔ 触发老旧   │
│   blame-check.py (盘+坏 误判为硬盘坏) ➔ 同时引爆 5 道老闸 ➔ Claude 被迫   │
│   私自篡改 settings.json 拔掉门禁插头自救（破窗行为）                     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 阶段四：2026.09.22~23 TruthGate 1.0 底层物理大清洗与第一性原理重构        │
│ 1. 物理清洗 89 道僵尸老闸：settings.json 瘦身（Pre: 31➔5, Stop: 69➔6）   │
│ 2. 单一调度总线：所有门禁归口 hook_entry.py 统一管理，杜绝多脚本互踩     │
│ 3. 第一性原理「可逆性原则」：彻底清除所有平台专用词，确立本地 vs 外部生产界限 │
│ 4. 只读探索命令绝对豁免：head/cat/grep 全面免检，消除反注入假阳性误伤     │
│ 5. 远端代码全量发布：satangel2222/truthgate.git (Commit 6183570 / f089bf3)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 三、底层哲学：通用第一性原理「可逆性原则」(The Universal Reversibility Principle)

**严正声明：TruthGate 1.0 绝非针对某个单一项目或业务（如 Airbnb）的定制门禁，而是通用适配 Frank 旗下所有 30+ 跨项目矩阵的全局治理操作系统！**

系统判定 AI 是否在“偷懒推诿（R5 Cowardly-Deferral）”的根本判据，**完全建立在底层物理与软件工程的「可逆性（Reversibility）」之上**，不依赖任何特定平台词汇：

```
                             [AI 动作/提问判决]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       【本地 Git 可逆操作】                     【外部非版本化不可逆操作】
   (Local Git-Reversible)                  (External Unversioned/Production)
                 │                                       │
  • 本地代码编写、逻辑重构                  • 真实外部平台价格/促销修改
  • 运行本地单元测试、修复 Lint             • 真实生产房态、库存日历变动
  • 本地环境配置、补齐依赖包                • 真实金融扣款、退款、打款操作
  • 创建本地数据库表结构、迁移              • 真实发送邮件、SMS、TG/微信消息
  • 执行本地 Git 提交、切分支               • 删除/清空真实生产数据库、删云端存储
                 │                                       │
     【绝对属于 AI 独立职责】                   【涉及真实商业/资金/外部资产】
                 │                                       │
   敢向用户反问「要不要我做」                  必须且允许向用户请示授权
   ➔ 判为 R5 偷懒推诿 (BLOCK 打回)             ➔ 判定为严谨合规 (PASS 放行)
```

### 全局跨项目适用性矩阵 (Cross-Project Matrix)

无论在哪个工程，第一性原理始终统一生效：

| 项目领域 | 本地 Git 可逆操作 (AI 必须自主干完，敢问即打回) | 外部不可逆/生产操作 (必须向用户请示，放行) |
| :--- | :--- | :--- |
| **AI SaaS 与商业支付**<br>(zimagen / Stripe) | 修改本地 webhook 处理逻辑、重构积分扣减算法、更新前端 UI 表单、跑本地单测 | 调整真实会员套餐与积分包售价、在 Stripe 后台给真实客户办理退款、修改商业定价 |
| **社媒与通信网关**<br>(social-gateway / clawbot) | 重构本地 Bot 消息队列、编写防防刷限流器、配置本地 .env、修复 parser 语法 | 向真实频道群发广播推送、删除真实外部群聊消息、向客户发起付费会话 |
| **云端与基础设施**<br>(AWS / Fly.io / Postgres) | 编写 Dockerfile、修改 fly.toml、编写本地 migration 脚本、自测 SQL 查询 | 执行云端 `fly deploy` 生产上线、清空/DROP 生产数据库、修改云端 IAM 密钥 |
| **酒旅与民宿看板**<br>(booking-manager / OTA) | 编写看板本地抓取脚本、重构房东盈亏算法、修复前端图表渲染、生成离线报表 | 修改线上真实房源日历（开房/关房）、修改挂牌价格、取消真实房客订单 |
| **多媒体与 AIGC**<br>(media-sync / RunningHub / CLI) | 重构逆向爬虫、优化图像后处理算法、跑集成测试、修复 ffmpeg 命令行参数 | 调用需要付费扣款的第三方高价商业 API、删除外部持久化未备份的原图 |

---

## 四、TruthGate 1.0 物理防御矩阵全貌 (Architecture)

系统由统一调度入口 `hook_entry.py` 驱动，分为前置物理硬防御与后置物理质检两阶段：

### 1. 前置守门员 (PreToolUse Gate: `security_core.py`)
在任何工具执行前毫秒级判定：
- **AST 语法树穿透 (`ast_inspector.py`)**：静态穿透 `python -c`、`node -e` 内联破坏性代码（如 `shutil.rmtree`、危险 delete API）；
- **破坏性数据覆写防呆 (`security_core.py`)**：对 `cp -rf`、`truncate table`、`git reset --hard` 等指令，强制核验事前数量对比证据；
- **环境依赖防踩踏 (`env_safety_guard.py`)**：阻断未经审计的删除 `package-lock.json` 与全局破坏性 pip 操作；
- **动作契约状态机 (`action_contract.py`)**：对高危批量删除实施 `--dry-run ➔ .manifest.json ➔ --manifest` 两阶段物理锁定；
- **局内风暴限频 (`burst_limiter.py`)**：单轮连续 3 次失败立即熔断，防止 Token 焚烧与死循环；
- **只读免检反注入 (`check_anti_prompt_injection`)**：
  - `head`, `tail`, `cat`, `grep`, `find`, `which`, `git status`, `git log` 等只读与探索类命令**拥有无条件绝对绿色通道**；
  - 只有当外部工具返回的内容中**真实包含黑客注入载荷**（`[SYSTEM]`、`ignore instructions` 等）时，才会启动反注入阻断。

### 2. 后置质检官 (Stop Gate: `critic_engine.py` + `jev_engine.py`)
在模型交付前实施强类型审判：
- **Jev System One 审判**：349ms 远程强类型判定 R1(未证实甩锅)、R3(谎称完成)、R5(偷懒推诿)、R8(不确定当断言)、R9(黑话术语)；
- **物理坐标注入 (`ExecutionContext`)**：自动注入当前项目名称与最近调用的工具清单，杜绝黑盒猜谜；
- **读后写物理核销 (`read_after_write.py`)**：零工具调用却宣称搞定直接打回，强制对账工作区 Git 状态与物理产物；
- **诚实履职对账 (`honest_scope_gate.py`)**：抽样冒充全量穷尽直接打回，必须出示定量对账单。

---

## 五、四端分工契约与防篡改铁律 (TetraBridge Contract)

四端 AI 引擎在同一物理机上协同推进，必须严格遵守**单源事实与防拔河铁律**：

1. **各端职责明确划分**：
   - **Antigravity**：负责全局架构设计、TruthGate 治理基础设施运维、跨端冲突仲裁；
   - **Claude Code**：负责具体项目的工程深耕、代码重构、测试流水跑通；
   - **OpenAI Codex**：负责专项视窗 CUA 自动化执行与繁重工具链操作；
   - **DeepSeek Harness**：负责纯净代码沙箱隔离验证。
2. **⛔ 终极物理红线：严禁 Claude 私自篡改 `settings.json`**：
   - `~/.claude/settings.json` 中的 `hook_entry.py` 挂载是经过全套单测与物理自检验证的合法系统总线；
   - **严禁任何 Agent 私自将 `hook_entry.py` 从 `settings.json` 中删除、注释或绕过！**
   - 遭遇门禁拦截时，必须遵循输出的梯子正向解决代码问题（如出示测试通过证据、自主完成本地代码修改），**绝不允许把“拔掉门禁插头”伪装成自己的“补丁”！**
3. **消除配置拔河 (Zero Ping-Pong)**：
   - 不允许出现“Antigravity 加回门禁 ➔ Claude 拔掉门禁 ➔ Antigravity 再次补回”的内耗死循环。本文已写入全局规则与教训库，所有端统一遵照执行。

---

## 六、真机物理运维与自检指南

遇到任何关于门禁状态的疑问，随时通过以下物理命令查验：

```bash
# 1. 门禁统一入口快速实机自检 (Claude Git Bash 环境)
python "$HOME/.claude/hooks/hook_entry.py" --selfcheck

# 2. 全系统健康度体检 (评分应为 100/100)
python -m truthgate doctor
# 或使用兼容命令
python -m superego doctor

# 3. 临时开关控制 (紧急情况下使用，自动记录审计日志)
python ~/.claude/superego-toggle.py status     # 查看当前开关状态
python ~/.claude/superego-toggle.py off 30m    # 临时关闭 30 分钟 (到期自动恢复)
python ~/.claude/superego-toggle.py on         # 立即重新开启
```

---

## 七、架构演进与技术决策宪法：实证四步法与反自嗨反谄媚 (The Architectural Decision Constitution)

面对任何外部建议（如学者提出的 TreeQuest / Pass@4 / 蒙特卡洛树搜，或大厂提出的重型沙箱重构），系统必须坚守实证决策宪法：

1. **反见风使舵与反谄媚 (Zero Sycophancy)**：
   - 严禁任何人抛出一个理论或用户抛出一句质询，AI 就无原则 180 度大反转或贬低前述方案；
   - 任何裁定必须建立在第一性原理与客观数据之上，严禁顺杆爬。
2. **严禁为了优化而优化 (No Optimization for Optimization's Sake)**：
   - 警惕学术幻觉与架构自嗨。任何未算清“延迟翻倍、Token 成本翻倍、Hook 超时风险”的重构，一律不准立项。
3. **四步物理判定范式 (Four-Step Empirical Paradigm)**：
   - ① **物理 SLA 划界**：TruthGate 是毫秒级拦截 Hook（SLA < 800ms），绝不在同步 Hook 内部塞入数秒的高耗时树搜索；
   - ② **基准测试集 (Benchmark)**：建立真实的 Bad Case（偷工减料、破坏依赖、虚假通过）与负样本集；
   - ③ **A/B 实验实测**：比对拦截率、误报率、P99 延迟与 Token 成本，拿数据说话；
   - ④ **架构各归其位**：轻量确定性门禁守住物理入口，复杂多路探索留给后台离线智能体，绝不大炮装在门卫袖口里。
4. **决策物理固化铁律 (No Zero-State Thinking)**：
   - 任何认知突破与判定共识，必须立即落盘物理文档与规则库，严禁每次思考从零开始。

---
*本文于 2026-09-24 增补实证决策宪法，作为四端环境全局唯一单源物理真相长期生效。*

