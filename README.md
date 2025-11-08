# Call Transcriber

Desktop application for transcribing Discord and Zoom calls in real-time.

## Features
- Detects active calls on Discord and Zoom
- Real-time speech-to-text transcription
- Sends transcriptions to microservice

## Prerequisites
- Python 3.9+
- Virtual audio device (VB-Cable for Windows, BlackHole for macOS)

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure

## Usage
```bash
python src/main.py
```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run tests:
```bash
pytest
```

## Project Structure
```
call-transcriber/
├── src/
│   ├── main.py              # Application entry point
│   ├── ui/                  # PyQt6 UI components
│   ├── audio/               # Audio capture logic
│   ├── detection/           # Process detection
│   ├── transcription/       # Speech-to-text
│   └── api/                 # Microservice communication
├── tests/                   # Unit tests
├── config/                  # Configuration files
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

## License

MIT