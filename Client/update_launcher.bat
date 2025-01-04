@echo off
REM Run the installer

if "%~1"=="" (
    exit /b 1
)

set "installer_path=%~1"

if exist "%installer_path%" (
    start /wait "" "%installer_path%" /VERYSILENT  REM Run the installer silently and wait for it to complete
    
    if %errorlevel% equ 0 (
        del "%installer_path%"
    )
) else (
    exit /b 1
)
