@echo off
REM 一键启动后端和前端
cd /d %~dp0

echo 正在启动后端服务...
start "" cmd /k "start-backend.bat"

echo 正在启动前端服务...
start "" cmd /k "start-frontend.bat"

echo 已分别在两个终端窗口中启动后端和前端。
echo 如需停止服务，请在对应终端窗口中手动关闭。

