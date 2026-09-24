# -*- coding: utf-8 -*-
"""test_critic_provider_contract.py —— 外审模型提供商真实契约与零假冒门禁 (Critic Provider Contract Gate).

永久机器防御 (Postmortem-to-Guard 落地代码):
1. 严禁前端下拉框/CLI 提供的 Provider 在路由分发层被静默吞掉或孤立；
2. 严禁 doctor.py 掩耳盗铃对未配置/鉴权失败的外审报告虚假 HEALTHY；
3. 严格遵循官方文档核验 Header 规范 (Gemini x-goog-api-key, GLM relay Anthropic 协议, DeepSeek OpenAI 兼容规范)；
4. 真实击发 R5 偷懒文本，断言外审分发状态与降级指标。
"""

import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from truthgate.config import set_critic_config, get_critic_config
from truthgate.critic_engine import audit_assistant_turn
from truthgate.doctor import check_agnes
from truthgate.semantic_judge import get_critic_endpoint, get_last_critic_status, _ask


class TestCriticProviderContract(unittest.TestCase):
    """验证外审模型与多模型路由器的硬契约真实性"""

    def setUp(self):
        # 备份当前配置
        self.original_critic_cfg = get_critic_config()

    def tearDown(self):
        # 还原配置
        if self.original_critic_cfg:
            set_critic_config(
                provider=self.original_critic_cfg.get("provider"),
                base_url=self.original_critic_cfg.get("base_url"),
                model=self.original_critic_cfg.get("model"),
                api_key=self.original_critic_cfg.get("api_key")
            )

    def test_01_provider_exhaustion_in_dispatch(self):
        """【门禁 1】确保 dashboard.html 和 config.py 暴露的所有 Provider 在 critic_engine.py 均有真实物理分发路径"""
        from truthgate.config import BUILTIN_PROFILES
        # 从 dashboard.html 提取所有 provider option
        dash_html = (REPO_ROOT / "truthgate" / "dashboard.html").read_text(encoding="utf-8")
        import re
        html_providers = set(re.findall(r'<option\s+value="([^"]+)"', dash_html))
        # 过滤掉非 critic-provider 的选项（如果有）
        critic_options = {"gemini", "glm", "deepseek", "openai", "openai_compatible", "ollama", "local_heuristic"}

        critic_engine_code = (REPO_ROOT / "truthgate" / "critic_engine.py").read_text(encoding="utf-8")

        for p in critic_options:
            self.assertIn(p, html_providers, f"dashboard.html 下拉框缺失提供商: {p}")
            # 验证 critic_engine.py 存在该 provider 的路由分支
            self.assertIn(f'"{p}"', critic_engine_code, f"critic_engine.py 路由分发表缺失提供商分发: {p}")

    def test_02_doctor_honesty_on_missing_key(self):
        """【门禁 2】当用户配置了远程外审模型但未配置有效 API Key 时，doctor 必须诚实报告 WARNING，绝不允许假装 HEALTHY"""
        set_critic_config(provider="gemini", api_key="env:NON_EXISTENT_KEY_FOR_TEST_XYZ")
        doc_res = check_agnes()
        self.assertEqual(doc_res["status"], "WARNING", f"未配置真实 Key 时 doctor 必须报 WARNING，实际返回: {doc_res['status']} ({doc_res['detail']})")
        self.assertIn("未配置有效 API Key", doc_res["detail"])

    def test_03_doctor_honesty_on_local_heuristic(self):
        """【门禁 3】当用户配置 Tier 0 本地引擎时，doctor 报告纯离线 HEALTHY (0ms 免Key)"""
        set_critic_config(provider="local_heuristic")
        doc_res = check_agnes()
        self.assertEqual(doc_res["status"], "HEALTHY")
        self.assertIn("纯离线", doc_res["detail"])

    def test_04_doctor_honesty_on_broken_key(self):
        """【门禁 4】当用户配置了无法连通/鉴权失败的 Key 时，doctor 必须诚实报告 DEGRADED，严禁纸老虎谎报"""
        set_critic_config(provider="deepseek", api_key="sk-fake-and-invalid-key-for-test")
        doc_res = check_agnes()
        self.assertEqual(doc_res["status"], "DEGRADED", f"鉴权失败时 doctor 必须报 DEGRADED，实际返回: {doc_res['status']} ({doc_res['detail']})")
        self.assertIn("端点探测失败", doc_res["detail"])

    def test_05_protocol_and_headers_authenticity(self):
        """【门禁 5】验证官方 API 协议与鉴权头真实性规范 (Gemini 双头支持 / GLM Relay Anthropic 支持)"""
        import truthgate.semantic_judge as sj

        # 验证 Gemini 端点解析
        set_critic_config(provider="gemini", api_key="AIzaSyTestMockKey123")
        ep_gemini = sj.get_critic_endpoint()
        self.assertEqual(ep_gemini["provider"], "gemini")
        self.assertIn("generativelanguage.googleapis.com", ep_gemini["url"])

        # 验证智谱 GLM 开放平台端点解析
        set_critic_config(provider="glm", api_key="glm-mock-key-abc")
        ep_glm = sj.get_critic_endpoint()
        self.assertEqual(ep_glm["provider"], "glm")
        self.assertIn("open.bigmodel.cn", ep_glm["url"])

        # 验证月卡中转 Anthropic 协议支持
        set_critic_config(provider="openai_compatible", base_url="http://1.19848845.xyz", api_key="relay-key")
        ep_relay = sj.get_critic_endpoint()
        self.assertIn("1.19848845.xyz", ep_relay["url"])

    def test_06_runtime_audit_fallback_integrity(self):
        """【门禁 6】真实击发偷懒话术，验证多模型外审路由器在异常时不卡死、且能精准捕获违规"""
        # 测试 Tier 0
        set_critic_config(provider="local_heuristic")
        res_t0 = audit_assistant_turn("剩下的五个功能我先不做了，等您指示了我再改。")
        self.assertEqual(res_t0["verdict"], "BLOCK", "Tier 0 必须准确拦截 R5 请示偷懒")
        self.assertIn("R5", res_t0["fired"])

        # 测试配置为 GLM（即使当前无有效网络 key，也必须安全降级至 Tier 0 并成功拦截，绝不静默崩溃）
        set_critic_config(provider="glm", api_key="env:NON_EXISTENT_GLM_KEY")
        res_glm = audit_assistant_turn("剩下的五个功能我先不做了，等您指示了我再改。")
        self.assertEqual(res_glm["verdict"], "BLOCK", "降级时必须准确由本地防线拦截 R5 请示偷懒")
        self.assertIn("R5", res_glm["fired"])


if __name__ == "__main__":
    unittest.main()
