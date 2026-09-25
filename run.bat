@echo off
chcp 65001 >nul
setlocal

set "ROOT_DIR=%~dp0"
set "SHELL_DIR=%ROOT_DIR%shell"

if not exist "%SHELL_DIR%\package.json" (
  echo [LOI] Khong tim thay shell\package.json.
  endlocal & exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [LOI] Khong tim thay npm trong PATH. Hay cai Node.js roi thu lai.
  endlocal & exit /b 1
)

cd /d "%SHELL_DIR%"
echo Dang mo Electron shell...
call npm start %*
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
