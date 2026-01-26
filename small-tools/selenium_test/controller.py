import time
import threading
import sys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from model import load_config, save_config, validate_and_launch_driver, DEFAULT_CONFIG
from view import (
    prompt_for_url,
    prompt_for_chrome_path,
    show_message,
    show_error,
    alert_beep,
    quit_input_handler,
)


ALARM_TOGGLE_SELECTOR = "monitorToggle"
ALARM_TOGGLE_BY = By.ID
CHECK_INTERVAL = 1


def get_valid_config_and_driver(current_config: dict, stop_event: threading.Event):
    driver = None
    new_config = current_config.copy()

    # 尝试使用当前配置启动 Driver
    if new_config.get("chrome_path"):
        show_message("--- 浏览器路径配置 ---")
        driver, error_message = validate_and_launch_driver(new_config["chrome_path"])
        if driver:
            show_message("✅ Chrome 驱动程序启动成功。")
            return driver, new_config
        else:
            show_error(error_message)

    show_message("--- 首次配置或路径错误，请手动输入 ---")

    while not stop_event.is_set() and driver is None:
        # 获取 URL
        if not new_config.get("target_url") or new_config["target_url"] == DEFAULT_CONFIG["target_url"]:
            new_config["target_url"] = prompt_for_url(new_config.get("target_url", ""))
        else:
            show_message(f"已使用配置中的 URL: {new_config['target_url']}")

        # 获取 Chrome Path
        while not stop_event.is_set() and driver is None:
            input_path = prompt_for_chrome_path(new_config.get("chrome_path"))
            if input_path:
                # normalize backslashes
                new_config["chrome_path"] = input_path.replace('\\', '\\\\')
            else:
                new_config["chrome_path"] = ""

            driver, error_message = validate_and_launch_driver(new_config["chrome_path"])

            if driver:
                show_message("✅ Chrome 驱动程序启动成功。")
                save_config(new_config)
                return driver, new_config
            else:
                show_error(error_message)
                new_config["chrome_path"] = ""
                time.sleep(1)

    return None, new_config


def start_audio_monitoring():
    stop_event = threading.Event()
    show_message("正在启动音频监控程序...")

    driver = None
    input_thread = None

    try:
        initial_config = load_config()
        driver, config = get_valid_config_and_driver(initial_config, stop_event)

        if driver is None:
            show_error("无法启动 Chrome 浏览器。程序退出。")
            sys.exit(1)

        target_url = config["target_url"]

        input_thread = threading.Thread(target=quit_input_handler, args=(stop_event,), daemon=True)
        input_thread.start()

        show_message(f"正在打开网页: {target_url}")
        driver.get(target_url)
        time.sleep(5)

        # 激活提醒开关
        show_message("尝试激活提醒功能...")
        try:
            alarm_checkbox = driver.find_element(ALARM_TOGGLE_BY, ALARM_TOGGLE_SELECTOR)
            if not alarm_checkbox.is_selected():
                alarm_checkbox.click()
                show_message("✅ 已成功勾选提醒框，功能已激活。")
            else:
                show_message("提醒框已是激活状态，跳过点击。")
        except NoSuchElementException:
            show_error(f"找不到提醒开关元素。ID: '{ALARM_TOGGLE_SELECTOR}'")
            stop_event.set()
            raise

        activate_script = """
        var audios = document.getElementsByTagName('audio');
        for(var i = 0; i < audios.length; i++){
            audios[i].muted = true; 
            audios[i].play().catch(e => console.log('Audio activation failed:', e));
            audios[i].pause();
            audios[i].muted = false; 
        }
        """
        driver.execute_script(activate_script)
        time.sleep(2)

        show_message(f"\n开始高频率监听音频状态 (间隔 {CHECK_INTERVAL} 秒)...")

        while not stop_event.is_set():
            check_script = """
            var audios = document.getElementsByTagName('audio');
            for(var i = 0; i < audios.length; i++){
                if(!audios[i].paused && audios[i].currentTime > 0){
                    return true;
                }
            }
            return false;
            """

            is_playing = driver.execute_script(check_script)

            if is_playing:
                show_message(f"\n【!!! 警报 !!!】检测到网页正在播放提示音！")
                alert_beep()
                time.sleep(3)

            for _ in range(int(CHECK_INTERVAL * 10)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)

        driver.quit()

    except KeyboardInterrupt:
        show_message("\n\n收到 Ctrl+C 信号，正在停止监控...")
        stop_event.set()
    except Exception as e:
        show_error(f"发生运行时错误: {e}")
        stop_event.set()
    finally:
        if driver is not None:
            show_message("正在关闭 Chrome 浏览器...")
            try:
                driver.quit()
            except Exception:
                pass
        stop_event.set()
        show_message("程序已安全退出。")
