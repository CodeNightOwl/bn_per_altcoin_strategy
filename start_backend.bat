@echo off
echo ====================================
echo 山寨币涨跌幅监控系统 - 后端启动
echo ====================================
echo.

cd backend

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 检查虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate

echo.
echo 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    pip install -r requirements.txt
)

echo.
echo 启动Flask服务器...
echo 后端地址: http://localhost:3007
echo.
python app.py

pause