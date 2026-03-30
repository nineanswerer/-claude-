@echo off
chcp 65001 >nul
echo 启动爬虫 Web 应用...
cd frontend\web_app
call python app.py
pause
