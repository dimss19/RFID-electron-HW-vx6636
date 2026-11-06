@echo off
title Matikan RFID Scanner (Background)
color 0C
echo ============================================================
echo         MENGHENTIKAN RFID SCANNER BACKGROUND
echo ============================================================
echo.

taskkill /F /IM RFID_Scanner.exe >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [BERHASIL] Aplikasi RFID Scanner background telah dihentikan!
) else (
    echo [INFO] Aplikasi RFID Scanner tidak sedang berjalan di background.
)

echo.
pause
