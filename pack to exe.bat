@echo off
:: .\.venv\Scripts\python.exe -m nuitka --mingw64 --standalone --output-dir=release-exe --show-progress --onefile --plugin-enable=upx --enable-plugin=tk-inter --plugin-enable=numpy --plugin-enable=matplotlib --windows-console-mode=disable --upx-binary --windows-icon-from-ico=favicon.ico ---windows-uac-admin main.py
:: .\.venv\Scripts\python.exe -m nuitka --mingw64 --standalone --onefile --output-dir=release-exe --windows-console-mode=disable --windows-icon-from-ico=favicon.ico --windows-uac-admin --enable-plugin=tk-inter main.py
.\.venv\Scripts\python.exe -m nuitka --mingw64 --standalone --onefile --output-dir=release-exe main.py

pause