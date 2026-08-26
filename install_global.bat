@echo off
REM install_global.bat - Global install for bo-novel (Windows).
REM Usage: install_global.bat [wheel|exe]
REM   wheel (default): pip install dist\bo_novel-*.whl; command at <Python>\Scripts\bonovel.exe
REM   exe           : copy dist\bonovel.exe to %LOCALAPPDATA%\bonovel\
REM After install, adds the command dir to the USER PATH (open a new terminal).
REM Note: keep this file ASCII-only (cmd reads .bat with the ANSI codepage).

setlocal enabledelayedexpansion

set "MODE=%~1"
if "%MODE%"=="" set "MODE=wheel"

if /i "%MODE%"=="exe" goto :do_exe
goto :do_wheel

:do_exe
set "BIN_DIR=%LOCALAPPDATA%\bonovel"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
copy /y "%~dp0dist\bonovel.exe" "%BIN_DIR%\bonovel.exe" >nul
if errorlevel 1 (
  echo [install] ERROR: dist\bonovel.exe not found. Build it with PyInstaller first.
  exit /b 1
)
set "ADD_PATH=%BIN_DIR%"
echo [install] Copied bonovel.exe to %BIN_DIR%
goto :path_done

:do_wheel
set "PY="
if exist "%SystemDrive%\Python311\python.exe" set "PY=%SystemDrive%\Python311\python.exe"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 (
    for /f "delims=" %%i in ('where python') do set "PY=%%i"
  )
)
if not defined PY (
  echo [install] ERROR: Python 3.9+ not found.
  exit /b 1
)
echo [install] Using Python: %PY%
for /f "delims=" %%w in ('dir /b "%~dp0dist\bo_novel-*.whl" 2^>nul') do set "WHEEL=%~dp0dist\%%w"
if not defined WHEEL (
  echo [install] ERROR: dist\bo_novel-*.whl not found. Build it with pip wheel first.
  exit /b 1
)
echo [install] Installing %WHEEL%
"%PY%" -m pip install --upgrade "%WHEEL%"
if errorlevel 1 exit /b 1
for %%i in ("%PY%") do set "PYDIR=%%~dpi"
set "ADD_PATH=%PYDIR%Scripts"
echo [install] Installed command at %ADD_PATH%\bonovel.exe
goto :path_done

:path_done
set "BONOVEL_INSTALL_DIR=%ADD_PATH%"
powershell -NoProfile -Command "$d=$env:BONOVEL_INSTALL_DIR; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($p -notlike '*'+$d+'*'){ [Environment]::SetEnvironmentVariable('Path', ($p.TrimEnd(';')+';'+$d), 'User'); Write-Host ('[install] Added to user PATH: '+$d) } else { Write-Host ('[install] Already in user PATH: '+$d) }"

REM Git Bash shim: ~/bin is always on the Git Bash PATH, independent of Windows PATH refresh.
if not exist "%USERPROFILE%\bin" mkdir "%USERPROFILE%\bin"
copy /y "%~dp0packaging\bonovel-shim" "%USERPROFILE%\bin\bonovel" >nul
if not errorlevel 1 echo [install] Installed Git Bash shim: %USERPROFILE%\bin\bonovel
echo [install] Done. Open a NEW terminal, then run: bonovel --version
endlocal
