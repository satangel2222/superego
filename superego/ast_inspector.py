# -*- coding: utf-8 -*-
"""ast_inspector.py —— 深度代码载荷静态语法树审计引擎 (AST Payload Inspector).

职能:
  穿透检查 Python / Node.js 脚本文件以及终端单行内联脚本 (python -c / node -e)，
  利用抽象语法树 (AST) 识别不可逆批量删除、数据销毁与未授权外部操作。
"""
import ast
import re
import shlex
from pathlib import Path
from typing import Optional, Tuple, List, Set

# 高危破坏性 Python 方法/函数特征
_DESTRUCTIVE_CALLS = {
    # 操作系统/文件系统强删
    ("shutil", "rmtree"),
    ("os", "remove"),
    ("os", "unlink"),
    ("os", "rmdir"),
    # 常见通讯/社交平台批量销毁 API (Telegram / Discord / Slack 等)
    ("client", "delete_messages"),
    ("client", "delete_dialog"),
    ("bot", "delete_message"),
    ("", "delete_messages"),
    ("", "delete_message"),
}

# 高危 SQL 语句特征
_DANGEROUS_SQL_RE = re.compile(
    r"\b(DROP\s+TABLE|TRUNCATE\s+TABLE|DROP\s+DATABASE|DELETE\s+FROM\s+\w+\s*(?:;|$))\b",
    re.I
)

# 命令行内联脚本匹配
_INLINE_PY_RE = re.compile(r"\b(?:python|python3|py|pwsh|powershell)\b.*?(?:-c|-Command)\s+([\"\'])([\s\S]*?)\1", re.I)
_INLINE_NODE_RE = re.compile(r"\b(?:node|bun|deno)\b.*?-e\s+([\"\'])([\s\S]*?)\1", re.I)

# 脚本执行命令匹配 (python script.py)
_RUN_SCRIPT_RE = re.compile(r"\b(?:python|python3|py)\s+([^\s\-][^\s]+\.py)\b", re.I)


class _DangerousCallVisitor(ast.NodeVisitor):
    """遍历 AST 收集所有危险函数与方法调用"""
    def __init__(self):
        self.found_destructive: List[str] = []
        self.found_raw_sql: List[str] = []

    def visit_Call(self, node: ast.Call):
        # 1. 检测 obj.method() 形式
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            obj_name = ""
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                obj_name = node.func.value.attr

            # 匹配破坏性方法
            if (obj_name, attr_name) in _DESTRUCTIVE_CALLS or ("", attr_name) in _DESTRUCTIVE_CALLS:
                self.found_destructive.append(f"{obj_name}.{attr_name}" if obj_name else attr_name)
            elif attr_name in ("rmtree", "unlink", "delete_messages", "delete_message"):
                self.found_destructive.append(f"{obj_name}.{attr_name}" if obj_name else attr_name)

            # 检测 execute("DROP TABLE ...")
            if attr_name in ("execute", "executemany") and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    if _DANGEROUS_SQL_RE.search(first_arg.value):
                        self.found_raw_sql.append(first_arg.value.strip()[:60])

        # 2. 检测 func() 形式
        elif isinstance(node.func, ast.Name):
            fname = node.func.id
            if ("", fname) in _DESTRUCTIVE_CALLS or fname in ("delete_messages", "rmtree"):
                self.found_destructive.append(fname)

        self.generic_visit(node)


def audit_python_code(code_str: str, source_label: str = "script") -> Tuple[bool, Optional[str]]:
    """使用 Python 官方 AST 解析器审查代码源码，返回 (allowed, reason)"""
    if not code_str or not code_str.strip():
        return True, None

    try:
        tree = ast.parse(code_str)
    except SyntaxError:
        # 若有语法错误，暂不做 AST 拦截，交由解释器报错
        return True, None
    except Exception:
        return True, None

    visitor = _DangerousCallVisitor()
    visitor.visit(tree)

    if visitor.found_destructive:
        calls_str = ", ".join(set(visitor.found_destructive))
        return False, (
            f"⛔ [AST_DESTRUCTIVE_API_BLOCKED] 在 {source_label} 中检测到高危不可逆破坏性调用: `{calls_str}`！\n"
            f"按安全契约铁律：严禁在未附带清单契约的情况下盲目批量调用删除/销毁 API。\n"
            f"⇒ 【梯子导航】：请在代码中增加 `--dry-run` 导出 `.manifest.json` 清单供核对，"
            f"并在实际执行时携带 `--manifest .manifest.json` 参数！"
        )

    if visitor.found_raw_sql:
        sql_str = "; ".join(visitor.found_raw_sql)
        return False, (
            f"⛔ [AST_DESTRUCTIVE_SQL_BLOCKED] 在 {source_label} 中检测到高危破坏性 SQL 执行: `{sql_str}`！\n"
            f"按数据安全铁律：严禁直接执行无约束删除或 DROP/TRUNCATE 表！"
        )

    return True, None


def audit_command_ast(command: str, cwd: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """穿透审查终端命令中包含的脚本文件或内联代码"""
    if not command:
        return True, None

    # 若命令显式声明了契约参数，放行执行阶段
    if "--manifest" in command or "--dry-run" in command:
        return True, None

    # 1. 检查内联 Python 执行: python -c "..."
    m_inline = _INLINE_PY_RE.search(command)
    if m_inline:
        inline_code = m_inline.group(2)
        ok, reason = audit_python_code(inline_code, source_label="内联命令行 (-c)")
        if not ok:
            return False, reason

    # 2. 检查脚本文件执行: python clean_cache.py
    m_script = _RUN_SCRIPT_RE.search(command)
    if m_script:
        script_path_str = m_script.group(1)
        base_dir = cwd or Path.cwd()
        script_path = (base_dir / script_path_str).resolve()
        if script_path.exists() and script_path.is_file():
            try:
                code_content = script_path.read_text(encoding="utf-8", errors="ignore")
                ok, reason = audit_python_code(code_content, source_label=f"脚本文件 `{script_path.name}`")
                if not ok:
                    return False, reason
            except Exception:
                pass

    return True, None
