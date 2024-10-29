@echo off
REM Run the installer

if "%~1"=="" (
    echo No installer path provided.
    exit /b 1
)

set "installer_path=%~1"

if exist "%installer_path%" (
    echo Starting the installer...
    start /wait "" "%installer_path%"  REM Run the installer and wait for it to complete
    
    if %errorlevel% equ 0 (
        echo Installer finished successfully. Cleaning up...
        del "%installer_path%"
        echo Update file removed.
    ) else (
        echo Installer encountered an error. Update file will not be removed.
    )
) else (
    echo Installer file does not exist: %installer_path%
    exit /b 1
)
