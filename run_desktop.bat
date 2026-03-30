@echo off
chcp 65001 >nul
echo 启动爬虫桌面应用...
cd frontend\desktop_app
if not exist "node_modules" (
    echo 检测到未安装依赖，正在运行 npm install...
    call npm install
)
call npm start
pause
