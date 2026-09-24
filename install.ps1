# ==============================================================================
# 🛡️ TruthGate 1.0 一键安装脚本 (Windows PowerShell)
# 用法: irm https://raw.githubusercontent.com/satangel2222/truthgate/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " 🛡️  TRUTHGATE 1.0: 专治 AI 偷懒、撒谎、吹牛与越权 (One-Line Installer)" -ForegroundColor Cyan
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
$truthgateHome = Join-Path $HOME ".truthgate"
Write-Host "  [✓] 目标安装目录: $truthgateHome" -ForegroundColor Gray

if (-not (Test-Path $truthgateHome)) {
    New-Item -ItemType Directory -Path $truthgateHome -Force | Out-Null
}

# 3. 拉取或更新 TruthGate 仓库
$repoUrl = "https://github.com/satangel2222/truthgate.git"
if (Get-Command git -ErrorAction SilentlyContinue) {
    if (Test-Path (Join-Path $truthgateHome ".git")) {
        Write-Host "  🔄 检测到已安装，正在同步拉取最新版本..." -ForegroundColor Cyan
        git -C $truthgateHome pull --quiet
    } else {
        Write-Host "  📦 正在克隆 TruthGate 核心资产..." -ForegroundColor Cyan
        git clone --depth 1 $repoUrl $truthgateHome --quiet
    }
} else {
    Write-Host "  📦 正在下载 TruthGate 源码包 (ZIP)..." -ForegroundColor Cyan
    $zipUrl = "https://github.com/satangel2222/truthgate/archive/refs/heads/main.zip"
    $zipFile = Join-Path $HOME "truthgate-main.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile
    Expand-Archive -Path $zipFile -DestinationPath $HOME -Force
    Copy-Item -Path (Join-Path $HOME "truthgate-main\*") -Destination $truthgateHome -Recurse -Force
    Remove-Item -Path (Join-Path $HOME "truthgate-main") -Recurse -Force
    Remove-Item -Path $zipFile -Force
}

# 4. 执行本地自适应跨四端安装器
$installerPy = Join-Path $truthgateHome "truthgate\installer.py"
if (-not (Test-Path $installerPy)) {
    $installerPy = Join-Path $truthgateHome "installer.py"
}
if (Test-Path $installerPy) {
    Write-Host "  ⚡ 正在执行全自动平台检测与跨端挂载..." -ForegroundColor Cyan
    & $pythonCmd $installerPy install --profile vibe-boss
} else {
    Write-Host "  ❌ 错误: 未找到 installer.py，安装包可能不完整。" -ForegroundColor Red
    exit 1
}

# 5. 创建 tg / truthgate / superego 快捷命令行并注册到 PATH
$binDir = Join-Path $truthgateHome "bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }

$tgCmdScript = "@echo off`r`n$pythonCmd `"%USERPROFILE%\.truthgate\truthgate\__main__.py`" %*"
Set-Content -Path (Join-Path $binDir "tg.cmd") -Value $tgCmdScript -Encoding Ascii
Set-Content -Path (Join-Path $binDir "truthgate.cmd") -Value $tgCmdScript -Encoding Ascii
Set-Content -Path (Join-Path $binDir "superego.cmd") -Value $tgCmdScript -Encoding Ascii

$tgPsScript = "& python `"`$env:USERPROFILE\.truthgate\truthgate\__main__.py`" `$args"
Set-Content -Path (Join-Path $binDir "tg.ps1") -Value $tgPsScript -Encoding Utf8
Set-Content -Path (Join-Path $binDir "truthgate.ps1") -Value $tgPsScript -Encoding Utf8
Set-Content -Path (Join-Path $binDir "superego.ps1") -Value $tgPsScript -Encoding Utf8

try {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$binDir;$userPath", "User")
        $env:Path = "$binDir;$env:Path"
    }
} catch {}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host " 🎉 恭喜！TruthGate 1.0 已全部部署完成并开机自适应生效！" -ForegroundColor Green
Write-Host " • 快捷命令: 终端直接使用 tg 或 truthgate" -ForegroundColor Yellow
Write-Host " • 切换画像: 终端运行 tg profile list / tg profile use engineer" -ForegroundColor White
Write-Host " • 自由外审: 终端运行 tg critic show / tg critic set (支持 DeepSeek/Ollama/Jev)" -ForegroundColor White
Write-Host " • 规则市场: 终端运行 tg rulepack list / tg rulepack test" -ForegroundColor White
Write-Host " • 实时大盘: 终端运行 tg dashboard (在浏览器访问 http://127.0.0.1:17911/dashboard)" -ForegroundColor White
Write-Host " • 如需一键回滚: 随时运行 tg rollback 即可 3 秒彻底复原" -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""
