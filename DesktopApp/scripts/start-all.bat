@echo off
echo starting server & desktop app


cd "%~dp0\..\transcriptions"
start cmd /k "echo starting server & python3 server.py"

cd "%~dp0\..\src"
start cmd /k "starting the desktop app & python3 main.py"


