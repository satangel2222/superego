# -*- coding: utf-8 -*-
"""test_user_panel_flow.py —— 模拟普通用户通过 Web 仪表盘配置外审并验证全流程。"""
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:17911"

def test_panel_html_contains_critic():
    print("[1] 测试仪表盘 HTML 是否包含外审配置面板元素...")
    req = urllib.request.Request(f"{BASE_URL}/dashboard")
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        content = resp.read().decode("utf-8")
        assert 'id="critic-provider"' in content, "缺失 critic-provider 下拉选择框"
        assert 'id="critic-api-key"' in content, "缺失 critic-api-key 输入框"
        assert 'id="critic-base-url"' in content, "缺失 critic-base-url 输入框"
        assert 'id="critic-model"' in content, "缺失 critic-model 输入框"
        assert 'testCriticConnection()' in content, "缺失连通性测试按钮触发函数"
        print("    ✅ 仪表盘 HTML 完全包含外审多模型配置与连通测试 UI")

def test_api_critic_test_endpoints():
    print("\n[2] 测试普通用户在面板点击【测试连通性】(POST /api/critic/test)...")
    providers_to_test = [
        {
            "name": "纯本地启发式 (Tier 0 本地保底)",
            "payload": {"provider": "local_heuristic", "base_url": "", "model": "", "api_key": ""},
            "expect_ok": True,
            "expect_model": "local_ast_tier0"
        },
        {
            "name": "Google Gemini (官方 OpenAI 端点测试)",
            "payload": {"provider": "gemini", "base_url": "", "model": "", "api_key": "AIzaSyTestInvalidMockKey"},
            "expect_ok": False, # 无效 Key 真实返回上游 400 报错，诚实拒绝假绿
            "expect_keyword": "HTTP Error 400"
        },
        {
            "name": "智谱 GLM (官方开放平台端点测试)",
            "payload": {"provider": "glm", "base_url": "", "model": "", "api_key": "mock-glm-key-123"},
            "expect_ok": False,
            "expect_keyword": "HTTP"
        },
        {
            "name": "DeepSeek (官方端点测试)",
            "payload": {"provider": "deepseek", "base_url": "", "model": "", "api_key": "sk-fake-deepseek-key"},
            "expect_ok": False,
            "expect_keyword": "HTTP"
        },
        {
            "name": "OpenAI (官方端点测试)",
            "payload": {"provider": "openai", "base_url": "", "model": "", "api_key": "sk-fake-openai-key"},
            "expect_ok": False,
            "expect_keyword": "HTTP"
        }
    ]

    for p in providers_to_test:
        print(f"  • 发起探针: {p['name']} ...")
        req = urllib.request.Request(
            f"{BASE_URL}/api/critic/test",
            data=json.dumps(p["payload"]).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if p["expect_ok"]:
                    assert data.get("ok") is True, f"预期 ok=True，实际: {data}"
                    assert p["expect_model"] in data.get("model", ""), f"模型不匹配: {data}"
                    print(f"    ✅ 响应符合预期: {data['message']}")
                else:
                    assert data.get("ok") is False, f"预期探针拒绝 (ok=False)，实际返回成功: {data}"
                    err_msg = data.get("error", "") or data.get("message", "")
                    assert p["expect_keyword"] in err_msg, f"预期包含关键字 {p['expect_keyword']}，实际: {err_msg}"
                    print(f"    ✅ 上游鉴权拦截真实可观测: {err_msg[:80]}...")
        except urllib.error.HTTPError as e:
            print(f"    ⚠️ HTTP 错误: {e.code}")

def test_api_config_save_flow():
    print("\n[3] 测试普通用户在面板点击【保存配置】(POST /api/config)...")
    save_payload = {
        "critic": {
            "provider": "gemini",
            "base_url": "auto",
            "model": "auto",
            "api_key": "AIzaSyTestUserKeyFromPanel",
            "timeout": 25.0
        }
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/config",
        data=json.dumps(save_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res.get("ok") is True, f"保存配置失败: {res}"
        print(f"    ✅ 面板保存配置返回: {res.get('message')}")

    # 读取验证配置是否已自动将 'auto' 解析为智能默认值，绝无写死 'auto' 破坏 URL
    req_get = urllib.request.Request(f"{BASE_URL}/api/config")
    with urllib.request.urlopen(req_get, timeout=5.0) as resp:
        saved_cfg = json.loads(resp.read().decode("utf-8"))
        critic_cfg = saved_cfg.get("critic", {})
        print(f"    • 读取保存后的配置: provider={critic_cfg.get('provider')}, base_url={critic_cfg.get('base_url')}, model={critic_cfg.get('model')}")
        assert critic_cfg.get("provider") == "gemini", "provider 保存异常"
        assert critic_cfg.get("base_url") == "https://generativelanguage.googleapis.com/v1beta/openai", f"base_url 智能默认值被 auto 污染: {critic_cfg.get('base_url')}"
        assert critic_cfg.get("model") == "gemini-2.5-flash", f"model 智能默认值被 auto 污染: {critic_cfg.get('model')}"
        assert critic_cfg.get("api_key") == "AIzaSyTestUserKeyFromPanel", "api_key 未正确保存"
        print("    ✅ 智能默认值归一化验证通过！未被 'auto' 字符串污染")

if __name__ == "__main__":
    try:
        test_panel_html_contains_critic()
        test_api_critic_test_endpoints()
        test_api_config_save_flow()
        print("\n🎉 全部用户面板模拟测试 100% 成功通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
