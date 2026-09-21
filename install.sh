#!/usr/bin/env bash
# ==============================================================================
# 🛡️ Superego 2.0 一键安装脚本 (macOS / Linux)
# 用法: curl -fsSL https://raw.githubusercontent.com/satangel2222/superego/main/install.sh | bash
# ==============================================================================

set -e

echo ""
echo "========================================================================"
echo " 🛡️  SUPEREGO 2.0: 专治 AI 偷懒、撒谎、吹牛与越权 (One-Line Installer)"
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
SUPEREGO_HOME="$HOME/.superego"
echo "  [✓] 目标安装目录: $SUPEREGO_HOME"
mkdir -p "$SUPEREGO_HOME"

# 3. 克隆或同步仓库
REPO_URL="https://github.com/satangel2222/superego.git"
if command -v git &>/dev/null; then
    if [ -d "$SUPEREGO_HOME/.git" ]; then
        echo "  🔄 正在同步拉取最新版本..."
        git -C "$SUPEREGO_HOME" pull --quiet
    else
        echo "  📦 正在克隆 Superego 核心资产..."
        git clone --depth 1 "$REPO_URL" "$SUPEREGO_HOME" --quiet
    fi
else
    echo "  📦 正在下载源码包 (TAR.GZ)..."
    TAR_URL="https://github.com/satangel2222/superego/archive/refs/heads/main.tar.gz"
    curl -fsSL "$TAR_URL" | tar -xz -C "$HOME"
    cp -r "$HOME/superego-main/"* "$SUPEREGO_HOME/"
    rm -rf "$HOME/superego-main"
fi

# 4. 执行跨端挂载
INSTALLER_PY="$SUPEREGO_HOME/superego/installer.py"
if [ -f "$INSTALLER_PY" ]; then
    echo "  ⚡ 正在执行全自动平台检测与跨端挂载..."
    "$PYTHON_BIN" "$INSTALLER_PY" install --profile vibe-boss
else
    echo "  ❌ 错误: 未找到 installer.py，安装包不完整。"
    exit 1
fi

echo ""
echo "========================================================================"
echo " 🎉 恭喜！Superego 2.0 已部署完成并开机自适应生效！"
echo " • 实时大盘: 访问 http://127.0.0.1:17911/dashboard 查看实时司法裁决"
echo " • 如需一键回滚: 随时运行 superego rollback 即可 3 秒彻底复原"
echo "========================================================================"
echo ""
