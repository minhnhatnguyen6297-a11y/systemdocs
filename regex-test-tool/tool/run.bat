@echo off
rem Tool test trich xuat van ban — nhan vien chi can nhap doi file nay.
rem Lan dau tu cai Python + thu vien (can mang 1 lan). Cac lan sau mo ngay.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY="

rem --- Tim Python san co ---
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
        if not errorlevel 1 set "PY=python"
    )
)
if not defined PY goto CAI_PYTHON
goto CO_PYTHON

:CAI_PYTHON
echo [1/3] Chua thay Python tren may. Dang tai ve de cai dat (can mang lan nay)...
set "PYSETUP=%TEMP%\python-test-tool-setup.exe"
del "%PYSETUP%" >nul 2>&1
powershell -NoLogo -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $env:PYSETUP } catch { exit 1 }"
if errorlevel 1 goto LOI_MANG
if not exist "%PYSETUP%" goto LOI_MANG
echo [2/3] Dang cai Python (cho 2-3 phut, khong tat cua so)...
"%PYSETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PYSETUP%" >nul 2>&1
rem Moi cai xong, PATH cua cua so nay chua co Python moi.
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=\"%LocalAppData%\Programs\Python\Python312\python.exe\""
if not defined PY (
    where py >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto LOI_CAI
%PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto LOI_CAI
goto CO_PYTHON

:LOI_MANG
echo [LOI] Khong tai duoc. Hay cam mang roi chay lai file nay.
pause
exit /b 1

:LOI_CAI
echo [LOI] Cai Python that bai. Tat cua so nay, mo lai may roi chay lai. Van loi thi bao cho chu.
pause
exit /b 1

:CO_PYTHON
%PY% -c "import docx" >nul 2>&1
if not errorlevel 1 goto CHAY_TOOL
echo [3/3] Dang cai them thu vien doc Word (1 lan duy nhat)...
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto LOI_THU_VIEN
goto CHAY_TOOL

:LOI_THU_VIEN
echo [LOI] Khong cai duoc thu vien. Hay cam mang roi chay lai.
pause
exit /b 1

:CHAY_TOOL
echo Mo tool test...
%PY% regex_test_tool.py
if errorlevel 1 pause
exit /b 0
