@echo off
echo Starting transcription server, meeting microservice & desktop app
echo Installing/updating dependencies...
echo.

REM Install DesktopApp dependencies
echo Checking DesktopApp dependencies...
cd "%~dp0\.."
pip install -q -r requirements.txt

REM Install MeetingAssistant dependencies
echo Checking MeetingAssistant dependencies...
cd "%~dp0\..\..\MeetingAssistant"
pip install -q -r requirements.txt

echo Dependencies up to date!
echo.

cd "%~dp0\..\src\transcription"
start cmd /k "echo Starting transcription server... & python3 server.py"

cd "%~dp0\..\..\MeetingAssistant"
start cmd /k "echo Starting meeting microservice... & python3 meeting_microservice.py"

cd "%~dp0\..\src"
start cmd /k "echo Starting desktop app... & python3 main.py"

echo All three processes started in separate windows

