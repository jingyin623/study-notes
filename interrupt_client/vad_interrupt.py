import sounddevice as sd
import numpy as np
import torch
import time
from silero_vad import load_silero_vad, get_speech_timestamps

SAMPLE_RATE = 16000
BLOCK_SIZE = 256   # 更小 = 更快响应

model = load_silero_vad()
audio_buffer = []

last_trigger_time = 0
COOLDOWN = 0.6  # 触发后冷却时间（秒）

def audio_callback(indata, frames, time_info, status):
    global audio_buffer
    audio_buffer.extend(indata[:, 0].tolist())

def main():
    global audio_buffer, last_trigger_time
    print("🎙 正在监听麦克风（优化版），说话试试…")

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
            audio_buffer = audio_buffer[int(SAMPLE_RATE * 0.15):]

            wav = torch.from_numpy(chunk).float()

            timestamps = get_speech_timestamps(
                wav,
                model,
                sampling_rate=SAMPLE_RATE,
                threshold=0.4,          # 🔧 提高阈值，过滤噪声
                min_speech_duration_ms=80,
                min_silence_duration_ms=200  # 🔧 更快判定“停话”
            )

            now = time.time()
            if timestamps and (now - last_trigger_time) > COOLDOWN:
                print("🛑 检测到你在说话")
                last_trigger_time = now

if __name__ == "__main__":
    main()
