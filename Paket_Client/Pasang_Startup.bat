@echo off
title Pasang RFID Scanner ke Windows Startup
echo ============================================================
echo      MEMASANG RFID SCANNER KE WINDOWS STARTUP
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXE_TARGET=%SCRIPT_DIR%RFID_Scanner.exe"

if not exist "%EXE_TARGET%" (
    echo [ERROR] File RFID_Scanner.exe tidak ditemukan di folder ini!
    pause
    exit /b 1
)

powershell -NoProfile -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; " ^
  "$StartupFolder = [Environment]::GetFolderPath('Startup'); " ^
  "$Shortcut = $WshShell.CreateShortcut(\"$StartupFolder\RFID Scanner.lnk\"); " ^
  "$Shortcut.TargetPath = '%EXE_TARGET%'; " ^
  "$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; " ^
  "$Shortcut.Description = 'RFID HW-VX6336 Scanner'; " ^
  "$Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo [BERHASIL] Shortcut berhasil dipasang ke Windows Startup!
    echo Aplikasi akan otomatis berjalan setiap komputer dinyalakan.
) else (
    echo [GAGAL] Gagal membuat shortcut di Startup.
)

echo.
pause
