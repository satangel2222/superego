@echo off
chcp 65001 >nul
echo =================================================================
echo 🔄 正在启动 TruthGate 1.0 零副作用一键物理回滚...
echo =================================================================
cd /d "%~dp0"

echo 📦 [1/4] 回退 Git 代码树至 v1.0.0-before-raptor (Commit: c5037af)...
git reset --hard v1.0.0-before-raptor
git clean -fd

echo 📂 [2/4] 从物理快照镜像同步...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Copy-Item -Path '%USERPROFILE%\.truthgate\backups\snapshot_v1.0.0_c5037af\truthgate\*' -Destination '%USERPROFILE%\.truthgate' -Recurse -Force"

echo 🔄 [3/4] 重启 17911 守护进程...
py -3 -m truthgate service stop
timeout /t 1 /nobreak >nul
py -3 -m truthgate service start

echo 🩸 [4/4] 运行满血度诊断体检...
py -3 -m truthgate blood

echo =================================================================
echo 🎉 回滚完成！TruthGate 已恢复至稳定锚点版本！
echo =================================================================
pause
