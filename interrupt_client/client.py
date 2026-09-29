import requests
import threading
import json
import sounddevice as sd
import numpy as np
import torch
import time
# 从本地模块导入 VAD 和 ASR 相关的工具函数
from silero_vad import load_silero_vad, get_speech_timestamps
from asr_whisper import record_and_transcribe

# ===== LLM (大语言模型) 配置 =====
OLLAMA_URL = "http://192.168.100.20:11434/api/chat" # Ollama API 地址
MODEL = "qwen2.5:7b"                             # 使用的模型名称

# ===== VAD (语音活动检测) 配置 =====
SAMPLE_RATE = 16000     # 采样率，Silero VAD 强制要求 16k
BLOCK_SIZE = 256        # 每次处理的音频块大小
VAD_THRESHOLD = 0.6     # VAD 灵敏度阈值 (0-1)，越高越不容易误触发
COOLDOWN = 0.6          # 打断冷却时间，防止频繁触发

model_vad = load_silero_vad() # 加载 Silero VAD 模型
audio_buffer = []             # 音频缓冲区，用于存放实时采集的语音数据
last_vad_trigger = 0          # 上次 VAD 触发的时间戳

# ===== 对话系统状态标志位 =====
messages = []            # 存储对话历史上下文
current_response = None  # 当前正在进行的 requests 请求对象
current_answer = ""      # 当前模型回复的内容文本
interrupted = False      # 是否被打断的标志
llm_speaking = False     # 模型是否正在生成回答
can_trigger_llm = True   # 是否允许触发新的 LLM 请求
asr_enabled = True       # ASR 是否处于启用状态


# ===== LLM streaming (流式聊天函数) =====
def stream_chat():
    """向 Ollama 发送请求并实时处理返回的 Token"""
    global current_response, current_answer, interrupted, llm_speaking
    current_answer = ""
    interrupted = False
    llm_speaking = True # 标记模型开始说话

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True # 开启流式传输
    }

    try:
        # 发送 POST 请求到 Ollama
        current_response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=None # 回复可能很长，不设置超时
        )

        # 迭代处理每一行返回的流式 JSON 数据
        for line in current_response.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            if "message" in data:
                token = data["message"]["content"]
                current_answer += token
                print(token, end="", flush=True) # 实时打印模型出的字

    except Exception:
        # 当连接被 .close() 强行关闭时，会进入这里
        interrupted = True
        print("\n[LLM 连接中断]")

    llm_speaking = False # 标记模型结束说话


def interrupt():
    """打断函数：强行关闭当前的网络连接"""
    global current_response, interrupted, can_trigger_llm
    if current_response:
        interrupted = True
        can_trigger_llm = False   # ❗重要：打断后锁住，直到下次用户说话
        try:
            current_response.close() # 核心：关闭 socket 连接，停止流式输出
        except Exception:
            pass

# ===== VAD 实时监听逻辑 =====
def audio_callback(indata, frames, time_info, status):
    """音频输入流的回调函数，将麦克风数据不断存入缓冲区"""
    audio_buffer.extend(indata[:, 0].tolist())


def vad_loop():
    """VAD 检测死循环，后台运行"""
    global last_vad_trigger

    # 开启持续录音流
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    ):
        while True:
            time.sleep(0.05) # 降低 CPU 占用

            # 只有当 LLM 正在说话时，才有必要检测“打断”
            if not llm_speaking:
                continue

            # 缓冲区数据足够（0.25秒）才进行检测
            if len(audio_buffer) < SAMPLE_RATE * 0.25:
                continue

            # 取出一段音频并转为 Tensor 格式
            chunk = np.array(audio_buffer[: int(SAMPLE_RATE * 0.25)])
            del audio_buffer[: int(SAMPLE_RATE * 0.15)] # 消费掉部分缓冲区

            wav = torch.from_numpy(chunk).float()

            # 调用 Silero VAD 模型检测是否有说话声
            timestamps = get_speech_timestamps(
                wav,
                model_vad,
                sampling_rate=SAMPLE_RATE,
                threshold=VAD_THRESHOLD,
                min_speech_duration_ms=80,
                min_silence_duration_ms=200
            )

            now = time.time()
            # 如果检测到人声且过了冷却期，执行打断
            if timestamps and (now - last_vad_trigger) > COOLDOWN:
                print("\n🛑 你开始说话 → 打断模型\n")
                last_vad_trigger = now
                interrupt()


# ===== 主程序入口 =====
def main():
    global asr_enabled, can_trigger_llm
    # 启动后台 VAD 监听线程
    threading.Thread(target=vad_loop, daemon=True).start()

    while True:
        print("\n🎤 请说话...")
        # ⚠️ 注意：此处需确保 asr_whisper.py 里的函数支持 duration 参数
        user_input = record_and_transcribe(duration=3.0) 
        
        print(f"你：{user_input}")
        
        # 过滤无效输入
        if not user_input or len(user_input.strip()) < 2:
            print("（无有效语音输入，忽略）")
            continue
        
        # 用户说话了，解锁 LLM 触发权限
        can_trigger_llm = True
        messages.append({"role": "user", "content": user_input})

        print("模型：", end="", flush=True)

        if not can_trigger_llm:
            print("（等待新的有效语音输入）")
            continue
            
        # 开启 LLM 回答线程
        t = threading.Thread(target=stream_chat)
        t.start()

        # 等待 LLM 线程结束（要么说完了，要么被打断了）
        t.join()

        # 处理对话历史
        if not interrupted and current_answer.strip():
            # 正常说完，保存回复到上下文中
            messages.append({"role": "assistant", "content": current_answer})
            print("\n--- 回答已保存 ---\n")
        else:
            # 如果被打断，丢弃最后一条用户输入（或根据需求调整逻辑）
            if messages and messages[-1]["role"] == "user":
                messages.pop() 
            print("\n--- 回答被打断，未写入上下文 ---\n")


if __name__ == "__main__":
    main()