@echo off
rem GIA LAP MAY TRANG (khong thay Python) de test nhanh cai dat.
rem Chi dung de test — nhan vien khong can file nay.
rem Cach dung: nhap doi file nay, no se chay run.bat nhu the may chua cai Python.
setlocal
set "PATH=C:\Windows\System32;C:\Windows\System32\WindowsPowerShell\v1.0"
call "%~dp0run.bat"
endlocal
