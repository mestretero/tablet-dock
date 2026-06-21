' Dock tepsi uygulamasini TAMAMEN gizli baslatir (hicbir pencere/konsol yok).
' Cift tikla -> saat yaninda tepsi ikonu cikar.
' Otomatik baslatma: bu .vbs'nin kisayolunu Win+R -> shell:startup klasorune birak.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.Run "pythonw """ & scriptDir & "\dock_tray.pyw""", 0, False
