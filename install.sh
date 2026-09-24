#!/usr/bin/env bash
# ==============================================================================
# 🛡️ TruthGate 1.0 一键安装脚本 (macOS / Linux)
# 用法: curl -fsSL https://raw.githubusercontent.com/satangel2222/truthgate/main/install.sh | bash
# ==============================================================================

set -e

echo ""
echo "========================================================================"
echo " 🛡️  TRUTHGATE 1.0: 专治 AI 偷懒、撒谎、吹牛与越权 (One-Line Installer)"
echo "========================================================================"
echo ""

# 1. 检测 Python 3
PYTHON_BIN=""
for cmd in python3 python py; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            PYTHON_BIN="$cmd"
            echo "  [✓] 发现可用 Python 解释器: $($PYTHON_BIN --version) ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "  ❌ 错误: 未检测到 Python 3.10+ 环境。请先安装 Python 3.10+。"
    exit 1
fi

# 2. 目标路径
TRUTHGATE_HOME="$HOME/.truthgate"
echo "  [✓] 目标安装目录: $TRUTHGATE_HOME"
mkdir -p "$TRUTHGATE_HOME"

# 3. 克隆或同步仓库
REPO_URL="https://github.com/satangel2222/truthgate.git"
if command -v git &>/dev/null; then
    if [ -d "$TRUTHGATE_HOME/.git" ]; then
        echo "  🔄 正在同步拉取最新版本..."
        git -C "$TRUTHGATE_HOME" pull --quiet
    else
        echo "  📦 正在克隆 TruthGate 核心资产..."
        git clone --depth 1 "$REPO_URL" "$TRUTHGATE_HOME" --quiet
    fi
else
    echo "  📦 正在下载源码包 (TAR.GZ)..."
    TAR_URL="https://github.com/satangel2222/truthgate/archive/refs/heads/main.tar.gz"
    curl -fsSL "$TAR_URL" | tar -xz -C "$HOME"
    cp -r "$HOME/truthgate-main/"* "$TRUTHGATE_HOME/" 2>/dev/null || cp -r "$HOME/superego-main/"* "$TRUTHGATE_HOME/"
    rm -rf "$HOME/truthgate-main" "$HOME/superego-main"
fi

# 4. 执行跨端挂载
INSTALLER_PY="$TRUTHGATE_HOME/truthgate/installer.py"
if [ ! -f "$INSTALLER_PY" ]; then
    INSTALLER_PY="$TRUTHGATE_HOME/installer.py"
fi
if [ -f "$INSTALLER_PY" ]; then
    echo "  ⚡ 正在执行全自动平台检测与跨端挂载..."
    "$PYTHON_BIN" "$INSTALLER_PY" install --profile vibe-boss
else
    echo "  ❌ 错误: 未找到 installer.py，安装包不完整。"
    exit 1
fi

# 5. 创建 CLI 入口并软链接 (tg, truthgate, superego)
mkdir -p "$TRUTHGATE_HOME/bin"

for cmd_name in tg truthgate superego; do
    cat << EOF > "$TRUTHGATE_HOME/bin/$cmd_name"
#!/usr/bin/env bash
python3 "$TRUTHGATE_HOME/truthgate/__main__.py" "\$@"
EOF
    chmod +x "$TRUTHGATE_HOME/bin/$cmd_name"
    if [ -d "$HOME/.local/bin" ]; then
        ln -sf "$TRUTHGATE_HOME/bin/$cmd_name" "$HOME/.local/bin/$cmd_name" 2>/dev/null || true
    fi
done

echo ""
echo "========================================================================"
echo " 🎉 恭喜！TruthGate 1.0 已部署完成并开机自适应生效！"
echo " • 快捷命令: 终端直接运行 tg 或 truthgate"
echo " • 切换画像: 终端运行 tg profile list / tg profile use engineer"
echo " • 自由外审: 终端运行 tg critic show / tg critic set (支持 DeepSeek/Ollama/Jev)"
echo " • 规则市场: 终端运行 tg rulepack list / tg rulepack test"
echo " • 实时大盘: 终端运行 tg dashboard (在浏览器访问 http://127.0.0.1:17911/dashboard)"
echo " • 如需一键回滚: 随时运行 tg rollback 即可 3 秒彻底复原"
echo "========================================================================"
echo ""
