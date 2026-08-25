@echo off
REM bonovel.bat — Windows 全局启动脚本（免 pip install）
REM 用法：bonovel          （打开书架）
REM        bonovel 小说.txt （导入一本小说）
REM        bonovel -d 目录    （指定数据目录）
REM 说明：把项目目录临时加入 PYTHONPATH 后调用 python -m bonovel。
REM       脚本所在目录须是项目根（含 bonovel 包）。

setlocal
set "PROJECT_DIR=%~dp0"
set "SRC_DIR=%PROJECT_DIR%src"

if not defined PYTHONPATH (
    set "PYTHONPATH=%SRC_DIR%"
) else (
    set "PYTHONPATH=%SRC_DIR%;%PYTHONPATH%"
)

REM 确定 Python 解释器：优先调用用户 PATH 中的 python
set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

%PY% -m bonovel %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
