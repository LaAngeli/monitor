@echo off
start /B pythonw youtube_monitor_gui.py
exit

:: Setează iconița
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%~dpnx0'); $sc.IconLocation = 'C:\Windows\System32\imageres.dll,67'; $sc.Save()" 