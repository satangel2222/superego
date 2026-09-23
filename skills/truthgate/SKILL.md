---
name: truthgate
description: >-
  Manage and inspect the TruthGate 1.0 (formerly Superego 3.0) critic, gatekeeper, and self-correction system.
  Activate whenever the user mentions 'truthgate', 'tg', 'superego', '关闸', '开闸', asks to toggle or check
  governance status ('tg on', 'tg off', 'tg status', 'superego on', 'superego off', 'superego status'), or asks why a gate fired.
---

# TruthGate 1.0 (formerly Superego) Control & Governance Skill

This skill allows AI agents across platforms (Claude Code, OpenAI Codex, Google Antigravity, and DSH) to check, toggle, and inspect the unified **TruthGate 1.0 (formerly Superego 3.0)** quality and gatekeeping system.

## Ironclad Red Lines
1. **Never steal focus**: All background commands must execute without opening foreground popups or interrupting the user's typing.
2. **Single Source of Truth**: State is read from and written to `~/.claude/.superego-off.json` (or via `superego-toggle.py`). Never invent conflicting state files.

---

## Commands & Actions

### 1. Check Status
When the user asks "truthgate 状态", "superego 状态", "现在开着还是关着", or "tg status":
Run:
```bash
tg status
# 或：
python -m truthgate status
```
Or if using the toggle script:
```bash
python ~/.claude/superego-toggle.py status
```
Output the exact status to the user and summarize whether TruthGate / Superego is currently active or disabled.

### 2. Turn Off Temporarily (Current Session Only)
When the user asks "关掉 truthgate", "关掉 superego", "tg off", or "superego off":
Run:
```bash
python ~/.claude/superego-toggle.py off
```
*Note: This only disables the gatekeeper for the current conversation. When switching conversations, it automatically restores.*

### 3. Turn Off with Timer
When the user asks "关 30 分钟", "tg off 30m", or "superego off 30m":
Run:
```bash
python ~/.claude/superego-toggle.py off 30m
```

### 4. Turn Off Globally
When the user asks "全局关掉", "tg off --global", or "superego off --global":
Run:
```bash
python ~/.claude/superego-toggle.py off --global
```

### 5. Restore / Turn On
When the user asks "打开 truthgate", "打开 superego", "恢复", "tg on", or "superego on":
Run:
```bash
python ~/.claude/superego-toggle.py on
```

---

## Active Gates Enforced on Antigravity
The Antigravity engine actively enforces gates via Native MCP (`superego_verify`) and the background watchdog `ag_watch.py`:
- **`visual-proof-gate`**: Blocks completion (`decision: continue`) if UI/window/page health or completion is claimed without reading a screenshot or image in the turn.
- **`false-done-gate`**: Blocks unverified victory declarations without proof.
- **`honest-scope-assertion-gate`**: Prohibits false exhaustive testing or file reading claims.
- **`internal-four-ends-and-six-universes-gate` (R10)**: 严禁坐井观天与单端断言。凡断定功能有无、历史需求、既有工具或SOTA对标，必须先经 `internal_four_ends.py` 全量穷尽内部四端（Claude 70项目 + Codex + AG + 本地200+技能工具库），并在外部六宇宙中进行双向交叉核对。违规出示单端妄断者当场打回。
- **`ephemeral-process-leak-gate`**: Intercepts unmanaged browser launches and uncontained local server processes to prevent zombie leaks.
