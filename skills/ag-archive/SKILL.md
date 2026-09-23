---
name: ag-archive
description: >-
  Query and inspect past Antigravity and Claude conversation history, architectural decisions, past configurations (such as CC Switch, RunningHub, Superego, project evolutions), and recall previous context. Use whenever the user mentions '之前', '上次', '做过没做过', asks about past discussions, historical context, or when verifying whether a topic was previously addressed before asserting facts.
---

# Antigravity 记忆检索与历史调阅 (ag-archive)

Antigravity 专属的离线全量对话记忆系统，支持 Antigravity 专属脑库（`D:\chat-archive-db\ag-brain.db`）、Codex 专属脑库（`D:\chat-archive-db\codex-brain.db`）、DeepSeek Harness 专属脑库（`D:\chat-archive-db\dsh-brain.db`）与 Claude 历史脑库（`D:\chat-archive-db\brain.db`）的毫秒级全文检索。

## 铁律与原则

1. **先查证，后发言**：凡是涉及“之前”、“上次”、“做过没做过”、“CC Switch”、“配置细节”、“历史经验”，或用户询问历史决策时，**必须优先在执行操作前运行检索命令**，把历史原话与时间线搞清楚，严禁凭空失忆回答“没有记录”或“没做过”。
2. **零污染隔离红线**：
   - 写入操作由专属守护（`ag_watch.py`）严格独立写入各自脑库（`ag-brain.db`, `codex-brain.db`, `dsh-brain.db`）。
   - 对 Claude 的 `D:\chat-archive-db\brain.db` **严格只读**，绝不进行任何修改。
   - 对 DSH 的运行时执行 **100% 纯只读旁路监听**，零侵入、零冲突。

## 常用命令

### 1. 全平台联合交叉检索（物理默认：Antigravity + Codex + DSH + Claude 四脑全量 Cross-Check）
> [!IMPORTANT]
> 默认不加参数即全平台联合检索！严禁只查单平台，否则必将因信息孤岛漏查其他平台的端口占用、双实例与历史决策！
```bash
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py search "<关键词>" --all
```

### 2. 定向指定单平台过滤（选配）
```bash
# 仅查 Antigravity:
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py search "<关键词>" --only-ag

# 仅查 DeepSeek Harness (DSH):
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py search "<关键词>" --dsh

# 仅查 OpenAI Codex:
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py search "<关键词>" --only-codex

# 仅查 Claude (严格只读):
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py search "<关键词>" --only-claude
```

### 3. DSH 专属深度调阅与状态感知
```bash
# 查看 DSH 最近活跃的会话清单（含模型选型、Token与首问）：
py -3 C:\Users\Casp\.gemini\antigravity\scripts\dsh_archive.py recent 10

# 调阅 DSH 指定会话的完整多轮答复与 Todos：
py -3 C:\Users\Casp\.gemini\antigravity\scripts\dsh_archive.py session <会话ID前缀>

# 查阅 DSH 脑库资产统计：
py -3 C:\Users\Casp\.gemini\antigravity\scripts\dsh_archive.py stats
```

### 4. 调阅 Antigravity 会话完整内容
```bash
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py session <会话ID前缀>
# 仅看用户发言：
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py session <会话ID前缀> --user
```

### 5. 查看最近活跃会话与脑库统计
```bash
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py recent 10
py -3 C:\Users\Casp\.gemini\antigravity\scripts\ag_archive.py stats
```

