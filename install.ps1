# ==============================================================================
# 🛡️ Superego 2.0 一键安装脚本 (Windows PowerShell)
# 用法: irm https://raw.githubusercontent.com/satangel2222/superego/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " 🛡️  SUPEREGO 2.0: 专治 AI 偷懒、撒谎、吹牛与越权 (One-Line Installer)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python 环境
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.") {
            $pythonCmd = $cmd
            Write-Host "  [✓] 发现可用 Python 解释器: $ver ($cmd)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  ❌ 错误: 未检测到 Python 3.10+ 环境。" -ForegroundColor Red
    Write-Host "  请先前往 https://www.python.org/downloads/ 安装 Python 并勾选 'Add to PATH'。" -ForegroundColor Yellow
    exit 1
}

# 2. 目标安装路径
$superegoHome = Join-Path $HOME ".superego"
Write-Host "  [✓] 目标安装目录: $superegoHome" -ForegroundColor Gray

if (-not (Test-Path $superegoHome)) {
    New-Item -ItemType Directory -Path $superegoHome -Force | Out-Null
}

# 3. 拉取或更新 Superego 仓库
$repoUrl = "https://github.com/satangel2222/superego.git"
if (Get-Command git -ErrorAction SilentlyContinue) {
    if (Test-Path (Join-Path $superegoHome ".git")) {
        Write-Host "  🔄 检测到已安装，正在同步拉取最新版本..." -ForegroundColor Cyan
        git -C $superegoHome pull --quiet
    } else {
        Write-Host "  📦 正在克隆 Superego 核心资产..." -ForegroundColor Cyan
        git clone --depth 1 $repoUrl $superegoHome --quiet
    }
} else {
    Write-Host "  📦 正在下载 Superego 源码包 (ZIP)..." -ForegroundColor Cyan
    $zipUrl = "https://github.com/satangel2222/superego/archive/refs/heads/main.zip"
    $zipFile = Join-Path $HOME "superego-main.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile
    Expand-Archive -Path $zipFile -DestinationPath $HOME -Force
    Copy-Item -Path (Join-Path $HOME "superego-main\*") -Destination $superegoHome -Recurse -Force
    Remove-Item -Path (Join-Path $HOME "superego-main") -Recurse -Force
    Remove-Item -Path $zipFile -Force
}

# 4. 执行本地自适应跨四端安装器
$installerPy = Join-Path $superegoHome "superego\installer.py"
if (Test-Path $installerPy) {
    Write-Host "  ⚡ 正在执行全自动平台检测与跨端挂载..." -ForegroundColor Cyan
    & $pythonCmd $installerPy install --profile vibe-boss
} else {
    Write-Host "  ❌ 错误: 未找到 installer.py，安装包可能不完整。" -ForegroundColor Red
    exit 1
}

# 5. 创建 superego 快捷命令行并注册到 PATH
$binDir = Join-Path $superegoHome "bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
$cmdScript = "@echo off`r`n$pythonCmd `"%USERPROFILE%\.superego\superego\__main__.py`" %*"
Set-Content -Path (Join-Path $binDir "superego.cmd") -Value $cmdScript -Encoding Ascii
try {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$binDir;$userPath", "User")
        $env:Path = "$binDir;$env:Path"
    }
} catch {}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host " 🎉 恭喜！Superego 2.0 已全部部署完成并开机自适应生效！" -ForegroundColor Green
Write-Host " • 实时大盘: 终端运行 superego dashboard (在浏览器访问 http://127.0.0.1:17925/dashboard)" -ForegroundColor White
Write-Host " • 如需一键回滚: 随时运行 superego rollback 即可 3 秒彻底复原" -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""
