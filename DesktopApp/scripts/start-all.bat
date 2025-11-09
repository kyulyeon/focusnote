@echo off
echo Starting transcription server, meeting microservice & desktop app


cd "%~dp0\..\src\transcription"
start cmd /k "echo Starting transcription server... & python3 server.py"

cd "%~dp0\..\..\MeetingAssistant"
start cmd /k "echo Starting meeting microservice... & python3 meeting_microservice.py"

cd "%~dp0\..\src"
start cmd /k "echo Starting desktop app... & python3 main.py"

echo All three processes started in separate windows

