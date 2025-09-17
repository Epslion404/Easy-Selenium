@echo off

.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
.\.venv\Scripts\python.exe -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

.\.venv\Scripts\python.exe -m pip install selenium

.\.venv\Scripts\python.exe --version
echo Done!
pause