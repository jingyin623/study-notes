import tkinter as tk
from tkinter import ttk, messagebox
import threading
from GetsJumpPoint import (
    FORECAST_LIST_ALL, add_code, remove_code, 
    quote_context_close, load_code, SUBSCRIBE_DICT_LIST
)

class GetsJumpPointTkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GetsJumpPoint (Tkinter)")
        self.root.geometry("350x650")
        self.root.attributes('-topmost', True) # 窗口置顶 [3]

        # 1. 数据展示列表 (对应 listView 和 listView_2)
        self.setup_display_area()

        # 2. 输入区域 (对应 MARKET_SECURITY_LE 等控件 [1, 2])
        self.setup_input_area()

        # 3. 初始化业务逻辑
        load_code() # 自动加载历史配置 [3, 4]
        self.refresh_loop() # 启动刷新循环

    def setup_display_area(self):
        # 顶部预测列表
        tk.Label(self.root, text="跳价预测:").pack(anchor="w")
        self.forecast_list = tk.Listbox(self.root, height=10)
        self.forecast_list.pack(fill="x", padx=5, pady=2)

        # 订阅信息列表
        tk.Label(self.root, text="订阅状态:").pack(anchor="w")
        self.subscribe_list = tk.Listbox(self.root, height=5)
        self.subscribe_list.pack(fill="x", padx=5, pady=2)

    def setup_input_area(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", padx=10, pady=10)

        # 定义输入标签与默认变量名 [1, 2]
        fields = [
            ("行情代码", "MARKET_SECURITY"),
            ("最小变动", "MARKET_SMALL"),
            ("交易代码", "TRADING_SECURITY"),
            ("交易经纪号", "TRADING_NUM"),
            ("敏感度", "TRADING_SENSITIVITY")
        ]
        self.entries = {}
        for i, (label_text, key) in enumerate(fields):
            tk.Label(frame, text=label_text).grid(row=i, column=0, sticky="e")
            entry = tk.Entry(frame)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.entries[key] = entry

        # 按钮区
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="提交任务", command=self.handle_submit).pack(side="left", padx=5)
        tk.Button(btn_frame, text="停止任务", command=self.handle_stop).pack(side="left", padx=5)
        tk.Button(btn_frame, text="保存退出", command=self.handle_exit).pack(side="left", padx=5)

    def handle_submit(self):
        # 获取输入值并调用业务逻辑 [5]
        data = {k: v.get() for k, v in self.entries.items()}
        if all(data.values()):
            add_code(data["MARKET_SECURITY"], data["MARKET_SMALL"], 
                     data["TRADING_SECURITY"], data["TRADING_NUM"], data["TRADING_SENSITIVITY"])
        else:
            messagebox.showwarning("提示", "请填写完整参数")

    def handle_stop(self):
        code = self.entries["TRADING_SECURITY"].get()
        if code:
            remove_code(code) # [6]

    def handle_exit(self):
        quote_context_close() # 关闭连接并保存 [7]
        self.root.quit()

    def refresh_loop(self):
        """每0.1秒刷新一次界面数据，替代原本的 UpdateThread [3]"""
        # 更新预测列表
        self.forecast_list.delete(0, tk.END)
        for item in FORECAST_LIST_ALL:
            self.forecast_list.insert(tk.END, item)
        
        # 更新订阅列表
        self.subscribe_list.delete(0, tk.END)
        for sub in SUBSCRIBE_DICT_LIST:
            self.subscribe_list.insert(tk.END, sub)

        self.root.after(100, self.refresh_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = GetsJumpPointTkApp(root)
    root.mainloop()
