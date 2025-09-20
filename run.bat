@echo off
.\.venv\Scripts\python.exe main.py ^
  --driver edge ^
  --driver-path .\msedgedriver.exe ^
  --commands .\command\cmd1.txt ^
  --maximize ^
  --netlog "%CD%\logs\netlog.json"
pause