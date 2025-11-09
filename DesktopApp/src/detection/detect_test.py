import wave
import psutil
import time
import threading
from datetime import datetime
import os
import sys
import platform
import struct
import queue
import subprocess


# Import appropriate audio library based on OS
SYSTEM = platform.system()

if SYSTEM == "Windows":
    try:
        import pyaudiowpatch as pyaudio

        AUDIO_BACKEND = "pyaudiowpatch"
    except ImportError:
        print("⚠️  PyAudioWPatch not found. Install with: pip install pyaudiowpatch")
        import pyaudio

        AUDIO_BACKEND = "pyaudio"
elif SYSTEM == "Darwin":  # macOS
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if (
            "blackhole" in dev["name"].lower()
            or "soundflower" in dev["name"].lower()
        ):
            self.speaker_device = dev
            print(f"🔊 macOS virtual device: {dev['name']}")
            break

    try:
        default_mic = p.get_default_input_device_info()
        self.mic_device = default_mic
        print(f"🎤 Microphone: {default_mic['name']}")
    except Exception as e:
        print(f"⚠️  Could not setup microphone: {e}")
else:  # Linux
    try:
        import pyaudio

        AUDIO_BACKEND = "pyaudio"
    except ImportError:
        print("⚠️  PyAudio not found. Install with: pip install pyaudio")
        sys.exit(1)


class AudioCapture:
    def __init__(self, output_dir="meeting_recordings"):
        self.output_dir = output_dir
        self.is_recording = False
        self.audio_thread = None
        self.running = False
        self.stream_speaker = None
        self.stream_mic = None
        self.p = None

        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.rate = 48000

        os.makedirs(output_dir, exist_ok=True)

        self.in_call = False
        self.active_platform = None

        # CPU threshold for detecting active calls
        self.cpu_threshold = 3.5
        self.discord_cpu_threshold = 5.0

        # Track consecutive detections
        self.call_detected_count = 0
        self.call_detection_threshold = 3

        # Inactivity threshold
        self.inactive_count = 0
        self.inactive_threshold = 3  # User preference: 3 seconds

        # Audio streaming queue for transcription
        self.audio_stream_queue = queue.Queue(maxsize=100)

        # Callback for real-time audio processing
        self.audio_callback = None
        # macOS ffmpeg process
        self.ffmpeg_process = None
        self.ffmpeg_thread = None
        self.ffmpeg_queue = queue.Queue(maxsize=50)
        # Audio device setup
        self.speaker_device = None
        self.mic_device = None
        self.setup_audio_devices()

        print(f"🖥️  Platform: {SYSTEM}")
        print(f"🎵 Audio backend: {AUDIO_BACKEND}\n")
def start_ffmpeg_capture(self):
    """Start ffmpeg system audio capture for macOS"""
    if SYSTEM != "Darwin":
        return
    
    try:
        # Start capturing
        cmd = [
            'ffmpeg',
            '-f', 'avfoundation',
            '-i', ':0',  # Audio device
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ar', str(self.rate),
            '-ac', '2',
            'pipe:1'
        ]
        
        self.ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8
        )
        
        print(f"✅ ffmpeg system audio capture started")
        
        # Start thread to read from ffmpeg
        def read_ffmpeg():
            chunk_size = self.chunk * 2 * 2  # samples * channels * bytes
            while self.is_recording and self.ffmpeg_process:
                try:
                    raw_data = self.ffmpeg_process.stdout.read(chunk_size)
                    if not raw_data:
                        break
                    try:
                        self.ffmpeg_queue.put_nowait(raw_data)
                    except queue.Full:
                        pass
                except Exception as e:
                    if self.is_recording:
                        print(f"⚠️  ffmpeg read error: {e}")
                    break
        
        self.ffmpeg_thread = threading.Thread(target=read_ffmpeg, daemon=True)
        self.ffmpeg_thread.start()
        
    except FileNotFoundError:
        print("❌ ffmpeg not found. Install with: brew install ffmpeg")
        print("   Falling back to microphone only")
    except Exception as e:
        print(f"⚠️  Could not start ffmpeg: {e}")

