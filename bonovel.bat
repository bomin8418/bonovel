@echo off
REM bonovel.bat — Windows 全局启动脚本（免 pip install）
REM 用法：bonovel          （打开书架）
REM        bonovel 小说.txt （导入一本小说）
REM        bonovel -d 目录    （指定数据目录）
REM 说明：委托根目录 run.py 启动（自动定位 src，无需 PYTHONPATH）。

setlocal
set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

%PY% "%~dp0run.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
