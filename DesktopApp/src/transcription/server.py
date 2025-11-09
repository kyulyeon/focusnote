import re
import asyncio
import websockets
import json
import numpy as np
import time
from pywhispercpp.model import Model

host = "localhost"
port = 17483
model = Model("large-v3")


class AudioServer:
    def __init__(self):
        self.host = host
        self.port = port
        self.model = model
        self.sample_rate = 16000

    # handling the incoming websockets
    async def handle_client(self, websocket):
        print(f"Client connected from {websocket.remote_address}")
        full_transcript = ""

        try:
            async for message in websocket:
                # Handle binary audio data (pre-chunked from client)
                if isinstance(message, bytes):
                    chunk_text = await self.transcribe_chunk(message, websocket)
                    print(chunk_text)
                    full_transcript += chunk_text + " "
                # Handle JSON control messages
                elif isinstance(message, str):
                    await self.handle_control_message(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected: {websocket.remote_address}")

        except Exception as e:
            print(f"Error handling client: {e}")
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))
        finally:
            # transcribe pre-chunked audio from client
            print("\n" + "final transcript" + "\n")
            print(full_transcript)

    async def transcribe_chunk(self, audio_data, websocket):
        chunk_text = ""

        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            duration = len(audio_array) / self.sample_rate

            # 1.5 so it doesnt complain
            min_samples = int(self.sample_rate * 1.5)
            if len(audio_array) < min_samples:
                print(f"  Audio too short ({duration:.1f}s), skipping")
                return ""
            # Send chunk to model for transcription
            segments = self.model.transcribe(audio_array)

            # Send transcription results back to client
            for segment in segments:
                chunk_text += segment.text + ""
                result = {
                    "type": "transcription",
                    "text": segment.text,
                    "start": segment.t0,
                    "end": segment.t1,
                    "timestamp": time.time(),
                }
                await websocket.send(json.dumps(result))

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            await websocket.send(
                json.dumps(
                    {"type": "error", "message": f"Transcription error: {str(e)}"}
                )
            )

        return chunk_text

    async def handle_control_message(self, message, websocket):
        """Handle control messages from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

        except json.JSONDecodeError:
            print(f"Invalid JSON message: {message}")
        except Exception as e:
            print(f"Error handling control message: {e}")

    async def start(self):
        """Start the WebSocket server"""
        print(f"Starting audio transcription server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"Server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  


def main():
    server = AudioServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down server...")


if __name__ == "__main__":
    main()
