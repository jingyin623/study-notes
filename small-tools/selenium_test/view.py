import threading
import time
import winsound


def show_message(msg: str):
    print(msg)


def show_error(msg: str):
    print(f"!!! 错误: {msg}")


def prompt_for_url(current_url: str):
    if current_url:
        print(f"已使用配置中的 URL: {current_url}")
        return current_url

    while True:
        prompt_url = input("请输入监控目标网页 URL (示例 https://...): ")
        prompt_url = prompt_url.strip()
        if prompt_url.startswith("http"):
            return prompt_url
        print("!!! URL 格式不正确，必须以 http 或 https 开头。请重新输入。")


def prompt_for_chrome_path(current_path: str):
    prompt_path = current_path or "无"
    input_path = input(f"请输入 Chrome.exe 路径 (当前: {prompt_path}, 示例: C:\\...\\chrome.exe): ")
    return input_path.strip()


def alert_beep():
    try:
        winsound.Beep(1500, 3000)
    except Exception:
        # 在非 Windows 平台或失败时静默处理
        pass


def quit_input_handler(stop_event: threading.Event):
    """在单独的线程中监听用户输入 '1' 命令以触发 stop_event。"""
    print("\n\n【控制提示】: 在任何时候输入 '1' 并回车，可立即安全退出程序。")
    while not stop_event.is_set():
        try:
            user_input = input("")
            if user_input.strip().lower() == "1":
                print("\n收到退出指令 '1'，正在准备停止监控和关闭浏览器...")
                stop_event.set()
                break
        except EOFError:
            print("\n检测到 EOF，正在停止监控...")
            stop_event.set()
            break
        except Exception:
            # 忽略其他可能的输入/输出异常
            pass
