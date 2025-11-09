# FocusNote

An intelligent meeting assistant that automatically detects calls, transcribes conversations in real-time, and generates AI-powered summaries, meeting minutes, and action items.

## Overview

FocusNote is a desktop application that monitors your computer for active calls on Discord, Zoom, or Microsoft Teams. When a call is detected, it automatically:
- Records system audio and microphone input
- Transcribes speech in real-time using Whisper
- Generates meeting summaries, formal minutes, and action items using Gemini AI
- Saves all outputs organized by date and time

## Features

- **Automatic Call Detection**: Monitors Discord, Zoom, and Teams for active calls
- **Real-time Transcription**: Uses Whisper AI for accurate speech-to-text
- **Smart Audio Capture**: Records both system audio and microphone on macOS and Windows
- **AI-Powered Analysis**:
  - Concise meeting summaries
  - Formal meeting minutes
  - Actionable items with context
- **User-Friendly UI**: Clean PyQt6 interface with live status updates
- **Organized Output**: All transcripts and AI outputs saved with timestamps

## Architecture

FocusNote consists of three main components:

1. **Desktop App** (`DesktopApp/`): PyQt6 GUI application that handles call detection and audio recording
2. **Transcription Server** (`DesktopApp/src/transcription/`): Whisper-based real-time speech-to-text service
3. **Meeting Microservice** (`MeetingAssistant/`): Gemini AI service for generating summaries and action items

## Prerequisites

- **Python**: 3.11 or higher
- **Operating System**: macOS or Windows
- **ffmpeg**: Required for macOS audio capture
  ```bash
  # macOS
  brew install ffmpeg
  
  # Windows
  # Download from https://ffmpeg.org/download.html
  ```
