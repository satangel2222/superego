# -*- coding: utf-8 -*-
"""tool_normalizer.py —— 跨四端工具调用统一归一化层 (Cross-Platform Tool Normalizer).

职能:
  将 Claude Code、OpenAI Codex、Google Antigravity、DeepSeek Harness 四大平台的
  工具调用与入参结构，统一归一化为标准的抽象数据载荷，彻底抹平平台间工具名与字段差异。
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class NormalizedToolCall:
    kind: str  # 'command' | 'file_write' | 'file_edit' | 'search' | 'fetch' | 'codegraph' | 'archive' | 'view' | 'screenshot' | 'other'
    tool_name: str
    command: str = ""
    file_path: str = ""
    content: str = ""
    old_content: str = ""
    is_new_file: bool = False
    query: str = ""
    url: str = ""
    raw_input: Dict[str, Any] = field(default_factory=dict)


def normalize_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> NormalizedToolCall:
    """对跨四端工具调用执行标准归一化映射 (抹平 Claude, Codex, AG, DSH 与本地生态工具差异)"""
    name = (tool_name or "").strip()
    inp = tool_input or {}
    name_lower = name.lower()

    # 1. 命令行执行类 (Command Execution)
    # Claude / Codex: "Bash", "PowerShell"
    # Antigravity: "run_command"
    # DSH: "terminal", "exec_command", "Bash"
    cmd_tools = ("bash", "powershell", "pwsh", "run_command", "terminal", "exec_command", "execute_command")
    if name_lower in cmd_tools or "command" in inp or "CommandLine" in inp:
        cmd = inp.get("command") or inp.get("CommandLine") or inp.get("cmd") or ""
        return NormalizedToolCall(
            kind="command",
            tool_name=name,
            command=str(cmd).strip(),
            raw_input=inp
        )

    # 2. 全量文件写入类 (Full File Write / Create)
    # Claude / Codex: "Write" (path, content)
    # Antigravity: "write_to_file" (TargetFile, CodeContent, Overwrite)
    write_tools = ("write", "write_to_file", "create_file")
    if name_lower in write_tools or ("TargetFile" in inp and "CodeContent" in inp):
        path = inp.get("TargetFile") or inp.get("path") or inp.get("file_path") or ""
        content = inp.get("CodeContent") or inp.get("content") or ""
        overwrite = bool(inp.get("Overwrite", False))
        return NormalizedToolCall(
            kind="file_write",
            tool_name=name,
            file_path=str(path).strip(),
            content=str(content),
            is_new_file=not overwrite,
            raw_input=inp
        )

    # 3. 增量/精准代码替换类 (Partial File Edit / Replace)
    # Claude / Codex: "Edit" (path, old_string, new_string)
    # Antigravity: "replace_file_content" (TargetFile, TargetContent, ReplacementContent)
    edit_tools = ("edit", "replace_file_content", "str_replace_editor", "patch_file")
    if name_lower in edit_tools or ("TargetContent" in inp and "ReplacementContent" in inp):
        path = inp.get("TargetFile") or inp.get("path") or inp.get("file_path") or ""
        old_c = inp.get("TargetContent") or inp.get("old_string") or inp.get("old_str") or ""
        new_c = inp.get("ReplacementContent") or inp.get("new_string") or inp.get("new_str") or ""
        return NormalizedToolCall(
            kind="file_edit",
            tool_name=name,
            file_path=str(path).strip(),
            old_content=str(old_c),
            content=str(new_c),
            is_new_file=False,
            raw_input=inp
        )

    # 4. 代码拓扑图谱类 (CodeGraph)
    # codegraph_explore, codegraph
    if "codegraph" in name_lower:
        q = inp.get("query") or inp.get("symbol") or ""
        return NormalizedToolCall(
            kind="codegraph",
            tool_name=name,
            query=str(q).strip(),
            raw_input=inp
        )

    # 5. 跨端脑库检索类 (Cross-Brain Archive)
    # ag_archive, codex_archive, q.js
    if "archive" in name_lower or "brain" in name_lower:
        q = inp.get("query") or inp.get("keyword") or inp.get("kw") or ""
        return NormalizedToolCall(
            kind="archive",
            tool_name=name,
            query=str(q).strip(),
            raw_input=inp
        )

    # 6. 外部检索与搜索类 (Web Search / SOTA Engines)
    # search_web, WebSearch, firecrawl_search, jina_search, scrapling
    search_tools = ("search_web", "websearch", "search", "firecrawl_search", "jina_search", "autocli")
    if name_lower in search_tools or ("search" in name_lower and "code" not in name_lower):
        q = inp.get("query") or inp.get("q") or ""
        return NormalizedToolCall(
            kind="search",
            tool_name=name,
            query=str(q).strip(),
            raw_input=inp
        )

    # 7. 网页与文档抓取类 (Web Fetch / Crawl)
    # read_url_content, WebFetch, firecrawl_scrape, jina_reader, crawl4ai
    fetch_tools = ("read_url_content", "webfetch", "fetch", "firecrawl_scrape", "jina_reader", "crawl4ai")
    if name_lower in fetch_tools or "url" in inp or "Url" in inp:
        u = inp.get("Url") or inp.get("url") or ""
        return NormalizedToolCall(
            kind="fetch",
            tool_name=name,
            url=str(u).strip(),
            raw_input=inp
        )

    # 8. 文件查看与只读类 (View / Read)
    # view_file, Read, read_file
    view_tools = ("view_file", "read", "read_file", "cat")
    if name_lower in view_tools or "AbsolutePath" in inp:
        path = inp.get("AbsolutePath") or inp.get("path") or inp.get("file_path") or ""
        return NormalizedToolCall(
            kind="view",
            tool_name=name,
            file_path=str(path).strip(),
            raw_input=inp
        )

    # 9. 桌面视窗与截图验真类 (Screenshots)
    # desktop-window-shot, view_image, take_screenshot
    if "shot" in name_lower or "screenshot" in name_lower or "view_image" in name_lower:
        return NormalizedToolCall(
            kind="screenshot",
            tool_name=name,
            raw_input=inp
        )

    # 10. 其他类
    return NormalizedToolCall(
        kind="other",
        tool_name=name,
        raw_input=inp
    )
