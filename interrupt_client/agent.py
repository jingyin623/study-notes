import asyncio
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent
from livekit.plugins import openai, silero

async def entrypoint(ctx: JobContext):
    print("--- Job 正在启动 ---")
    
    llm = openai.LLM.with_ollama(
        model="qwen2.5:7b",
        base_url="http://192.168.100.20:11434/v1"
    )

    # 暂时禁用 STT 和 TTS，只测试核心 VAD 和 LLM 逻辑
    # 看看是否还会出现 DuplexClosed 错误
    agent = Agent(
        instructions="你是一个本地助手。",
        vad=silero.VAD.load(),
        stt=openai.STT(api_key="sk-abc123456789012345678901234567890"), # 换一个符合长度的假 Key
        llm=llm,
        tts=openai.TTS(api_key="sk-abc123456789012345678901234567890"),
    )

    await ctx.connect()
    print(f"成功连接到房间: {ctx.room.name}")
    
    agent.start(ctx.room)
    await agent.say("连接成功。", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url="ws://127.0.0.1:7880",
            api_key="devkey",
            api_secret="secret",
        )
    )