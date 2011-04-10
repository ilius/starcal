@echo off
for %%F in (%0) do set rootDir=%%~dpF

if not exist %APPDATA%\starcal2 (
  set IMP=scal2\ui_qt\config_importer.pyw
  if exist %rootDir%\%IMP% (
    %rootDir%\run.bat %IMP%
  )
)

%rootDir%\run.bat scal2\ui_qt\starcal_qt.pyw

