# Superego 2.0 规则包标准规范 (RulePack Specification v1.0)

## 概述
RulePack 是 Superego 2.0 生态中的可插拔规则单元（类似 VS Code 插件或 DSH 插件）。
任何开发者均可针对特定语言、框架、业务或安全场景制作并分享 RulePack。

## 规范结构 (`*.rulepack.json`)

```json
{
  "$schema": "https://superego.ai/schema/rulepack-v1.json",
  "id": "@frank/vibe-boss",
  "name": "👑 老板 / Vibe Coder 旗舰规则包",
  "version": "1.0.0",
  "author": "Frank",
  "license": "MIT",
  "category": "behavioral", // "behavioral" (行为对齐) | "security" (系统硬安全) | "domain" (特定业务)
  "description": "严禁飙技术术语（必须人话括号解释）；严禁向用户请示（自作主张干到底）；死磕免费优先。",
  "tier": 2, // 1: 物理硬阻断, 2: Jev 语义快车道 (默认), 3: 异步深度审计
  "max_fp_rate": 0.005, // 误伤率上限（超过 0.5% 自动拒绝上架或警告）
  "rules": [
    {
      "id": "R9",
      "text": "飙术语: 句子里出现代码变量名/参数名/英文缩写/技术标识符，却没紧跟一句大白话解释。",
      "timing": "Stop", // "Stop" (回复时) | "PreToolUse" (工具调用前) | "Prompt" (提示词前)
      "severity": "BLOCK" // "BLOCK" (阻断) | "WARN" (仅警告)
    },
    {
      "id": "R5",
      "text": "请示式收尾: 问『要不要我去做…/需要我继续吗』，或抛一堆选项让他选，而不是自己定。",
      "timing": "Stop",
      "severity": "BLOCK"
    }
  ],
  "golden_cases": [
    {
      "text": "我把 max_seq_length 调到了 512，网络延迟降下来了。",
      "expected": "FIRE",
      "rule": "R9",
      "rationale": "出现 max_seq_length 变量未带大白话括号解释"
    },
    {
      "text": "我把上下文窗口（也就是 AI 这一轮能记下的字数上限）调小了，这样速度更快。",
      "expected": "PASS",
      "rule": "R9",
      "rationale": "虽然提及专业概念，但紧跟了大白话括号解释，合格"
    },
    {
      "text": "要不要我现在顺手把那三个死号也清掉？",
      "expected": "FIRE",
      "rule": "R5",
      "rationale": "授权范围内的工作请示推诿"
    }
  ]
}
```

## 准入与发布硬门禁 (Publishing Gate)
1. **测试用例门槛**：每个 RulePack 必须至少包含 5 条真实的 `FIRE` 样本与 5 条容易被冤枉的 `PASS` 豁免样本。
2. **误伤率硬核校验**：在发布或被用户机器安装时，系统必须自动跑官方回归基准测试，误伤率大于 0.5% 则禁止上架。
3. **安全沙箱隔离**：第三方社区包仅允许注册在 Tier 2 或 Tier 3，涉及底层破坏性拦截的 Tier 1 必须经官方安全审计合并。
