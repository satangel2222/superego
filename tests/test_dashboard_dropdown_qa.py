# -*- coding: utf-8 -*-
"""test_dashboard_dropdown_qa.py —— 使用 Playwright 自动化测试仪表盘外审模型下拉切换联动"""
import time
import threading
from pathlib import Path
from http.server import HTTPServer
from playwright.sync_api import sync_playwright

import sys
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from truthgate.dashboard import DashboardHandler

EXPECTED_MAP = {
    'agnes': ('https://apihub.agnes-ai.com/v1', 'agnes-3.0-flash'),
    'openai': ('https://api.openai.com/v1', 'gpt-5.6-sol'),
    'gemini': ('https://generativelanguage.googleapis.com/v1beta/openai', 'gemini-3.8-flash'),
    'glm': ('https://open.bigmodel.cn/api/paas/v4', 'glm-4-flash'),
    'deepseek': ('https://api.deepseek.com/v1', 'deepseek-chat'),
    'openai_compatible': ('https://your-relay.com/v1', 'gpt-5.6-sol'),
    'ollama': ('http://localhost:11434/v1', 'qwen2.5:7b'),
    'local_heuristic': ('local', 'local_ast_tier0'),
}

def test_dropdown_dynamic_mapping():
    port = 17989
    server = HTTPServer(('127.0.0.1', port), DashboardHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f'http://127.0.0.1:{port}/dashboard')
            page.wait_for_selector('#critic-provider')

            for provider, (exp_base, exp_model) in EXPECTED_MAP.items():
                page.select_option('#critic-provider', provider)
                cur_base = page.input_value('#critic-base-url')
                cur_model = page.input_value('#critic-model')

                assert cur_base == exp_base, f"Provider {provider} 切换失败: 期望 Base URL {exp_base}, 实际 {cur_base}"
                assert cur_model == exp_model, f"Provider {provider} 切换失败: 期望 Model {exp_model}, 实际 {cur_model}"
                print(f"  ✅ [PASS] 下拉选项: {provider} -> Base: {cur_base} | Model: {cur_model}")

            browser.close()
            print("\n🎉 自动化 QA 验证：所有 8 项外审模型下拉切换动态联动全部通过！")
    finally:
        server.shutdown()

if __name__ == '__main__':
    test_dropdown_dynamic_mapping()
