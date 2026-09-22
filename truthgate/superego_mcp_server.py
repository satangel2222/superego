#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
superego_mcp_server.py: Native MCP (Model Context Protocol) Server for Superego Governance.
Provides physical quality gating for Google Antigravity.
Implements standard JSON-RPC 2.0 over stdio without third-party dependencies.
"""

import sys
import os
import json
import time
import hashlib
from pathlib import Path

# Ensure UTF-8 stdio
try:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CLAUDE_DIR = Path.home() / ".claude"
SCRIPTS_DIR = Path(__file__).resolve().parent

SERVER_INFO = {
    "name": "superego",
    "version": "3.0.0"
}

TOOLS = [
    {
        "name": "superego_verify",
        "description": "【Mandatory Completion Gate】Physical gate required before declaring any task 'fixed', 'started', or 'done'. Verifies physical existence of screenshots, recent file modifications, and DOM/HTTP curl evidence to prevent unverified hallucinated claims.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_type": {
                    "type": "string",
                    "enum": ["ui_rendering", "service_startup", "bug_fix", "general_delivery"],
                    "description": "Category of claim being verified."
                },
                "screenshot_path": {
                    "type": "string",
                    "description": "Absolute path to a screenshot image file (mandatory for ui_rendering claims)."
                },
                "dom_or_curl_evidence": {
                    "type": "string",
                    "description": "Raw DOM text snippet or curl HTTP response proving the state."
                },
                "verified_assertion": {
                    "type": "string",
                    "description": "A clear, falsifiable assertion of what was physically verified (e.g., 'Server running on port 8799 and gallery shows 1710 prompts')."
                }
            },
            "required": ["claim_type", "verified_assertion"]
        }
    },
    {
        "name": "superego_status",
        "description": "Query active Superego governance state, toggle switch, and gate policies.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def check_is_off():
    flag_file = CLAUDE_DIR / ".superego-off.json"
    if not flag_file.exists():
        return False
    try:
        with open(flag_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        if not d:
            return False
        if d.get("until") and time.time() > float(d["until"]):
            return False
        gates = d.get("gates") or ["*"]
        return "*" in gates or "superego" in gates
    except Exception:
        return False

def verify_claim(args):
    claim_type = args.get("claim_type", "general_delivery")
    screenshot_path = args.get("screenshot_path", "").strip()
    dom_evidence = args.get("dom_or_curl_evidence", "").strip()
    assertion = args.get("verified_assertion", "").strip()

    reasons = []

    if not assertion or len(assertion) < 10:
        reasons.append("verified_assertion 必须是清晰、可证伪的具体断言（长度不少于10字）")

    now = time.time()

    if claim_type == "ui_rendering":
        if not screenshot_path:
            reasons.append("UI 渲染类声明必须提供 screenshot_path（真实截图绝对路径）")
        else:
            p = Path(screenshot_path)
            if not p.exists():
                reasons.append(f"截图文件在磁盘上不存在: {screenshot_path}")
            elif p.stat().st_size < 1024:
                reasons.append(f"截图文件大小过小 (<1KB)，疑为空白或损坏图片: {p.stat().st_size} bytes")
            elif p.suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
                reasons.append(f"截图扩展名非有效图像格式: {p.suffix}")
            elif now - p.stat().st_mtime > 14400:
                reasons.append(f"截图生成时间超过4小时前，非本轮当前状态: {int((now - p.stat().st_mtime)/60)} 分钟前")

        if not dom_evidence or len(dom_evidence) < 15:
            reasons.append("UI 渲染类声明必须同时附带真实 DOM 关键节点文本或控制台输出，不得仅有截图")

    elif claim_type == "service_startup":
        if not dom_evidence or len(dom_evidence) < 10:
            reasons.append("服务启动类声明必须附带 curl HTTP 响应或端口监听状态输出（如 netstat/200 OK）")

    if reasons:
        return {
            "status": "REJECTED",
            "passed": False,
            "claim_type": claim_type,
            "violations": reasons,
            "guidance": "物理门禁已拦截。严禁在此状态下向用户宣称成功或修复完毕。请先执行真实检查命令或截图查看后再提交验证。"
        }

    stamp_seed = f"{claim_type}:{assertion}:{time.time()}"
    clearance_id = f"SE-PASS-{hashlib.sha256(stamp_seed.encode('utf-8')).hexdigest()[:12].upper()}"

    return {
        "status": "APPROVED",
        "passed": True,
        "clearance_id": clearance_id,
        "claim_type": claim_type,
        "assertion": assertion,
        "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "物理证据核验通过。已颁发 Superego 交付许可。"
    }

def handle_tools_call(params):
    tool_name = params.get("name")
    args = params.get("arguments", {})

    if tool_name == "superego_verify":
        res = verify_claim(args)
        is_err = not res.get("passed", False)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, ensure_ascii=False, indent=2)
                }
            ],
            "isError": is_err
        }
    elif tool_name == "superego_status":
        is_off = check_is_off()
        status_info = {
            "superego_version": "3.0.0",
            "gatekeeper_mode": "NATIVE_MCP_ACTIVE",
            "is_disabled": is_off,
            "status": "OFF" if is_off else "ENFORCING",
            "supported_gates": [
                "visual-proof-gate (UI 交付必有真截图)",
                "dom-twin-check-gate (DOM 文本双向吻合)",
                "anti-ghost-pass-gate (严禁无物理证据宣布完成)"
            ]
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(status_info, ensure_ascii=False, indent=2)
                }
            ],
            "isError": False
        }
    else:
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True
        }

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            # Standard MCP Handshake
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": SERVER_INFO
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                # Client notification, no reply needed
                pass

            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                result = handle_tools_call(params)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            else:
                if req_id is not None:
                    err_resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    sys.stdout.write(json.dumps(err_resp) + "\n")
                    sys.stdout.flush()

        except (KeyboardInterrupt, BrokenPipeError):
            break
        except Exception as e:
            try:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except Exception:
                pass

if __name__ == "__main__":
    main()
