from PyQt6.QtCore import QThread
from detection.detect_test import AudioCapture


class AudioCaptureThread(QThread):
    def __init__(self, audio_capture: AudioCapture):
        super().__init__()
        self.audio_capture = audio_capture

    def run(self):
        self.audio_capture.running = True
        self.audio_capture.monitor_loop()

    def stop(self):
        self.audio_capture.stop()
        self.quit()
        self.wait()
