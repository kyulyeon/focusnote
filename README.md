# Meeting Transcript Microservice

A Python microservice that uses Google's Gemini AI to process meeting transcripts and generate summaries, meeting minutes, and action items.

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/meeting-transcript-service.git
cd meeting-transcript-service
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or with a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Get a Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_api_key_here
PORT=8888
```

### 5. Run the Service
```bash
python main.py
```

The service will start at `http://localhost:8888`

## Testing

Run the included test script:
```bash
python test_service.py
```

Or visit the interactive API documentation:
```
http://localhost:8888/docs
```

## API Endpoints

### Generate Summary
```bash
POST /api/v1/summary
```
Creates a concise summary of the meeting.

### Generate Minutes
```bash
POST /api/v1/minutes
```
Generates formal meeting minutes with discussion points and decisions.

### Extract Action Items
```bash
POST /api/v1/action-items
```
Extracts action items with owners and deadlines.

### Health Check
```bash
GET /health
```
Check service status.

## Request Format

All endpoints accept JSON with the following structure:

```json
{
  "transcript": "Your meeting transcript here...",
  "meeting_title": "Optional meeting title",
  "meeting_date": "Optional date (YYYY-MM-DD)",
  "participants": ["Optional", "List", "Of", "Participants"]
}
```

Only `transcript` is required.

## Example Usage

```bash
curl -X POST http://localhost:8888/api/v1/summary \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "John: We need to increase the marketing budget. Sarah: I agree, I propose 20% more for Q4. John: Approved, make it happen.",
    "meeting_title": "Q4 Budget Review"
  }'
```

## Project Structure

```
meeting-transcript-service/
├── main.py              # Main service
├── test_service.py      # Test script
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (create this)
├── .env.example        # Example env file
└── README.md           # This file
```

## Troubleshooting

**"GEMINI_API_KEY not configured"**
- Make sure `.env` file exists in the project root
- Verify `GEMINI_API_KEY` is set in `.env`
- Restart the service after creating/updating `.env`

**"Address already in use"**
- Port 8888 is being used by another application
- Change `PORT` in `.env` to a different port (e.g., 8889)

**Module not found errors**
- Install dependencies: `pip install -r requirements.txt`
- Make sure your virtual environment is activated

**Connection errors to Gemini API**
- Verify your API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check your internet connection
- Verify you haven't exceeded API rate limits

## Requirements

- Python 3.11+
- Valid Gemini API key
- Internet connection

## Notes

- The service runs locally only (127.0.0.1)
- `.env` file is git-ignored for security
- Never commit your API key to version control

## Stop the Service

Press `Ctrl+C` in the terminal where the service is running.
