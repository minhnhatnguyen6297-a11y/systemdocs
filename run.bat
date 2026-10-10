@echo off
chcp 65001 >nul
setlocal

set "ROOT_DIR=%~dp0"
set "SHELL_DIR=%ROOT_DIR%shell"

if not exist "%SHELL_DIR%\package.json" (
  echo [LOI] Khong tim thay shell\package.json.
  endlocal & exit /b 1
)

rem Worktrees share Git history, but do not include installed runtimes.
set "SHARED_ROOT="
for /f "delims=" %%G in ('git -C "%ROOT_DIR%." rev-parse --path-format^=absolute --git-common-dir 2^>nul') do for %%R in ("%%G\..") do set "SHARED_ROOT=%%~fR"
set "ELECTRON_EXE=%SHELL_DIR%\node_modules\electron\dist\electron.exe"
if exist "%ELECTRON_EXE%" goto runtime_ready
if defined SHARED_ROOT set "ELECTRON_EXE=%SHARED_ROOT%\shell\node_modules\electron\dist\electron.exe"
if exist "%ELECTRON_EXE%" goto runtime_ready
echo [LOI] Chua co Electron. Chay npm ci trong "%SHELL_DIR%" roi thu lai.
pause
endlocal & exit /b 1

:runtime_ready
if defined G1_PYTHON goto launch
if exist "%ROOT_DIR%notary_v2\venv\Scripts\python.exe" (
  set "G1_PYTHON=%ROOT_DIR%notary_v2\venv\Scripts\python.exe"
  goto launch
)
if defined SHARED_ROOT if exist "%SHARED_ROOT%\notary_v2\venv\Scripts\python.exe" set "G1_PYTHON=%SHARED_ROOT%\notary_v2\venv\Scripts\python.exe"

:launch
set "ELECTRON_RUN_AS_NODE="
cd /d "%SHELL_DIR%"
echo Dang mo Electron shell...
"%ELECTRON_EXE%" . %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause

endlocal & exit /b %EXIT_CODE%
