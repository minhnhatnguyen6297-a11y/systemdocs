@echo off
chcp 65001 >nul
setlocal

rem Development-only reporting in the same shell; packaged builds stay disabled.
set "G1_VISUAL_BUG_SPIKE=1"
echo Ctrl + Shift + B -^> chon phan tu -^> ghi chu -^> Save report.
echo Escape de thoat. Bao cao va du lieu thu nam trong docs\tmp\visual-bug-reporting.
call "%~dp0run.bat" %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
