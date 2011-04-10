@echo off
for %%F in (%0) do set rootDir=%%~dpF
set PYTHONPATH=%PYTHONPATH%;%rootDir%
C:\Python27\python.exe %rootDir%\%1 %2 %3