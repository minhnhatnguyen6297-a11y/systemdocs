@echo off
rem Entry point for the Zalo intake module.
rem Dependencies come from requirements.txt -- install once with:
rem     pip install -r requirements.txt
rem No venv is created or activated here.
setlocal
set "PYTHONPATH=%~dp0src"
python -m zalo_module.cli %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo zalo_module exited with code %RC%.
    pause
)
endlocal & exit /b %RC%
