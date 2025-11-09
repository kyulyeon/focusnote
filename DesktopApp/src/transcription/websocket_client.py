import asyncio
import websockets
import json
import threading
import numpy as np
import requests
import os
from datetime import datetime


class TranscriptionWebSocketClient:
    def __init__(self, audio_capture, server_url="ws://localhost:17483"):
        self.audio_capture = audio_capture
        self.server_url = server_url
        self.running = False
        self.websocket = None
        self.thread = None
        self.loop = None
        self.transcript = ""

    def start(self):
        """Start the transcription client in a separate thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        print(f"Transcription client started, connecting to {self.server_url}")

    def stop(self):
        """Stop the transcription client"""
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=2)
        print("Transcription client stopped")
        
        # Send transcript to meeting assistant service if we have any transcript
        if self.transcript.strip():
            self._send_to_meeting_service()
    
    def flush_transcript(self):
        """Send accumulated transcript to meeting service and reset (without stopping)"""
        if self.transcript.strip():
            print(f"\nFlushing transcript (recording ended)...")
            self._send_to_meeting_service()
            # Reset transcript for next recording
            self.transcript = ""
        else:
            print("No transcript to flush")
    
    #send to api to send to gmeini 
    def _send_to_meeting_service(self):
        """Send the accumulated transcript to the meeting assistant service"""
        base_url = "http://localhost:8888"
        endpoints = ["/summary", "/action-items", "/minutes"]

               # Prepare the request payload
        payload = {
            "transcript": self.transcript.strip(),
            "meeting_date": datetime.now().isoformat()
        }
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "meeting_output",payload["meeting_date"].split(".")[0])
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
 
        print(f"\nSending transcript to meeting assistant service...")
        print(f"Transcript length: {len(self.transcript)} characters")
        print(f"Output directory: {output_dir}\n")
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"Requesting {endpoint}...")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"{endpoint}: Success")
                    # Print the result in a nice format
                    if endpoint == "/summary":
                        summary = result.get('summary', 'N/A')
                        print(f"Summary: {summary[:100]}...")
                        summary_path = os.path.join(output_dir, "meeting_summary.txt")
                        with open(summary_path, "w") as f:
                            f.write(summary)
                        print(f"Saved to: {summary_path}")
                    elif endpoint == "/action-items":
                        action_items = result.get('action_items', [])
                        print(f"Action items: {len(action_items)} found")
                        actions_path = os.path.join(output_dir, "action_items.txt")
                        with open(actions_path, "w") as f:
                            for item in action_items:
                                f.write(f"- {item}\n")
                        print(f"Saved to: {actions_path}")
                        
                    elif endpoint == "/minutes":
                        minutes = result.get('minutes', '')
                        print(f"Minutes generated successfully")
                        minutes_path = os.path.join(output_dir, "meeting_minutes.txt")
                        with open(minutes_path, "w") as f:
                            f.write(minutes)
                        print(f"Saved to: {minutes_path}")
                else:
                    print(f"{endpoint}: Failed (status {response.status_code})")
                    
            except requests.exceptions.ConnectionError:
                print(f"{endpoint}: Connection failed (is the service running?)")
            except requests.exceptions.Timeout:
                print(f"{endpoint}: Request timeout")
            except Exception as e:
                print(f"{endpoint}: Error - {e}")
        
        print(f"\nMeeting assistant requests completed\n")

    def _run_async_loop(self):
        """Run the asyncio event loop in this thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._transcription_loop())
        except Exception as e:
            print(f"Transcription loop error: {e}")
        finally:
            self.loop.close()

    async def _transcription_loop(self):
        """Main loop that sends audio chunks to the server"""
        retry_delay = 5

        while self.running:
            try:
                async with websockets.connect(self.server_url) as websocket:
                    self.websocket = websocket
                    print("Connected to transcription server")

                    # Audio buffer for accumulating chunks
                    audio_buffer = []
                    target_duration = 5.0  # Accumulate 5 seconds of audio
                    current_sample_rate = None
                    current_channels = None

                    while self.running:
                        # Get audio chunk from AudioCapture (non-blocking)
                        chunk_data = await asyncio.get_event_loop().run_in_executor(
                            None,
                            self.audio_capture.get_audio_chunk,
                            0.1,  # 100ms timeout
                        )

                        if chunk_data is None:
                            # No audio available, sleep briefly
                            await asyncio.sleep(0.1)
                            continue

                        audio_bytes, sample_rate, channels = chunk_data
                        current_sample_rate = sample_rate
                        current_channels = channels

                        # Add to buffer
                        audio_buffer.append(audio_bytes)

                        # Calculate total samples (accounting for channels and bytes per sample)
                        total_bytes = sum(len(chunk) for chunk in audio_buffer)
                        total_samples = total_bytes // (
                            channels * 2
                        )  # 2 bytes per sample (int16)
                        
                        # Calculate duration based on original sample rate
                        duration_seconds = total_samples / sample_rate

                        # Send when buffer has enough duration (accounts for resampling)
                        if duration_seconds >= target_duration:
                            print(f"Accumulated {duration_seconds:.1f}s of audio, sending to transcription...")
                            await self._send_buffer(
                                audio_buffer, current_sample_rate, current_channels
                            )
                            audio_buffer = []

            except websockets.exceptions.ConnectionClosed:
                print(f"Connection closed, reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                print(f"Connection error: {e}")
                import traceback

                traceback.print_exc()
                await asyncio.sleep(retry_delay)

        self.websocket = None

    async def _send_buffer(self, audio_buffer, sample_rate, channels):
        """Convert buffer to float32 and send to server"""
        try:
            # Combine all chunks
            combined_bytes = b"".join(audio_buffer)

            # Convert from int16 to numpy array
            int16_data = np.frombuffer(combined_bytes, dtype=np.int16)

            # If stereo, convert to mono by averaging channels
            if channels == 2:
                int16_data = int16_data.reshape(-1, 2).mean(axis=1).astype(np.int16)

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                int16_data = self._resample_int16(int16_data, sample_rate, 16000)

            # Convert to float32 normalized to [-1, 1]
            float32_data = int16_data.astype(np.float32) / 32768.0

            # Ensure we have at least 2 seconds (server requirement)
            min_samples = int(16000 * 2)
            if len(float32_data) < min_samples:
                # Pad with zeros if slightly short
                padding = min_samples - len(float32_data)
                float32_data = np.pad(float32_data, (0, padding), mode='constant')
                print(
                    f"Buffer slightly short, padded {padding} samples to reach {min_samples}"
                )

            # Ensure we don't exceed reasonable limits (10 seconds max)
            max_samples = int(16000 * 10)
            if len(float32_data) > max_samples:
                print(
                    f"Buffer too long ({len(float32_data)} samples), truncating to {max_samples}"
                )
                float32_data = float32_data[:max_samples]

            # Send as bytes
            audio_bytes = float32_data.tobytes()

            duration = len(float32_data) / 16000
            print(f"Sending {len(float32_data)} samples ({duration:.1f}s)")

            if self.websocket:
                await self.websocket.send(audio_bytes)

                # Listen for transcription response
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0,  # Increased timeout
                    )
                    data = json.loads(response)
                    if data.get("type") == "transcription":
                        text = data.get("text", "").strip()
                        if text:
                            print(f"Transcription: {text}")
                            self.transcript +=  text + " "
                except asyncio.TimeoutError:
                    print("Transcription timeout (server may be processing)")
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"Error sending audio: {e}")
            import traceback

            traceback.print_exc()

    def _resample_int16(self, audio, orig_sr, target_sr):
        """Resample int16 audio using linear interpolation"""
        if orig_sr == target_sr:
            return audio

        # Calculate target length
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)

        # Linear interpolation
        indices = np.linspace(0, len(audio) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)

        return resampled.astype(np.int16)

