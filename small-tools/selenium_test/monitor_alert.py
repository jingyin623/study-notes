"""入口文件：启动 MVC 风格的监控程序。"""
from controller import start_audio_monitoring


if __name__ == "__main__":
    try:
        start_audio_monitoring()
    except Exception as e:
        print(f"程序启动失败: {e}")
        raise