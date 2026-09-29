import sounddevice as sd
import numpy as np
import torch
import time
import requests
from silero_vad import load_silero_vad, get_speech_timestamps

LLM_INTERRUPT_URL = "http://127.0.0.1:8001/interrupt"

SAMPLE_RATE = 16000
BLOCK_SIZE = 256

model = load_silero_vad()
audio_buffer = []
last_trigger = 0
COOLDOWN = 0.6


def audio_callback(indata, frames, time_info, status):
    audio_buffer.extend(indata[:, 0].tolist())


def listen():
    global last_trigger
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    ):
        while True:
            time.sleep(0.05)

            if len(audio_buffer) < SAMPLE_RATE * 0.25:
                continue

            chunk = np.array(audio_buffer[: int(SAMPLE_RATE * 0.25)])
            del audio_buffer[: int(SAMPLE_RATE * 0.15)]

            wav = torch.from_numpy(chunk).float()
            ts = get_speech_timestamps(
                wav,
                model,
                sampling_rate=SAMPLE_RATE,
                threshold=0.6,
                min_silence_duration_ms=200
            )

            now = time.time()
            if ts and now - last_trigger > COOLDOWN:
                print("🛑 VAD: 检测到说话 → 中断 LLM")
                requests.post(LLM_INTERRUPT_URL)
                last_trigger = now