def stop_ffmpeg_capture(self):
    """Stop ffmpeg system audio capture"""
    if self.ffmpeg_process:
        try:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait(timeout=2)
        except:
            try:
                self.ffmpeg_process.kill()
            except:
                pass
        self.ffmpeg_process = None
    
    if self.ffmpeg_thread and self.ffmpeg_thread.is_alive():
        self.ffmpeg_thread.join(timeout=1)
    def set_audio_callback(self, callback):
        """
        Set a callback function that will be called with each audio chunk
        callback should accept: (audio_data: bytes, sample_rate: int, channels: int)
        """
        self.audio_callback = callback

    def get_audio_chunk(self, timeout=None):
        """
        Get the next audio chunk from the queue (blocking)
        Returns: (audio_data: bytes, sample_rate: int, channels: int) or None if timeout
        """
        try:
            return self.audio_stream_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def setup_audio_devices(self):
        """Setup both speaker loopback AND microphone"""
        try:
            p = pyaudio.PyAudio()

            if SYSTEM == "Windows" and AUDIO_BACKEND == "pyaudiowpatch":
                # Get speaker loopback (for other people's audio)
                try:
                    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                    default_speakers = p.get_device_info_by_index(
                        wasapi_info["defaultOutputDevice"]
                    )

                    if not default_speakers["isLoopbackDevice"]:
                        for loopback in p.get_loopback_device_info_generator():
                            if default_speakers["name"] in loopback["name"]:
                                self.speaker_device = loopback
                                print(f"🔊 Speaker loopback: {loopback['name']}")
                                break
                    else:
                        self.speaker_device = default_speakers
                        print(f"🔊 Speaker loopback: {default_speakers['name']}")
                except Exception as e:
                    print(f"⚠️  Could not setup speaker loopback: {e}")

                # Get microphone (for your voice)
                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"🎤 Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"⚠️  Could not setup microphone: {e}")

            elif SYSTEM == "Darwin":  # macOS
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    if (
                        "blackhole" in dev["name"].lower()
                        or "soundflower" in dev["name"].lower()
                    ):
                        self.speaker_device = dev
                        print(f"🔊 macOS virtual device: {dev['name']}")
                        break

                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"🎤 Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"⚠️  Could not setup microphone: {e}")

            else:  # Linux
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    if "monitor" in dev["name"].lower() and dev["maxInputChannels"] > 0:
                        self.speaker_device = dev
                        print(f"🔊 Linux monitor device: {dev['name']}")
                        break

                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"🎤 Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"⚠️  Could not setup microphone: {e}")

            p.terminate()

            if not self.speaker_device and not self.mic_device:
                print("⚠️  Warning: Could not find any audio devices")
            elif not self.speaker_device:
                print("⚠️  Warning: No speaker loopback (recording mic only)")
            elif not self.mic_device:
                print("⚠️  Warning: No microphone (recording speakers only)")

        except Exception as e:
            print(f"⚠️  Warning: Could not initialize audio: {e}")

    def get_process_names(self, base_names):
        """Get platform-specific process names"""
        if SYSTEM == "Windows":
            return [
                f"{name}.exe" if not name.endswith(".exe") else name
                for name in base_names
            ]
        return base_names

    def is_process_active(self, process_names, cpu_threshold=3.5):
        """Check if process is running AND using significant CPU"""
        platform_names = self.get_process_names(process_names)

        for proc in psutil.process_iter(["name", "cpu_percent"]):
            try:
                proc_name = proc.info["name"].lower()
                if proc_name in [p.lower() for p in platform_names]:
                    cpu = proc.cpu_percent(interval=0.1)
                    if cpu > cpu_threshold:
                        return True, proc_name, cpu
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None, 0

    def detect_discord_call(self):
        """Detect active Discord call"""
        process_names = ["discord.exe", "discord", "Discord"]
        max_cpu = 0
        has_udp = False

        for proc in psutil.process_iter(["name", "cpu_percent"]):
            try:
                proc_name = proc.info["name"]
                if any(name.lower() in proc_name.lower() for name in process_names):
                    cpu = proc.cpu_percent(interval=0.1)
                    if cpu > max_cpu:
                        max_cpu = cpu

                    try:
                        connections = proc.net_connections(kind="inet")
                        udp_connections = [c for c in connections if c.type == 2]
                        if len(udp_connections) > 2:
                            has_udp = True
                    except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if has_udp and max_cpu > 3.0:
            return True, "discord", max_cpu
        elif max_cpu > self.discord_cpu_threshold:
            return True, "discord", max_cpu
        return False, None, 0

    def detect_zoom_call(self):
        """Detect active Zoom call"""
        process_names = ["zoom.exe", "zoom.us", "zoom", "zoom.us.app"]
        return self.is_process_active(process_names, cpu_threshold=self.cpu_threshold)

    def detect_teams_call(self):
        """Detect active Teams call"""
        process_names = ["teams.exe", "teams", "Teams"]
        return self.is_process_active(process_names, cpu_threshold=self.cpu_threshold)

    def mix_audio_simple(self, data1, data2):
        """Simple audio mixing - handles different buffer sizes"""
        # Ensure both are the same length
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]

        # Unpack as signed 16-bit integers
        samples1 = struct.unpack(f"{min_len // 2}h", data1)
        samples2 = struct.unpack(f"{min_len // 2}h", data2)

        # Mix by averaging
        mixed = [(s1 + s2) // 2 for s1, s2 in zip(samples1, samples2)]

        # Pack back to bytes
        return struct.pack(f"{len(mixed)}h", *mixed)

    def start_recording(self, platform_name=None):
        if self.is_recording:
            return

        if not self.speaker_device and not self.mic_device:
            print("❌ Cannot record: No audio devices available")
            return

        self.is_recording = True
        self.inactive_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = f"_{platform_name}" if platform_name else ""
        filename = os.path.join(self.output_dir, f"meeting{platform}_{timestamp}.wav")

        print(f"\n🎙️ Recording to: {filename}")
        if self.speaker_device:
            print(f"🔊 Speakers: {self.speaker_device['name']}")
        if self.mic_device:
            print(f"🎤 Microphone: {self.mic_device['name']}")
        sys.stdout.flush()

        def record():
            frames = []
            channels = 2
            sample_rate = 48000
            recording_active = True

            try:
                self.p = pyaudio.PyAudio()

                # Open speaker stream
                if self.speaker_device:
                    channels_spk = min(
                        self.speaker_device.get("maxInputChannels", 2), 2
                    )
                    rate_spk = int(
                        self.speaker_device.get("defaultSampleRate", self.rate)
                    )
                    self.stream_speaker = self.p.open(
                        format=self.format,
                        channels=channels_spk,
                        rate=rate_spk,
                        input=True,
                        frames_per_buffer=self.chunk,
                        input_device_index=self.speaker_device["index"],
                    )
                    sample_rate = rate_spk
                    channels = channels_spk
                    print(f"✅ Speaker: {channels_spk}ch @ {rate_spk}Hz")

                # Open microphone stream
                if self.mic_device:
                    channels_mic = min(self.mic_device.get("maxInputChannels", 2), 2)
                    rate_mic = int(self.mic_device.get("defaultSampleRate", self.rate))
                    self.stream_mic = self.p.open(
                        format=self.format,
                        channels=channels_mic,
                        rate=rate_mic,
                        input=True,
                        frames_per_buffer=self.chunk,
                        input_device_index=self.mic_device["index"],
                    )
                    if not self.speaker_device:
                        sample_rate = rate_mic
                        channels = channels_mic
                    print(f"✅ Mic: {channels_mic}ch @ {rate_mic}Hz")

                print("🎬 Recording...\n")
                sys.stdout.flush()

                # Recording loop
                while self.is_recording and recording_active:
                    try:
                        speaker_data = None
                        mic_data = None

                        # Read speaker audio
                        if self.stream_speaker:
                            try:
                                speaker_data = self.stream_speaker.read(
                                    self.chunk, exception_on_overflow=False
                                )
                            except:
                                pass

                        # Read mic audio
                        if self.stream_mic:
                            try:
                                mic_data = self.stream_mic.read(
                                    self.chunk, exception_on_overflow=False
                                )
                            except:
                                pass

                        # Combine audio
                        audio_chunk = None
                        if speaker_data and mic_data:
                            audio_chunk = self.mix_audio_simple(speaker_data, mic_data)
                        elif speaker_data:
                            audio_chunk = speaker_data
                        elif mic_data:
                            audio_chunk = mic_data
                        else:
                            recording_active = False
                            continue

                        # Save to frames for file backup
                        frames.append(audio_chunk)

                        # Stream to transcription
                        # Put in queue
                        try:
                            self.audio_stream_queue.put_nowait(
                                (audio_chunk, sample_rate, channels)
                            )
                        except queue.Full:
                            pass  # Drop frame if queue is full

                        # Call callback if registered
                        if self.audio_callback:
                            try:
                                self.audio_callback(audio_chunk, sample_rate, channels)
                            except Exception as e:
                                print(f"⚠️  Callback error: {e}")

                    except Exception as e:
                        if self.is_recording:
                            print(f"⚠️  Error: {e}")
                            sys.stdout.flush()
                        recording_active = False

                print(f"📊 Captured {len(frames)} chunks")
                sys.stdout.flush()

            except Exception as e:
                print(f"❌ Setup error: {e}")
                import traceback

                traceback.print_exc()
                sys.stdout.flush()

            finally:
                # Cleanup streams
                if self.stream_speaker:
                    try:
                        self.stream_speaker.stop_stream()
                        self.stream_speaker.close()
                        self.stream_speaker = None
                    except:
                        pass

                if self.stream_mic:
                    try:
                        self.stream_mic.stop_stream()
                        self.stream_mic.close()
                        self.stream_mic = None
                    except:
                        pass

                if self.p:
                    try:
                        self.p.terminate()
                        self.p = None
                    except:
                        pass

                # Save file
                if len(frames) > 0:
                    try:
                        print(f"💾 Saving...")
                        sys.stdout.flush()

                        temp_p = pyaudio.PyAudio()
                        wf = wave.open(filename, "wb")
                        wf.setnchannels(channels)
                        wf.setsampwidth(temp_p.get_sample_size(self.format))
                        wf.setframerate(sample_rate)
                        wf.writeframes(b"".join(frames))
                        wf.close()
                        temp_p.terminate()

                        file_size = os.path.getsize(filename) / (1024 * 1024)
                        duration = len(frames) * self.chunk / sample_rate
                        print(f"✅ Saved: {file_size:.2f} MB, {duration:.1f}s")
                        print(f"📁 {filename}\n")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"❌ Save error: {e}")
                        import traceback

                        traceback.print_exc()
                        sys.stdout.flush()
                else:
                    print(f"⚠️  No data recorded\n")
                    sys.stdout.flush()

        self.audio_thread = threading.Thread(target=record, daemon=False)
        self.audio_thread.start()

    def stop_recording(self):
        if not self.is_recording:
            return

        print("⏹️ Stopping...")
        sys.stdout.flush()

        # 1. Signal the recording thread to stop
        self.is_recording = False

        # 2. Wait for the recording thread to finish its OWN cleanup and saving
        #    (Its 'finally' block will handle closing streams)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=3)  # Wait for it to save the file
            if self.audio_thread.is_alive():
                print("⚠️ Recording thread still running (will finish in background)")
                sys.stdout.flush()

        # 3. Now that the thread is done, we can safely report completion
        print("✅ Stop complete")
        sys.stdout.flush()

        # Wait for thread to finish - DON'T let it block forever
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=3)
            if self.audio_thread.is_alive():
                print("⚠️ Recording thread still running (will finish in background)")
                sys.stdout.flush()

        print("✅ Stop complete")
        sys.stdout.flush()

    def monitor_loop(self):
        print("👀 Monitoring for calls...")
        print(f"⚙️  Inactivity timeout: {self.inactive_threshold}s")
        print(f"⚙️  Call confirmation: {self.call_detection_threshold} checks\n")
        sys.stdout.flush()

        check_count = 0
        while self.running:
            # 1. Check all potential platforms
            zoom_active, zoom_name, zoom_cpu = self.detect_zoom_call()
            discord_active, discord_name, discord_cpu = self.detect_discord_call()
            teams_active, teams_name, teams_cpu = self.detect_teams_call()

            # 2. Status printing (this is fine)
            check_count += 1
            if check_count % 30 == 0 and not self.in_call:
                status = []
                if discord_active:
                    status.append(f"Discord: ✅ {discord_cpu:.1f}%")
                else:
                    status.append(f"Discord: ❌")
                if zoom_active:
                    status.append(f"Zoom: ✅ {zoom_cpu:.1f}%")
                else:
                    status.append(f"Zoom: ❌")

                print(f"[{datetime.now().strftime('%H:%M:%S')}] {' | '.join(status)}")
                sys.stdout.flush()

            # 3. Determine current call state
            current_platform = None
            is_any_call_active = False

            if zoom_active:
                current_platform = "zoom"
                is_any_call_active = True
            elif discord_active:  # Use elif to prioritize one app at a time
                current_platform = "discord"
                is_any_call_active = True
            elif teams_active:
                current_platform = "teams"
                is_any_call_active = True

                sys.stdout.flush()

            if is_any_call_active:
                sys.stdout.flush()

            elif not is_any_call_active:
                sys.stdout.flush()

            # --- State Machine Logic ---

            if not self.in_call:
                # --- STATE: NOT IN CALL (NOT RECORDING) ---
                if is_any_call_active:
                    # A call is active, start confirmation counter
                    self.inactive_count = 0
                    self.call_detected_count += 1
                    print(
                        f"🔍 Call activity ({self.call_detected_count}/{self.call_detection_threshold})"
                    )
                    sys.stdout.flush()

                    if self.call_detected_count >= self.call_detection_threshold:
                        print(f"📞 {current_platform.upper()} call started!")
                        sys.stdout.flush()

                        self.start_recording(current_platform)
                        self.in_call = True
                        self.active_platform = (
                            current_platform  # ⭐️ Store which platform started
                        )
                        self.call_detected_count = 0
                else:
                    # No call active, reset detection counter
                    self.call_detected_count = 0

            else:
                # --- STATE: IN CALL (RECORDING) ---
                # We are recording, so self.active_platform is set (e.g., "zoom")

                # Check if the *specific* platform that started the recording is still active
                is_original_call_active = False
                if self.active_platform == "zoom" and zoom_active:
                    is_original_call_active = True
                elif self.active_platform == "discord" and discord_active:
                    is_original_call_active = True
                elif self.active_platform == "teams" and teams_active:
                    is_original_call_active = True

                if is_original_call_active:
                    # The call is still ongoing. Reset inactivity.
                    self.inactive_count = 0
                else:
                    # The call that triggered the recording seems to have ended.
                    # Start the inactivity countdown.
                    self.inactive_count += 1

                    # Only show countdown occasionally to reduce spam
                    if self.inactive_count % 3 == 0:
                        print(
                            f"⏳ Inactive {self.inactive_count}/{self.inactive_threshold}s"
                        )
                        sys.stdout.flush()

                    if self.inactive_count >= self.inactive_threshold:
                        # Inactivity threshold met! Stop the recording.
                        print(
                            f"\n📴 {self.active_platform.upper()} call ended (inactive {self.inactive_threshold}s)"
                        )
                        sys.stdout.flush()
                        self.stop_recording()
                        self.in_call = False
                        self.active_platform = None  # ⭐️ Clear the active platform
                        self.inactive_count = 0
                        print("👀 Back to monitoring...\n")
                        sys.stdout.flush()

            time.sleep(1)

    def start(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✨ FocusNote Started!\n")
        sys.stdout.flush()

    def stop(self):
        print("\n🛑 Shutting down...")
        self.running = False
        self.stop_recording()
        time.sleep(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FocusNote - Call recording")
    parser.add_argument("--test", action="store_true", help="Test 10s recording")
    parser.add_argument("--manual", action="store_true", help="Manual mode")
    args = parser.parse_args()

    backend = AudioCapture()

    if args.test:
        print("\n🧪 Test recording for 10 seconds...")
        print("💬 Talk into your microphone!\n")
        backend.start_recording("test")
        time.sleep(10)
        backend.stop_recording()
        print("✅ Done! Check meeting_recordings folder\n")
        return

    if args.manual:
        print("\n🎮 MANUAL MODE")
        print("Press Enter to start/stop\n")
        try:
            while True:
                input("Press Enter to START: ")
                backend.start_recording("manual")
                input("Press Enter to STOP: ")
                backend.stop_recording()
        except KeyboardInterrupt:
            backend.stop_recording()
            print("\n👋 Goodbye!")
        return

    # Auto mode - stays running indefinitely
    try:
        backend.start()
        print("Press Ctrl+C to exit")
        print("=" * 50 + "\n")
        # Keep running forever
        while backend.running:
            time.sleep(1)
    except KeyboardInterrupt:
        backend.stop()
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
