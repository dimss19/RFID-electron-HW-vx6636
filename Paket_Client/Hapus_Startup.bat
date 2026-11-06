@echo off
title Hapus RFID Scanner dari Windows Startup
echo ============================================================
echo      MENGHAPUS RFID SCANNER DARI STARTUP WINDOWS
echo ============================================================
echo.

powershell -NoProfile -Command ^
  "$StartupFolder = [Environment]::GetFolderPath('Startup'); " ^
  "$Path1 = \"$StartupFolder\RFID Scanner.lnk\"; " ^
  "$Path2 = \"$StartupFolder\RFID_Reader.lnk\"; " ^
  "if (Test-Path $Path1) { Remove-Item $Path1 -Force; Write-Host '[BERHASIL] Shortcut berhasil dihapus dari Startup.' } " ^
  "elseif (Test-Path $Path2) { Remove-Item $Path2 -Force; Write-Host '[BERHASIL] Shortcut berhasil dihapus dari Startup.' } " ^
  "else { Write-Host '[INFO] Shortcut tidak ditemukan di Startup.' }"

echo.
pause
