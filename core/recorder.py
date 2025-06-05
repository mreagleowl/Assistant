# core/recorder.py

import sounddevice as sd
import soundfile as sf
import threading
import queue
import datetime
import os
from logger import logger

class AudioRecorder:
    def __init__(self, save_dir="recordings", samplerate=16000,
                 channels=1, device=None):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.samplerate = samplerate
        self.channels = channels
        self.device = device
        self.q = queue.Queue()
        self.recording = False
        self.filepath = None
        self.thread = None

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Record status: {status}")
        self.q.put(indata.copy())

    def start_recording(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(self.save_dir, f"meeting_{ts}.wav")
        self.recording = True
        self.thread = threading.Thread(target=self._record)
        self.thread.start()
        logger.info(f"Recording started: {self.filepath}")

    def _record(self):
        with sf.SoundFile(self.filepath, mode='x', samplerate=self.samplerate,
                          channels=self.channels, subtype='PCM_16') as file:
            with sd.InputStream(samplerate=self.samplerate,
                                channels=self.channels,
                                callback=self._callback,
                                device=self.device):
                while self.recording:
                    file.write(self.q.get())

    def stop_recording(self):
        self.recording = False
        self.thread.join()
        logger.info(f"Recording saved to {self.filepath}")
        return self.filepath