- **Gemini API Key**: Required for AI features
  - Get one at [Google AI Studio](https://makersuite.google.com/app/apikey)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd focusnote
```

### 2. Set Up Desktop App
```bash
cd DesktopApp
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Meeting Microservice
```bash
cd ../MeetingAssistant
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the `MeetingAssistant` directory:

```bash
GEMINI_API_KEY=your_api_key_here
PORT=8888
```

**Important**: Never commit your `.env` file or API key to version control!

## Running FocusNote

### Quick Start (Recommended)

We provide startup scripts that launch all three components automatically in separate terminal windows.

#### macOS/Linux:
```bash
cd DesktopApp
bash scripts/start-all.sh
```

Or make it executable first:
```bash
chmod +x scripts/start-all.sh
./scripts/start-all.sh
```

#### Windows:
```bash
cd DesktopApp
scripts\start-all.bat
```

This will open **three terminal windows**:
1. **Transcription Server** - Whisper AI (port 17483)
2. **Meeting Microservice** - Gemini AI (port 8888)
3. **Desktop App** - FocusNote UI

### Manual Start (Alternative)

If you prefer to start components individually:

**Terminal 1 - Transcription Server:**
```bash
cd DesktopApp/src/transcription
python server.py
```

**Terminal 2 - Meeting Microservice:**
```bash
cd MeetingAssistant
python meeting_microservice.py
```

**Terminal 3 - Desktop App:**
```bash
cd DesktopApp/src
python main.py
```

## Usage

1. **Start the application** using one of the methods above
2. **Join a call** on Discord, Zoom, or Teams
3. **FocusNote automatically detects** the call and starts recording
4. **View live transcription** in the console
5. **When the call ends**, FocusNote automatically:
   - Stops recording
   - Sends transcript to AI service
   - Generates summary, minutes, and action items
   - Saves all outputs to `DesktopApp/meeting_output/`

## Output Files

All meeting data is saved in `DesktopApp/meeting_output/` organized by timestamp:

```
DesktopApp/meeting_output/
├── 2025-11-09T14:30:45/
│   ├── meeting_summary.txt      # AI-generated summary
│   ├── action_items.txt         # Extracted action items
│   └── meeting_minutes.txt      # Formal meeting minutes
└── meeting_recordings/
    └── meeting_discord_20251109_143045.wav
```

## Project Structure

```
focusnote/
├── DesktopApp/                     # Main desktop application
│   ├── src/
│   │   ├── main.py                 # Application entry point
│   │   ├── ui/                     # PyQt6 user interface
│   │   ├── audio/                  # Audio capture logic
│   │   ├── detection/              # Call detection (Discord, Zoom, Teams)
│   │   ├── transcription/          # Whisper transcription server
│   │   │   ├── server.py           # Transcription WebSocket server
│   │   │   └── websocket_client.py # Client for real-time transcription
│   │   └── api/                    # Microservice communication
│   ├── scripts/
│   │   ├── start-all.sh            # macOS/Linux startup script
│   │   └── start-all.bat           # Windows startup script
│   ├── meeting_output/             # AI-generated outputs (created automatically)
│   ├── meeting_recordings/         # Audio recordings (created automatically)
│   ├── requirements.txt            # Python dependencies
│   └── README.md
│
├── MeetingAssistant/               # AI microservice
│   ├── meeting_microservice.py     # FastAPI service
│   ├── test_service.py             # Test script
│   ├── requirements.txt            # Python dependencies
│   └── README.md
│
└── README.md                       # This file
```

## API Endpoints

The Meeting Microservice exposes the following endpoints:

### Generate Summary
```bash
POST http://localhost:8888/summary
```

### Generate Minutes
```bash
POST http://localhost:8888/minutes
```

### Extract Action Items
```bash
POST http://localhost:8888/action-items
```

### Health Check
```bash
GET http://localhost:8888/health
```

Request format:
```json
{
  "transcript": "Meeting transcript text...",
  "meeting_title": "Optional title",
  "meeting_date": "Optional date",
  "participants": ["Optional", "list"]
}
```

## Development

### Running Tests

Desktop App:
```bash
cd DesktopApp
pip install -r requirements-dev.txt
pytest
```

Meeting Microservice:
```bash
cd MeetingAssistant
python test_service.py
```

### Testing Audio Only
```bash
cd DesktopApp
python src/detection/detect_test.py --test
```

## Troubleshooting

### "GEMINI_API_KEY not configured"
- Ensure `.env` file exists in `MeetingAssistant/`
- Verify your API key is correct
- Restart the microservice after creating/updating `.env`

### "Address already in use"
- Port 8888 or 17483 is being used
- Change `PORT` in `.env` or kill the conflicting process

### Audio sounds fast/high-pitched
- This has been fixed in the latest version
- Sample rates are now properly matched (48kHz)
- Mono mic audio is converted to stereo for mixing

### Call not detected
- Ensure Discord/Zoom/Teams is actually in a call
- Check CPU usage is above the threshold (actively transmitting audio)
- Wait for 3 consecutive detections (3 seconds)

### No system audio on macOS
- Install ffmpeg: `brew install ffmpeg`
- Ensure microphone permissions are granted in System Preferences

### Connection errors
- Verify all three components are running
- Check the transcription server is on port 17483
- Check the meeting microservice is on port 8888
- Verify internet connection for Gemini API

## Platform-Specific Notes

### macOS
- Uses ffmpeg for system audio capture
- Requires microphone permissions
- Audio is captured at 48kHz stereo

### Windows
- Uses PyAudioWPatch for loopback audio
- May require running with administrator privileges
- Supports WASAPI loopback

## Security & Privacy

- All processing happens locally except AI generation
- Audio recordings stay on your machine
- Only transcripts are sent to Gemini API
- API keys are stored in `.env` files (git-ignored)
- No data is collected or transmitted to third parties

## Requirements

- Python 3.11+
- PyQt6
- PyAudio (Windows: PyAudioWPatch)
- Whisper (pywhispercpp)
- FastAPI
- Google Generative AI SDK
- ffmpeg (macOS)

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- Tests pass
- New features are documented
- No API keys in commits

## License

[Your License Here]

## Acknowledgments

- Whisper AI by OpenAI for transcription
- Google Gemini for AI analysis
- PyQt6 for the UI framework
- FastAPI for the microservice architecture

## Support

For issues and questions:
- Check the troubleshooting section above
- Review component-specific READMEs
- Create an issue on GitHub

---

**Made with focus. Powered by AI.**

