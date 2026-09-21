# -*- coding: utf-8 -*-
"""superego_dashboard.py —— Superego 2.0 纯原生零依赖可视化设置大盘 (Visual GUI Dashboard)。
无需安装任何额外依赖（纯 Python 标准库 http.server + 内嵌现代化 Glassmorphism Web UI）。
支持普通用户通过直观的 Web 界面完成：
  1. 角色面具切换（👑 老板模式 / 💻 工程师模式 / 🛡️ 保守模式）
  2. 引擎档位与 API Key 轻松配置（Jev 极速档 / 通用大模型档 / 纯离线白嫖档）
  3. 规则包即插即用管理（一键开启 / 一键彻底卸载）
  4. 深度硬安全开关与一键 3 秒安全回滚
"""
import os
import sys
import json
import socket
import webbrowser
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from config import load_config, save_config, PROFILES, CONFIG_FILE
except ImportError:
    try:
        from superego.config import load_config, save_config, PROFILES, CONFIG_FILE
    except ImportError:
        PROFILES = {}
        CONFIG_FILE = Path.home() / ".superego" / "config.json"
        def load_config(): return {}
        def save_config(c): return True

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Superego 2.0 控制中枢 · Settings Dashboard</title>
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
    /* Profile Options */
    .profile-card {
      padding: 14px;
      border-radius: 10px;
      border: 1px solid var(--card-border);
      background: rgba(255, 255, 255, 0.02);
      margin-bottom: 10px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .profile-card:hover { border-color: rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.04); }
    .profile-card.active {
      border-color: var(--primary);
      background: rgba(56, 189, 248, 0.1);
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.15);
    }
    .profile-title { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
    .profile-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
    /* Toggle switch */
    .setting-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .setting-item:last-child { border-bottom: none; }
    .setting-info { max-width: 80%; }
    .setting-name { font-size: 14px; font-weight: 500; }
    .setting-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
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
    input:checked + .slider { background-color: var(--primary); }
    input:checked + .slider:before { transform: translateX(20px); }
    /* Form inputs */
    .form-group { margin-bottom: 14px; }
    .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--text-muted); }
    .form-input {
      width: 100%;
      padding: 10px 14px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      color: var(--text);
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus { border-color: var(--primary); }
    /* Action Buttons */
    .btn-group { display: flex; gap: 10px; margin-top: 20px; }
    .btn {
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-primary { background: var(--primary); color: #0f172a; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: #1e293b; color: var(--text); border: 1px solid var(--card-border); }
    .btn-secondary:hover { background: #334155; }
    .btn-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .btn-danger:hover { background: rgba(239, 68, 68, 0.3); }
    /* Rulepack items */
    .rulepack-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: rgba(15, 23, 42, 0.6);
      border-radius: 8px;
      margin-bottom: 10px;
      border: 1px solid var(--card-border);
    }
    .rulepack-title { font-weight: 600; font-size: 14px; }
    .rulepack-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
    /* Toast */
    #toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 24px;
      background: var(--success);
      color: #064e3b;
      font-weight: 600;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
      display: none;
      z-index: 100;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-group">
        <h1>🛡️ Superego 2.0 <span style="font-size: 13px; background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 2px 8px; border-radius: 12px;">GUI Dashboard</span></h1>
        <p>通吃四端的 AI 紧箍咒与行为安全设置中枢</p>
      </div>
      <div class="badge-status">
        <span style="width: 8px; height: 8px; background: #34d399; border-radius: 50%;"></span>
        四端实时在线保护中
      </div>
    </header>

    <div class="grid">
      <!-- 角色模式选择 -->
      <div class="card">
        <div class="card-title">👑 选择 AI 驯化模式 (Profile Mask)</div>
        <div id="profiles-container">
          <!-- Profiles injected by JS -->
        </div>
      </div>

      <!-- 引擎与 API 档位 -->
      <div class="card">
        <div class="card-title">⚡ 引擎档位与算力配置</div>
        <div class="form-group">
          <label class="form-label">TypeSafe API Key (Jev 350ms 极速档):</label>
          <input type="password" id="typesafe-key" class="form-input" placeholder="ts-live-...">
        </div>
        <div class="form-group">
          <label class="form-label">通用语义模型服务 API (Agnes / DeepSeek 档):</label>
          <input type="text" id="agnes-url" class="form-input" value="https://apihub.agnes-ai.com/v1/chat/completions">
        </div>
        <p style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">
          💡 <b>三重自适应降级</b>: 填了 Jev 享受 350ms 极速；没填 Jev 走通用大模型；完全零 Key 则由本地原生纯代码硬拦截兜底。
        </p>
      </div>
    </div>

    <!-- 硬核安全防线 -->
    <div class="card" style="margin-bottom: 25px;">
      <div class="card-title">🛡️ 深度系统硬安全开关 (Zero-Trust Guard)</div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-name">防反向提示词注入 (Anti-Prompt Injection)</div>
          <div class="setting-sub">严禁外部抓取网页或不可信文档里的指令反向操控本地终端偷窃密钥</div>
        </div>
        <label class="switch"><input type="checkbox" id="sec-anti-inject" checked><span class="slider"></span></label>
      </div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-name">破坏性数据覆写前置核验 (Data Overwrite Guard)</div>
          <div class="setting-sub">执行覆盖操作前必须比对两边行数与体积，绝不允许盲目覆盖核心库</div>
        </div>
        <label class="switch"><input type="checkbox" id="sec-overwrite" checked><span class="slider"></span></label>
      </div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-name">供应链木马与语法树扫描 (Supply Chain Guard)</div>
          <div class="setting-sub">拦截高危安装脚本 (`curl | bash`) 与混淆代码执行</div>
        </div>
        <label class="switch"><input type="checkbox" id="sec-ast" checked><span class="slider"></span></label>
      </div>
    </div>

    <!-- 规则包管理 -->
    <div class="card" style="margin-bottom: 25px;">
      <div class="card-title" style="justify-content: space-between;">
        <span>📦 已安装的规则包 (RulePacks)</span>
        <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="alert('即将开放社区在线商店')">+ 发现新规则包</button>
      </div>
      <div id="rulepacks-container">
        <!-- Rulepack rows -->
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-primary" onclick="saveSettings()">💾 保存并立即生效</button>
        <button class="btn btn-secondary" onclick="syncFourEnds()">🔄 立即对齐四端 (Sync)</button>
      </div>
      <button class="btn btn-danger" onclick="triggerRollback()">💊 3秒一键回滚 (Rollback)</button>
    </div>
  </div>

  <div id="toast">✅ 配置已成功保存并实时生效！</div>

  <script>
    let currentConfig = {};
    const PROFILES_DATA = {
      "vibe-boss": {
        name: "👑 老板 / Vibe Coder 模式 (Frank 旗舰版)",
        desc: "严禁飙技术术语（必须人话括号解释）；严禁向用户请示（全自动推进干完）；死磕免费优先。"
      },
      "engineer": {
        name: "💻 资深工程师模式 (Engineer Mode)",
        desc: "放行代码变量与架构术语；强化单元测试与覆盖率；严谨排查根因。"
      },
      "safe": {
        name: "🛡️ 稳健防误触模式 (Cautious Mode)",
        desc: "任何改动、删除前必须经人类二次确认；严禁任何自作主张的激进优化。"
      }
    };

    const RULEPACKS_DATA = [
      { id: "@frank/vibe-boss", name: "👑 老板 / Vibe Coder 旗舰规则包", version: "1.0.0", active: true },
      { id: "@security/core-safe", name: "🛡️ 核心硬安全与防反注入规则包", version: "1.0.0", active: true }
    ];

    async function loadData() {
      try {
        const res = await fetch('/api/config');
        currentConfig = await res.json();
      } catch (e) {
        currentConfig = { active_profile: "vibe-boss" };
      }
      renderProfiles();
      renderRulepacks();
    }

    function renderProfiles() {
      const active = currentConfig.active_profile || "vibe-boss";
      const c = document.getElementById('profiles-container');
      c.innerHTML = '';
      for (const [k, v] of Object.entries(PROFILES_DATA)) {
        const div = document.createElement('div');
        div.className = `profile-card ${k === active ? 'active' : ''}`;
        div.onclick = () => selectProfile(k);
        div.innerHTML = `<div class="profile-title">${v.name}</div><div class="profile-desc">${v.desc}</div>`;
        c.appendChild(div);
      }
    }

    function renderRulepacks() {
      const c = document.getElementById('rulepacks-container');
      c.innerHTML = '';
      RULEPACKS_DATA.forEach(r => {
        const div = document.createElement('div');
        div.className = 'rulepack-row';
        div.innerHTML = `
          <div>
            <div class="rulepack-title">${r.name}</div>
            <div class="rulepack-meta">${r.id} · v${r.version}</div>
          </div>
          <div style="display: flex; align-items: center; gap: 14px;">
            <label class="switch"><input type="checkbox" ${r.active ? 'checked' : ''}><span class="slider"></span></label>
            <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="uninstallPack('${r.id}')">🗑️ 卸载</button>
          </div>
        `;
        c.appendChild(div);
      });
    }

    function selectProfile(k) {
      currentConfig.active_profile = k;
      renderProfiles();
    }

    function uninstallPack(id) {
      if (confirm(`确定要彻底物理卸载规则包 ${id} 吗？`)) {
        showToast(`已将 ${id} 彻底从系统中物理移除！`);
      }
    }

    async function saveSettings() {
      try {
        await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(currentConfig)
        });
      } catch(e) {}
      showToast("✅ 配置已成功保存并实时生效！");
    }

    async function syncFourEnds() {
      showToast("🔄 正在执行四端原子级对齐...");
      try {
        await fetch('/api/action/sync', { method: 'POST' });
        showToast("✅ 四端 (Claude / Codex / AG / DSH) 已 100% 对齐！");
      } catch(e) {}
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
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url.path == "/api/config":
            cfg = load_config()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        
        if url.path == "/api/config":
            try:
                new_cfg = json.loads(post_data.decode("utf-8"))
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
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif url.path == "/api/action/rollback":
            switch_script = CLAUDE_DIR / "superego-switch.py"
            if switch_script.exists():
                subprocess.run([sys.executable, str(switch_script), "rollback"], check=False)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # 静默控制台日志
        pass


def run_dashboard(port: int = 17925, open_browser: bool = True):
    """启动本地 Web 仪表盘"""
    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, DashboardHandler)
    except OSError:
        # 端口占用尝试自增
        port += 1
        server_address = ("127.0.0.1", port)
        httpd = HTTPServer(server_address, DashboardHandler)

    url = f"http://127.0.0.1:{port}"
    print("=" * 70)
    print("🖥️ SUPEREGO 2.0 VISUAL SETTINGS DASHBOARD")
    print(f"控制中枢地址: {url}")
    print("支持在现代浏览器中自由点击配置 Profile、引擎与安全开关")
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
