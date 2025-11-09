import asyncio
import websockets
import json
import numpy as np
import wave
import sys


async def send_audio_file(audio_file_path, chunk_duration=1.3, overlap=0.2):
    """
    Test client that reads an audio file and sends it to the WebSocket server
    """
    uri = "ws://localhost:17483"

    try:
        # Read the audio file
        print(f"Reading audio file: {audio_file_path}")
        with wave.open(audio_file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()

            print(f"Sample rate: {sample_rate} Hz")
            print(f"Channels: {n_channels}")
            print(f"Sample width: {sample_width} bytes")
            print(f"Duration: {n_frames / sample_rate:.2f} seconds")

            # Read all audio data
            audio_bytes = wf.readframes(n_frames)

            # Convert to numpy array
            if sample_width == 2:  # 16-bit PCM
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                # Convert to float32 and normalize to [-1.0, 1.0]
                audio_data = audio_data.astype(np.float32) / 32768.0
            else:
                print(f"Unsupported sample width: {sample_width}")
                return

            # Convert stereo to mono if needed
            if n_channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                print(f"Resampling from {sample_rate} Hz to 16000 Hz...")
                import scipy.signal

                num_samples = int(len(audio_data) * 16000 / sample_rate)
                audio_data = scipy.signal.resample(audio_data, num_samples)
                sample_rate = 16000

        # Connect to WebSocket server
        print(f"\nConnecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending audio chunks...\n")

            # Calculate chunk sizes
            chunk_size = int(chunk_duration * sample_rate)
            overlap_size = int(overlap * sample_rate)
            step_size = chunk_size - overlap_size

            # Send audio in chunks
            position = 0
            chunk_num = 0

            while position < len(audio_data):
                # Get chunk
                end_pos = min(position + chunk_size, len(audio_data))
                chunk = audio_data[position:end_pos]

                # Pad with zeros if chunk is too short
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

                # Convert to bytes and send
                chunk = np.array(chunk, dtype=np.float32)
                chunk_bytes = chunk.tobytes()
                await websocket.send(chunk_bytes)

                chunk_num += 1
                print(f"Sent chunk {chunk_num} ({len(chunk)} samples)")

                # Listen for responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    result = json.loads(response)
                    if result.get("type") == "transcription":
                        print(f"  → Transcription: {result['text']}")
                    elif result.get("type") == "error":
                        print(f"  → Error: {result['message']}")
                except asyncio.TimeoutError:
                    print("  → No response received")

                # Move to next chunk
                position += step_size

                # Small delay to simulate real-time streaming

            print("\nFinished sending audio!")
            await websocket.close()

    except FileNotFoundError:
        print(f"Error: Audio file not found: {audio_file_path}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <audio_file.wav>")
        print("\nNote: Audio file should be in WAV format")
        sys.exit(1)

    audio_file = sys.argv[1]
    asyncio.run(send_audio_file(audio_file))
