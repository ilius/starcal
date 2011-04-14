@echo off
for %%F in (%0) do set rootDir=%%~dpF

set ui=qt

if not exist %APPDATA%\starcal2 (
    %rootDir%\run.bat scal2\ui_%ui%\config_importer.py
)

%rootDir%\run.bat scal2\ui_%ui%\starcal_%ui%.py

