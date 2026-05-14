@echo off
echo ====================================
echo 山寨币涨跌幅监控系统 - 前端启动
echo ====================================
echo.

cd frontend

echo 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo.
echo 检查依赖包...
if not exist "node_modules" (
    echo 安装依赖包...
    call npm install
)

echo.
echo 启动Vite开发服务器...
echo 前端地址: http://localhost:3008
echo.
call npm run dev

pause