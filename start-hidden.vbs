Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\Projects\apleith\weight-tracker"
WshShell.Run """E:\Projects\apleith\weight-tracker\.venv\Scripts\pythonw.exe"" run.py all", 0, False
