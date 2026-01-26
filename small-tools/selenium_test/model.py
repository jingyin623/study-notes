import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager

# --- 配置区域 ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "target_url": "https://alpha123.uk/zh/stability/",
    "chrome_path": "",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"⭐ {CONFIG_FILE} 文件不存在，将使用默认配置。")
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            config = json.load(f)
            print(f"✅ 从 {CONFIG_FILE} 加载配置成功。")
            merged = {**DEFAULT_CONFIG, **config}
            return merged
        except json.JSONDecodeError:
            print(f"!!! 警告: {CONFIG_FILE} 文件格式错误，将使用默认配置。")
            return DEFAULT_CONFIG.copy()


def save_config(config):
    config_to_save = {
        "target_url": config.get("target_url"),
        "chrome_path": config.get("chrome_path")
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_to_save, f, indent=4, ensure_ascii=False)
    print(f"⭐ 配置已保存/更新到 {CONFIG_FILE}。下次运行将直接加载。")


def validate_and_launch_driver(path_to_chrome: str):
    """尝试使用给定路径启动 Chrome 驱动程序。"""
    chrome_options = Options()

    # 设置为无头模式以节省资源
    # chrome_options.add_argument("--headless=new")
    # chrome_options.add_argument("--disable-gpu")

    if not path_to_chrome or not os.path.exists(path_to_chrome):
        return None, f"Chrome.exe 路径配置错误或文件不存在。"

    chrome_options.binary_location = path_to_chrome
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver, None
    except SessionNotCreatedException:
        return None, "会话创建失败，可能是 Chrome 版本与驱动不兼容。"
    except Exception as e:
        return None, f"启动时发生未知错误: {e}"
