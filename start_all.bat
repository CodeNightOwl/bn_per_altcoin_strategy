@echo off
echo ====================================
echo 山寨币涨跌幅监控系统 - 一键启动
echo ====================================
echo.

echo 正在启动后端服务...
start "后端服务" cmd /k "start_backend.bat"

echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo 正在启动前端服务...
start "前端服务" cmd /k "start_frontend.bat"

echo.
echo ====================================
echo 启动完成！
echo ====================================
echo 后端地址: http://localhost:3007
echo 前端地址: http://localhost:3008
echo.
echo 按任意键关闭此窗口...
pause >nul