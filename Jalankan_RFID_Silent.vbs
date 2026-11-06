Dim WshShell, fso, scriptDir
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

WshShell.CurrentDirectory = scriptDir
' Angka 0 = tersembunyi / hidden (berjalan di background tanpa jendela CMD)
WshShell.Run "python reader.py", 0, False
