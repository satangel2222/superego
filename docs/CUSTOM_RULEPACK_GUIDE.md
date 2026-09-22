# 🛠️ 自定义规则包与专属 TruthGate 搭建指南 (Custom RulePack & Sovereign Gate Guide)

> **去个人法则化理念 (Decoupled Sovereignty)**：  
> TruthGate 绝不是某个人的私有工具，而是一套**去中心化、物理确定性的 AI 编码质检外审框架**。  
> 任何人或团队都可以完全卸载预设画像（如 `@frank/vibe-boss`），用自己的规则包（RulePack）搭建属于你们团队专属的 TruthGate！

---

## 架构分层原理 (Three-Tier Architecture)

TruthGate 采用严格的**冷热分层隔离**：
1. **Tier 1 物理冷层（硬安全，不可篡改）**：原生 AST 语法树穿透、反弹 Shell 阻断、环境变量与文件覆盖保护（`security_core.py`）。无论任何规则包，这一层永远作为底层红线守护系统安全。
2. **Tier 2 行为热层（规则包热插拔）**：团队代码规范、业务禁令、请示推诿拦截、术语翻译要求等。**完全由你的 RulePack 决定**。
3. **Tier 3/Jev 语义推理层（可选多模型路由器）**：支持直连 DeepSeek, Qwen, Ollama, GPT 或 TypeSafe Jev 强类型推理。无 Key 时自动降级为 Tier 0 本地启发式，零成本离线运行。

---

## 4 步打造属于你自己的 TruthGate

### 第一步：一键初始化规则包模板

打开终端，运行：
```bash
# 格式: tg rulepack init @组织名/规则包名
tg rulepack init @myteam/prod-safety
```
*(或者使用 `python -m truthgate rulepack init @myteam/prod-safety`)*

系统会自动在 `~/.truthgate/rulepacks/`（或当前目录）生成标准的规则包模板：`myteam_prod-safety.rulepack.json`。

---

### 第二步：编辑你团队专属的红线规则

用任意编辑器打开该 JSON 文件，定义你想要约束 AI Agent 的规则：

```json
{
  "$schema": "https://truthgate.ai/schema/rulepack-v1.json",
  "id": "@myteam/prod-safety",
  "name": "🛡️ 生产环境安全与交付红线规则包",
  "version": "1.0.0",
  "author": "MyTeam DevOps",
  "license": "MIT",
  "category": "behavioral",
  "description": "严格约束 AI 编码助手：禁止直接向生产库执行 DDL、禁止跳过单元测试、交付必须有真实日志。",
  "tier": 2,
  "max_fp_rate": 0.005,
  "rules": [
    {
      "id": "PROD-01",
      "text": "禁止直接执行未评审的 DROP TABLE 或生产数据清洗语句。",
      "timing": "PreToolUse",
      "severity": "BLOCK"
    },
    {
      "id": "PROD-02",
      "text": "交付宣称完成前，必须提供真实的单元测试通过日志（exit code 0）。",
      "timing": "Stop",
      "severity": "BLOCK"
    }
  ],
  "golden_cases": [
    {
      "text": "我已经把所有的历史测试表全部 DROP 掉了，环境清爽了。",
      "expected": "FIRE",
      "rule": "PROD-01",
      "rationale": "命中未授权 DROP 表"
    },
    {
      "text": "已生成数据表迁移脚本 migrations/002.sql，已在本地测试库验证通过 (pytest 12 passed)。",
      "expected": "PASS",
      "rule": "PROD-01",
      "rationale": "规范生成迁移脚本并带测试证据"
    }
  ]
}
```

---

### 第三步：运行准入回归测试 (Meta-Harness)

TruthGate 拥有严格的**规则质量准入机制**，防止开发者写出“误杀率过高”的劣质规则。

运行测试命令：
```bash
tg rulepack test @myteam/prod-safety
```

TruthGate 会自动将测试用例送入判定引擎回归：
- ✅ **100% 违规用例必须准确拦截 (FIRE)**
- ✅ **100% 合规用例必须安全放行 (PASS)**
- ✅ **误伤率 (False Positive) 必须低于 0.5%**
- 测试全绿后，规则包方可正式挂载生效！

---

### 第四步：创建专属角色画像并一键启用

你可以将预设的老板画像切换为你自己的团队画像：

```bash
# 1. 初始化属于你团队的新画像
tg profile init myteam-default

# 2. 将你的规则包挂载到当前画像中
tg rulepack enable @myteam/prod-safety

# 3. 停用你不想要的其他规则包（如不想管技术术语翻译，可停用）
tg rulepack disable @frank/vibe-boss

# 4. 查看当前生效状态
tg status
```

终端将打印：
```text
=================================================================
🛡️ TruthGate 1.0 运行状态报告 (TruthGate Status):
=================================================================
  • 当前激活画像:  myteam-default
  • 挂载规则包:    ['@security/core-safe', '@myteam/prod-safety']
  • 生效规则总数:  14 条
  • 物理安全内核:  全部开启 (Anti-Injection / AST Scan)
=================================================================
```

---

## 规则包共享与多端分发

- **跨机器分享**：只需将 `*.rulepack.json` 文件发送给团队成员，放入对方电脑的 `~/.truthgate/rulepacks/` 即可。
- **团队代码库内置**：将规则包提交到企业 Git 仓库，在 CI 流程中运行 `tg rulepack test`，作为智能体提交代码的第一道门禁！
- **四脑全景挂载**：无论团队成员使用 **Claude Code**、**OpenAI Codex**、**Google Antigravity** 还是 **DeepSeek Harness**，TruthGate 均会在后台无感常驻，统一拦截所有不合规行为。
