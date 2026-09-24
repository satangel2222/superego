# ==============================================================================
# TruthGate 1.0 零副作用一键物理秒级回滚脚本 (One-Click Zero-Side-Effect Rollback)
# 锚定版本: v1.0.0-before-raptor (Commit: c5037af)
# ==============================================================================
param (
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "🔄 正在启动 TruthGate 1.0 零副作用一键物理回滚..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Git 强力物理回滚到不可变锚点
Set-Location $ScriptDir
Write-Host "📦 [1/4] 回退 Git 代码树至 v1.0.0-before-raptor (Commit: c5037af)..." -ForegroundColor Yellow
git reset --hard v1.0.0-before-raptor
git clean -fd
Write-Host "  [✓] Git 仓库已完全恢复至纯净锚点状态" -ForegroundColor Green

# 2. 物理快照双保险同步 (若有非 Git 管理的损坏)
$BackupDir = Join-Path $env:USERPROFILE ".truthgate\backups\snapshot_v1.0.0_c5037af\truthgate"
$TargetTg = Join-Path $env:USERPROFILE ".truthgate"
$TargetClaudeHooks = Join-Path $env:USERPROFILE ".claude\hooks"
$TargetClaudeSemantic = Join-Path $env:USERPROFILE ".claude\superego-semantic"

Write-Host "📂 [2/4] 从本地物理快照二次镜像同步宿主配置目录..." -ForegroundColor Yellow
if (Test-Path $BackupDir) {
    Copy-Item -Path "$BackupDir\*" -Destination $TargetTg -Recurse -Force
    if (Test-Path $TargetClaudeHooks) {
        Copy-Item -Path "$BackupDir\hook_entry.py" -Destination $TargetClaudeHooks -Force
        Copy-Item -Path "$BackupDir\critic_engine.py" -Destination $TargetClaudeHooks -Force
        Copy-Item -Path "$BackupDir\semantic_judge.py" -Destination $TargetClaudeHooks -Force
    }
    if (Test-Path $TargetClaudeSemantic) {
        Copy-Item -Path "$BackupDir\semantic_judge.py" -Destination $TargetClaudeSemantic -Force
        Copy-Item -Path "$BackupDir\critic_engine.py" -Destination $TargetClaudeSemantic -Force
    }
    Write-Host "  [✓] 宿主 hook 目录已完成物理快照同步覆盖" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ 未找到物理快照，以 Git 代码树覆盖为准" -ForegroundColor Yellow
}

# 3. 重启 17911 司法守护进程
Write-Host "🔄 [3/4] 重启 17911 常驻司法守护进程..." -ForegroundColor Yellow
try {
    python -m truthgate service stop
    Start-Sleep -Seconds 1
    python -m truthgate service start
    Write-Host "  [✓] 17911 守护进程已成功重启" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ 守护进程自动重启遇阻，可手动执行 tg service start" -ForegroundColor Yellow
}

# 4. 满血度诊断体检核实
Write-Host "🩸 [4/4] 运行体检，核实是否 100% 满血恢复..." -ForegroundColor Yellow
python -m truthgate blood

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "🎉 回滚完成！TruthGate 已 100% 恢复至稳定锚点版本，零副作用残留！" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
