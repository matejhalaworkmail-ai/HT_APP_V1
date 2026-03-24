' Skript pro vytvoreni zkratky TZ Databaze na plochu
' Dvakrat klikni na tento soubor - zkratka se vytvori automaticky

Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strAppDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

Set oShortCut = WshShell.CreateShortcut(strDesktop & "\TZ Databaze.lnk")
oShortCut.TargetPath = strAppDir & "run.bat"
oShortCut.WorkingDirectory = strAppDir
oShortCut.Description = "TZ Databaze - Heat Treatment"
oShortCut.WindowStyle = 1
oShortCut.Save

MsgBox "Zkratka 'TZ Databaze' byla vytvorena na plochu!", vbInformation, "Hotovo"
