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
import argparse


# Import appropriate audio library based on OS
SYSTEM = platform.system()

if SYSTEM == "Windows":
    try:
        import pyaudiowpatch as pyaudio
        AUDIO_BACKEND = "pyaudiowpatch"
    except ImportError:
        print("PyAudioWPatch not found. Install with: pip install pyaudiowpatch")
        import pyaudio
        AUDIO_BACKEND = "pyaudio"
elif SYSTEM == "Darwin":  # macOS
    try:
        import pyaudio
        AUDIO_BACKEND = "pyaudio"
    except ImportError:
        print("PyAudio not found. Install with: pip install pyaudio")
        sys.exit(1)
else:  # Linux
    try:
        import pyaudio
        AUDIO_BACKEND = "pyaudio"
    except ImportError:
        print("PyAudio not found. Install with: pip install pyaudio")
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
        self.rate = 48000  # Use standard 48kHz to match device native rates

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
        self.inactive_threshold = 3

        # Audio streaming queue for transcription
        self.audio_stream_queue = queue.Queue(maxsize=100)

        # Callback for real-time audio processing
        self.audio_callback = None
        
        # Callback for when recording stops
        self.recording_stop_callback = None
        
        # macOS ffmpeg process
        self.ffmpeg_process = None
        self.ffmpeg_thread = None
        self.ffmpeg_queue = queue.Queue(maxsize=50)
        
        # Audio device setup
        self.speaker_device = None
        self.mic_device = None
        self.setup_audio_devices()

        print(f"Platform: {SYSTEM}")
        print(f"Audio backend: {AUDIO_BACKEND}\n")

    def start_ffmpeg_capture(self):
        """Start ffmpeg system audio capture for macOS"""
        if SYSTEM != "Darwin":
            return False
        
        try:
            # Start capturing system audio
            cmd = [
                'ffmpeg',
                '-f', 'avfoundation',
                '-i', ':0',  # Audio device (index 0 is usually the default)
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', str(self.rate),
                '-ac', '2',
                'pipe:1'
            ]
            
            #read the system audio from ffmpeg
            print(f"DEBUG: Starting ffmpeg with sample rate: {self.rate} Hz")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=10**8
            )
            
            print(f"ffmpeg system audio capture started at {self.rate} Hz, 2 channels")
            
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
                            print(f"ffmpeg read error: {e}")
                        break
            
            self.ffmpeg_thread = threading.Thread(target=read_ffmpeg, daemon=True)
            self.ffmpeg_thread.start()
            return True
            
        except FileNotFoundError:
            print("ffmpeg not found. Install with: brew install ffmpeg")
            print("Falling back to microphone only")
            return False
        except Exception as e:
            print(f"Could not start ffmpeg: {e}")
            return False

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
    
    def set_recording_stop_callback(self, callback):
        """
        Set a callback function that will be called when recording stops
        callback should accept no arguments
        """
        self.recording_stop_callback = callback

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
                                print(f"Speaker loopback: {loopback['name']}")
                                break
                    else:
                        self.speaker_device = default_speakers
                        print(f"Speaker loopback: {default_speakers['name']}")
                except Exception as e:
                    print(f"Could not setup speaker loopback: {e}")

                # Get microphone (for your voice)
                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"Could not setup microphone: {e}")

            elif SYSTEM == "Darwin":  # macOS
                # On macOS, we'll use ffmpeg for system audio instead of PyAudio
                print("macOS detected - will use ffmpeg for system audio capture")
                
                # Still set up microphone for user's voice
                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"Could not setup microphone: {e}")

            else:  # Linux
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    if "monitor" in dev["name"].lower() and dev["maxInputChannels"] > 0:
                        self.speaker_device = dev
                        print(f"Linux monitor device: {dev['name']}")
                        break

                try:
                    default_mic = p.get_default_input_device_info()
                    self.mic_device = default_mic
                    print(f"Microphone: {default_mic['name']}")
                except Exception as e:
                    print(f"Could not setup microphone: {e}")

            p.terminate()

            if SYSTEM == "Darwin":
                # On macOS, we don't need speaker_device for PyAudio
                if not self.mic_device:
                    print(" Warning: No microphone found")
            elif not self.speaker_device and not self.mic_device:
                print("Warning: Could not find any audio devices")
            elif not self.speaker_device:
                print("Warning: No speaker loopback (recording mic only)")
            elif not self.mic_device:
                print("Warning: No microphone (recording speakers only)")

        except Exception as e:
            print(f"Warning: Could not initialize audio: {e}")

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

    def mono_to_stereo(self, mono_data):
        """Convert mono audio to stereo by duplicating the channel"""
        samples = struct.unpack(f"{len(mono_data) // 2}h", mono_data)
        # Duplicate each sample for left and right channels
        stereo = []
        for sample in samples:
            stereo.append(sample)  # Left channel
            stereo.append(sample)  # Right channel
        return struct.pack(f"{len(stereo)}h", *stereo)

    def mix_audio_simple(self, data1, data2):
        """Simple audio mixing - handles different buffer sizes"""
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]

        samples1 = struct.unpack(f"{min_len // 2}h", data1)
        samples2 = struct.unpack(f"{min_len // 2}h", data2)

        mixed = [(s1 + s2) // 2 for s1, s2 in zip(samples1, samples2)]

        return struct.pack(f"{len(mixed)}h", *mixed)

    def start_recording(self, platform_name=None):
        if self.is_recording:
            return

        if SYSTEM != "Darwin" and not self.speaker_device and not self.mic_device:
            print("Cannot record: No audio devices available")
            return

        self.is_recording = True
        self.inactive_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = f"_{platform_name}" if platform_name else ""
        filename = os.path.join(self.output_dir, f"meeting{platform}_{timestamp}.wav")

        print(f"\nRecording to: {filename}")
        if self.mic_device:
            print(f"Microphone: {self.mic_device['name']}")
        sys.stdout.flush()

        def record():
            frames = []
            channels = 2
            sample_rate = self.rate
            recording_active = True
            ffmpeg_started = False

            try:
                self.p = pyaudio.PyAudio()

                # macOS: Start ffmpeg for system audio
                if SYSTEM == "Darwin":
                    ffmpeg_started = self.start_ffmpeg_capture()
                    if ffmpeg_started:
                        print("System audio: ffmpeg capture")

                # Windows/Linux: Open speaker stream
                if SYSTEM != "Darwin" and self.speaker_device:
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
                    print(f"Speaker: {channels_spk}ch @ {rate_spk}Hz")

                # Open microphone stream (all platforms)
                if self.mic_device:
                    # Use mic's native channel count (usually 1 for built-in mics)
                    channels_mic = min(self.mic_device.get("maxInputChannels", 2), 2)
                    # Force the mic to use the same rate as ffmpeg/self.rate
                    rate_mic = self.rate  # Force to match ffmpeg capture rate
                    print(f"DEBUG: Mic native rate: {self.mic_device.get('defaultSampleRate')}, forcing to: {rate_mic}")
                    print(f"DEBUG: Mic native channels: {self.mic_device.get('maxInputChannels')}, using: {channels_mic}")
                    self.stream_mic = self.p.open(
                        format=self.format,
                        channels=channels_mic,
                        rate=rate_mic,
                        input=True,
                        frames_per_buffer=self.chunk,
                        input_device_index=self.mic_device["index"],
                    )
                    # If mic-only and not macOS, use mic's native channels
                    # On macOS with ffmpeg, we keep channels=2 (default set earlier)
                    if not self.speaker_device and SYSTEM != "Darwin":
                        sample_rate = rate_mic
                        channels = channels_mic
                    print(f"Mic: {channels_mic}ch @ {rate_mic}Hz (will be converted to stereo if needed)")

                print("Recording...\n")
                sys.stdout.flush()

                # Recording loop
                while self.is_recording and recording_active:
                    try:
                        speaker_data = None
                        mic_data = None

                        # Read speaker audio (Windows/Linux: PyAudio, macOS: ffmpeg)
                        if SYSTEM == "Darwin" and ffmpeg_started:
                            try:
                                speaker_data = self.ffmpeg_queue.get(timeout=0.1)
                            except queue.Empty:
                                pass
                        elif self.stream_speaker:
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
                                # Convert mono mic to stereo if needed (for macOS)
                                if channels_mic == 1 and mic_data:
                                    mic_data = self.mono_to_stereo(mic_data)
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
                            continue

                        # Save to frames
                        frames.append(audio_chunk)

                        # Stream to transcription
                        try:
                            self.audio_stream_queue.put_nowait(
                                (audio_chunk, sample_rate, channels)
                            )
                        except queue.Full:
                            pass

                        # Call callback
                        if self.audio_callback:
                            try:
                                self.audio_callback(audio_chunk, sample_rate, channels)
                            except Exception as e:
                                print(f"Callback error: {e}")

                    except Exception as e:
                        if self.is_recording:
                            print(f"Error: {e}")
                            sys.stdout.flush()
                        recording_active = False

                print(f"📊 Captured {len(frames)} chunks")
                sys.stdout.flush()

            except Exception as e:
                print(f"Setup error: {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()

            finally:
                # Stop ffmpeg (macOS)
                if SYSTEM == "Darwin":
                    self.stop_ffmpeg_capture()

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
                        print(f"Saving...")
                        print(f"DEBUG: WAV file params - Rate: {sample_rate} Hz, Channels: {channels}")
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
                        print(f"Saved: {file_size:.2f} MB, {duration:.1f}s")
                        print(f"{filename}\n")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"Save error: {e}")
                        import traceback
                        traceback.print_exc()
                        sys.stdout.flush()
                else:
                    print(f"No data recorded\n")
                    sys.stdout.flush()

        self.audio_thread = threading.Thread(target=record, daemon=False)
        self.audio_thread.start()

    def stop_recording(self):
        if not self.is_recording:
            return

        print("Stopping...")
        sys.stdout.flush()

        self.is_recording = False

        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=3)
            if self.audio_thread.is_alive():
                print("Recording thread still running (will finish in background)")
                sys.stdout.flush()

        print("Stop complete")
        sys.stdout.flush()
        
        # Call the recording stop callback if registered
        if self.recording_stop_callback:
            try:
                self.recording_stop_callback()
            except Exception as e:
                print(f"Recording stop callback error: {e}")

    def monitor_loop(self):
        print("Monitoring for calls...")
        print(f"Inactivity timeout: {self.inactive_threshold}s")
        print(f"Call confirmation: {self.call_detection_threshold} checks\n")
        sys.stdout.flush()

        check_count = 0
        while self.running:
            zoom_active, zoom_name, zoom_cpu = self.detect_zoom_call()
            discord_active, discord_name, discord_cpu = self.detect_discord_call()
            teams_active, teams_name, teams_cpu = self.detect_teams_call()

            check_count += 1
            if check_count % 30 == 0 and not self.in_call:
                status = []
                if discord_active:
                    status.append(f"Discord: cpu {discord_cpu:.1f}%")
                else:
                    status.append(f"Discord: not active")
                if zoom_active:
                    status.append(f"Zoom: cpu {zoom_cpu:.1f}%")
                else:
                    status.append(f"Zoom: not active")

                print(f"[{datetime.now().strftime('%H:%M:%S')}] {' | '.join(status)}")
                sys.stdout.flush()

            current_platform = None
            is_any_call_active = False

            if zoom_active:
                current_platform = "zoom"
                is_any_call_active = True
            elif discord_active:
                current_platform = "discord"
                is_any_call_active = True
            elif teams_active:
                current_platform = "teams"
                is_any_call_active = True

            if not self.in_call:
                if is_any_call_active:
                    self.inactive_count = 0
                    self.call_detected_count += 1
                    print(
                        f"🔍 Call activity ({self.call_detected_count}/{self.call_detection_threshold})"
                    )
                    sys.stdout.flush()

                    if self.call_detected_count >= self.call_detection_threshold:
                        print(f"{current_platform.upper()} call started!")
                        sys.stdout.flush()

                        self.start_recording(current_platform)
                        self.in_call = True
                        self.active_platform = current_platform
                        self.call_detected_count = 0
                else:
                    self.call_detected_count = 0

            else:
                is_original_call_active = False
                if self.active_platform == "zoom" and zoom_active:
                    is_original_call_active = True
                elif self.active_platform == "discord" and discord_active:
                    is_original_call_active = True
                elif self.active_platform == "teams" and teams_active:
                    is_original_call_active = True

                if is_original_call_active:
                    self.inactive_count = 0
                else:
                    self.inactive_count += 1

                    if self.inactive_count % 3 == 0:
                        print(
                            f"Inactive {self.inactive_count}/{self.inactive_threshold}s"
                        )
                        sys.stdout.flush()

                    if self.inactive_count >= self.inactive_threshold:
                        print(
                            f"\n{self.active_platform.upper()} call ended (inactive {self.inactive_threshold}s)"
                        )
                        sys.stdout.flush()
                        self.stop_recording()
                        self.in_call = False
                        self.active_platform = None
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
        print("\nShutting down...")
        self.running = False
        self.stop_recording()
        time.sleep(1)


def main():

    parser = argparse.ArgumentParser(description="FocusNote - Call recording")
    parser.add_argument("--test", action="store_true", help="Test 10s recording")
    parser.add_argument("--manual", action="store_true", help="Manual mode")

    backend = AudioCapture()

    try:
        backend.start()
        print("Press Ctrl+C to exit")
        print("=" * 50 + "\n")
        while backend.running:
            time.sleep(1)
    except KeyboardInterrupt:
        backend.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    main()