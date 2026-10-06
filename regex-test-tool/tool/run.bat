@echo off
rem Tool test trich xuat van ban — nhan vien chi can nhap doi file nay.
rem Lan dau tu cai Python + thu vien (can mang 1 lan). Cac lan sau mo ngay.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY="
goto TIM_PYTHON

:TIM_PYTHON
where py >nul 2>&1
if errorlevel 1 goto TIM_PYTHON2
call :DU_PYTHON py -3
if not errorlevel 1 goto CO_PYTHON
goto TIM_PYTHON2

:TIM_PYTHON2
where python >nul 2>&1
if errorlevel 1 goto CAI_PYTHON
call :DU_PYTHON python
if not errorlevel 1 goto CO_PYTHON
goto CAI_PYTHON

:DU_PYTHON
%* -c "import sys"
if errorlevel 1 exit /b 1
%* -c "import sys; v = sys.version_info; raise SystemExit(0 if (v[0] > 3 or (v[0] == 3 and v[1] >= 10)) else 1)"
exit /b %errorlevel%

:CAI_PYTHON
echo [1/3] Chua thay Python tren may. Dang tai ve de cai dat (can mang lan nay)...
set "PYSETUP=%TEMP%\python-test-tool-setup.exe"
del "%PYSETUP%" >nul 2>&1
powershell -NoLogo -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $env:PYSETUP } catch { exit 1 }"
if errorlevel 1 goto LOI_MANG
if not exist "%PYSETUP%" goto LOI_MANG
if not exist "%PYSETUP%" goto LOI_MANG
echo [2/3] Dang cai Python (cho 2-3 phut, khong tat cua so)...
"%PYSETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PYSETUP%" >nul 2>&1
rem Moi cai xong, PATH cua cua so nay chua co Python moi.
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY (
  where py >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 set "PY=python"
)
if not defined PY goto LOI_CAI
call :DU_PYTHON %PY%
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
if not defined PY set "PY=py -3"
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
if not defined PY goto LOI_CAI
echo Mo tool test...
%PY% regex_test_tool.py
if errorlevel 1 pause
exit /b 0
