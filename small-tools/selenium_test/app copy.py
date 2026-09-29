import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import os
from playwright.sync_api import sync_playwright

LOCAL_CHROME_PATH = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
LOGIN_URL = "http://qkjpw.ayuanwl.com/loginByPhone"
MAIN_PAGE_A = 'http://qkjpw.ayuanwl.com/main/first'
SEL_PHONE = '//*[@id="app"]/div[1]/form/div[1]/div/div/input'
SEL_GET_CODE = '//*[@id="app"]/div[1]/form/div[2]/div/div/div/button'
SEL_CODE = '//*[@id="app"]/div[1]/form/div[2]/div/div/input'
SEL_LOGIN = '//*[@id="app"]/div[1]/form/div[4]/button'
SEL_PROGRAM_A = '//*[@id="app"]/div[1]/div[1]/div/div[1]/a[3]'
SEL_INFO_DIV = '//*[@id="goodsMap-2"]'

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("监控控制面板")
        self.root.geometry("300x200")
        
        # UI 组件初始化
        tk.Label(root, text="关键字:").pack(pady=5)
        self.entry_keyword = tk.Entry(root)
        self.entry_keyword.pack()
        
        tk.Label(root, text="手机号:").pack(pady=5)
        self.entry_phone = tk.Entry(root)
        self.entry_phone.pack()
        
        tk.Button(root, text="开始", command=self.start_task).pack(pady=10)
        tk.Button(root, text="退出", command=self.exit_app).pack()

    def exit_app(self):
        self.root.destroy()
        os._exit(0) # 强制清理底层浏览器进程

    def start_task(self):
        keyword = self.entry_keyword.get().strip()
        # phone = self.entry_phone.get().strip()
        phone = '19946036483'
        
        if not keyword or not phone:
            messagebox.showwarning("错误", "请填写完整信息")
            return
            
        # 禁用按钮防止重复点击
        # 启动后台守护线程运行 Playwright 逻辑
        threading.Thread(target=self.run_playwright, args=(phone, keyword), daemon=True).start()

    def run_playwright(self, phone, keyword):
        with sync_playwright() as p:
            # 开启有头模式以便观察
            browser = p.chromium.launch(
                headless=False,
                executable_path=LOCAL_CHROME_PATH  # 直接点对点定位
                )
            print("浏览器已启动，正在登录...")
            page = browser.new_page()

            # --- 登录逻辑 ---
            page.goto(LOGIN_URL)
            page.fill(SEL_PHONE, phone)
            page.click(SEL_GET_CODE)

            # 跨线程请求主线程弹窗获取验证码
            code = self.ask_for_code_thread_safe()
            if not code:
                browser.close()
                return

            page.fill(SEL_CODE, code)
            page.click(SEL_LOGIN)
            
            # 等待跳转到主页 (根据实际 URL 规则调整)
            page.wait_for_url(f"**{MAIN_PAGE_A}**", timeout=15000)

            # --- 核心监控循环 ---
            while True:
                page.click(SEL_PROGRAM_A)
                
                # 等待目标 DIV 出现
                page.wait_for_selector(SEL_INFO_DIV, state="attached")
                
                # 抓取所有匹配的 DIV 文本内容
                div_elements = page.locator(SEL_INFO_DIV).all_inner_texts()
                if div_elements is not []:
                    print("已经抓取内容，即将对比数据")
                
                # 检查关键词
                is_found = any(keyword in text for text in div_elements)
                
                if is_found:
                    self.show_success_thread_safe(keyword)
                    break
                
                # 未找到，等待 120 秒后刷新重试
                time.sleep(120)
                page.reload()

            browser.close()
            self.exit_app()

    # --- 线程安全的 GUI 调用封装 ---
    def ask_for_code_thread_safe(self):
        # 跨线程通信：使用 event 阻塞等待主线程回传数据
        result = []
        event = threading.Event()
        def _ask():
            res = simpledialog.askstring("验证码", "请输入收到的短信验证码:", parent=self.root)
            result.append(res)
            event.set()
        self.root.after(0, _ask)
        event.wait()
        return result[0] if result else None

    def show_success_thread_safe(self, keyword):
        event = threading.Event()
        def _show():
            messagebox.showinfo("监控触发", f"已捕获目标关键字: {keyword}")
            event.set()
        self.root.after(0, _show)
        event.wait()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()