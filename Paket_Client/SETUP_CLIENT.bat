@echo off
title Setup RFID Reader - Client
color 0A
echo ====================================================================
echo             SETUP APLIKASI RFID UHF HW-VX6336 (CLIENT)
echo ====================================================================
echo.
echo Selamat datang di installer RFID Keyboard Wedge.
echo Installer ini akan:
echo   1. Membuat icon shortcut di Desktop (Layar Utama) komputer Anda.
echo   2. Opsi untuk mengaktifkan otomatis saat komputer dinyalakan.
echo.
echo ====================================================================
pause

set "SCRIPT_DIR=%~dp0"
set "EXE_TARGET=%SCRIPT_DIR%RFID_Scanner.exe"

if not exist "%EXE_TARGET%" (
    if exist "%SCRIPT_DIR%Jalankan_RFID.bat" (
        set "EXE_TARGET=%SCRIPT_DIR%Jalankan_RFID.bat"
    ) else (
        echo [ERROR] File RFID_Scanner.exe atau Jalankan_RFID.bat tidak ditemukan!
        pause
        exit /b 1
    )
)

echo.
echo [1/2] Membuat Shortcut di Desktop...
powershell -NoProfile -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; " ^
  "$Desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$Shortcut = $WshShell.CreateShortcut(\"$Desktop\RFID Scanner.lnk\"); " ^
  "$Shortcut.TargetPath = '%EXE_TARGET%'; " ^
  "$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; " ^
  "$Shortcut.Description = 'Aplikasi Pembaca RFID UHF HW-VX6336'; " ^
  "$Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Shortcut 'RFID Scanner' berhasil dibuat di Desktop!
) else (
    echo [!] Gagal membuat shortcut di Desktop.
)

echo.
echo [2/2] Pengaturan Auto-Startup:
echo Apakah Anda ingin aplikasi ini otomatis berjalan setiap Windows menyala?
echo   [Y] Ya, jalankan otomatis saat komputer dinyalakan (Direkomendasikan)
echo   [T] Tidak, saya akan klik manual dari Desktop saat butuh
echo.
set /p startup_choice="Pilihan Anda (Y/T, default Y): "

if /i "%startup_choice%"=="T" (
    echo [INFO] Auto-startup dilewati.
) else (
    powershell -NoProfile -Command ^
      "$WshShell = New-Object -ComObject WScript.Shell; " ^
      "$Startup = [Environment]::GetFolderPath('Startup'); " ^
      "$Shortcut = $WshShell.CreateShortcut(\"$Startup\RFID Scanner.lnk\"); " ^
      "$Shortcut.TargetPath = '%EXE_TARGET%'; " ^
      "$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; " ^
      "$Shortcut.Description = 'Aplikasi Pembaca RFID UHF HW-VX6336 Auto-Start'; " ^
      "$Shortcut.Save()"
    echo [OK] Berhasil didaftarkan ke Windows Startup!
)

echo.
echo ====================================================================
echo                        SETUP SELESAI!
echo ====================================================================
echo.
echo Anda sekarang bisa langsung membuka aplikasi melalui icon
echo 'RFID Scanner' yang ada di Desktop komputer Anda.
echo.
pause
