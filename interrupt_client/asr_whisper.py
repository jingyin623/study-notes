import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from client import asr_enabled

SAMPLE_RATE = 16000

# ⚠️ 程序启动时加载一次模型
model = WhisperModel(
    "tiny",
    device="cpu",          # 稳定后你可以改成 cuda
    compute_type="int8"
)

def record_and_transcribe(duration=3.0) -> str:
    if not asr_enabled:
        return " "

    """
    录一段音，返回识别文本
    """
    recording = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    audio = recording.flatten()

    segments, _ = model.transcribe(
        audio,
        beam_size=1,
        language="zh"
    )

    text = "".join(seg.text for seg in segments).strip()
    return text
