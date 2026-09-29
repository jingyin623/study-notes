import requests
import threading
import json
import sounddevice as sd
import numpy as np
import torch
import time
from silero_vad import load_silero_vad, get_speech_timestamps

# ===== LLM 配置 =====
OLLAMA_URL = "http://192.168.100.20:11434/api/chat"
MODEL = "qwen2.5:7b"

# ===== VAD 配置 =====
SAMPLE_RATE = 16000
BLOCK_SIZE = 256
VAD_THRESHOLD = 0.6
COOLDOWN = 0.6

model_vad = load_silero_vad()
audio_buffer = []
last_vad_trigger = 0

# ===== 对话状态 =====
messages = []
current_response = None
current_answer = ""
interrupted = False
llm_speaking = False


# ===== LLM streaming =====
def stream_chat():
    global current_response, current_answer, interrupted, llm_speaking
    current_answer = ""
    interrupted = False
    llm_speaking = True

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True
    }

    try:
        current_response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=None
        )

        for line in current_response.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            if "message" in data:
                token = data["message"]["content"]
                current_answer += token
                print(token, end="", flush=True)

    except Exception:
        interrupted = True
        print("\n[LLM 连接中断]")

    llm_speaking = False


def interrupt():
    global current_response, interrupted
    if current_response:
        interrupted = True
        try:
            current_response.close()
        except Exception:
            pass


# ===== VAD =====
def audio_callback(indata, frames, time_info, status):
    audio_buffer.extend(indata[:, 0].tolist())


def vad_loop():
    global last_vad_trigger

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    ):
        while True:
            time.sleep(0.05)

            if not llm_speaking:
                continue

            if len(audio_buffer) < SAMPLE_RATE * 0.25:
                continue

            chunk = np.array(audio_buffer[: int(SAMPLE_RATE * 0.25)])
            del audio_buffer[: int(SAMPLE_RATE * 0.15)]

            wav = torch.from_numpy(chunk).float()

            timestamps = get_speech_timestamps(
                wav,
                model_vad,
                sampling_rate=SAMPLE_RATE,
                threshold=VAD_THRESHOLD,
                min_speech_duration_ms=80,
                min_silence_duration_ms=200
            )

            now = time.time()
            if timestamps and (now - last_vad_trigger) > COOLDOWN:
                print("\n🛑 你开始说话 → 打断模型\n")
                last_vad_trigger = now
                interrupt()


# ===== 主循环 =====
def main():
    threading.Thread(target=vad_loop, daemon=True).start()

    while True:
        user_input = input("\n\n你：")
        messages.append({"role": "user", "content": user_input})

        print("模型：", end="", flush=True)

        t = threading.Thread(target=stream_chat)
        t.start()

        t.join()

        if not interrupted and current_answer.strip():
            messages.append({"role": "assistant", "content": current_answer})
            print("\n--- 回答已保存 ---\n")
        else:
            messages.pop()
            print("\n--- 回答被打断，未写入上下文 ---\n")


if __name__ == "__main__":
    main()
