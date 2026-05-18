@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =======================================
echo    Galgame Studio v0.2.1
echo    小说 - 剧本 - 提示词 - 打包
echo =======================================
echo.
echo [启动] 正在启动服务...
echo [提示] 浏览器将自动打开 http://127.0.0.1:8888
echo [提示] 按 Ctrl+C 或关闭此窗口停止服务
echo.

start "" http://127.0.0.1:8888
python main.py
pause
