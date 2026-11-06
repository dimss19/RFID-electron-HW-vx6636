@echo off
title Status RFID Scanner (Background)
color 0B
echo ============================================================
echo           STATUS RFID SCANNER BACKGROUND
echo ============================================================
echo.

tasklist /FI "IMAGENAME eq RFID_Scanner.exe" 2>NUL | find /I /N "RFID_Scanner.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [STATUS] AKTIF!
    echo Aplikasi RFID Scanner SEDANG BERJALAN di latar belakang.
    echo Setiap kartu di-scan akan otomatis ter-paste ke form web.
) else (
    echo [STATUS] TIDAK AKTIF!
    echo Aplikasi RFID Scanner saat ini TIDAK BERJALAN di background.
    echo Klik 2x file RFID_Scanner.exe untuk menyalakannya.
)

echo.
pause

