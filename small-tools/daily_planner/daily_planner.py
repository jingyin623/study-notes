import tkinter as tk
from tkinter import messagebox, ttk
from plyer import notification
import datetime
import time
import threading
import json
import os
import winsound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "disciplined_life.json")

class PersistentReminder:
    def __init__(self, root):
        self.root = root
        self.data = self.load_data()
        self.schedule = self.data.get("schedule", [])
        self.settings = self.data.get("settings", {"geometry": "320x180+100+100"})

        self.root.overrideredirect(True)      
        self.root.attributes("-topmost", True) 
        self.root.geometry(self.settings.get("geometry"))
        self.root.configure(bg="#2b2b2b")      

        self.last_notified = ""
        self.build_main_ui()

        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        self.root.bind("<ButtonRelease-1>", self.save_window_state)

        self.update_clock()
        threading.Thread(target=self.scheduler_engine, daemon=True).start()

    def load_data(self):
        default_data = {
            "schedule": [["06:50", "【黄金100分】Python 学习"], ],
            "settings": {"geometry": "320x180+100+100"}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        return {"schedule": content, "settings": default_data["settings"]}
                    return content
            except:
                pass
        return default_data

    def build_main_ui(self):
        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(anchor="ne", padx=5, pady=2)
        tk.Button(btn_frame, text="—", command=self.minimize, font=("Arial", 9),
                  bg="#2b2b2b", fg="#7f8c8d", bd=0, activebackground="#3d3d3d").pack(side="left")
        tk.Button(btn_frame, text="✕", command=self.safe_exit, font=("Arial", 9),
                  bg="#2b2b2b", fg="#7f8c8d", bd=0, activebackground="#c0392b").pack(side="left", padx=5)

        self.label_time = tk.Label(self.root, text="", font=("Helvetica", 20, "bold"), bg="#2b2b2b", fg="#81a1c1") 
        self.label_time.pack()
        tk.Label(self.root, text="CURRENT TASK", font=("Helvetica", 7, "bold"), bg="#2b2b2b", fg="#5e81ac").pack()
        self.label_task = tk.Label(self.root, text="载入中...", font=("Microsoft YaHei", 11), bg="#2b2b2b", fg="#eceff4", wraplength=280)
        self.label_task.pack(pady=(0, 10))

        self.next_frame = tk.Frame(self.root, bg="#3b4252", padx=10, pady=5)
        self.next_frame.pack(fill="x", side="bottom")
        self.label_next = tk.Label(self.next_frame, text="NEXT: ...", font=("Microsoft YaHei", 9), bg="#3b4252", fg="#a3be8c", wraplength=280, justify="left")
        self.label_next.pack(anchor="w")

        self.manage_btn = tk.Button(self.root, text="⚙", command=self.open_manage_window, font=("Arial", 10), bg="#2b2b2b", fg="#4c566a", bd=0)
        self.manage_btn.place(x=5, y=5)

    # --- 核心：补全二级管理窗口 ---
    def open_manage_window(self):
        m_win = tk.Toplevel(self.root)
        m_win.title("日程管理")
        m_win.geometry("420x400")
        m_win.attributes("-topmost", True)
        
        # 1. 点选时间区域
        pick_f = tk.Frame(m_win, pady=15)
        pick_f.pack()
        
        hours = [str(i).zfill(2) for i in range(24)]
        mins = [str(i).zfill(2) for i in range(60)]
        
        h_cb = ttk.Combobox(pick_f, values=hours, width=5, state="readonly")
        h_cb.set(datetime.datetime.now().strftime("%H"))
        h_cb.pack(side="left")
        
        tk.Label(pick_f, text=":").pack(side="left")
        
        m_cb = ttk.Combobox(pick_f, values=mins, width=5, state="readonly")
        m_cb.set(datetime.datetime.now().strftime("%M"))
        m_cb.pack(side="left")
        
        tk.Label(pick_f, text=" 任务内容:").pack(side="left", padx=(10, 0))
        c_ent = tk.Entry(pick_f, width=20)
        c_ent.pack(side="left", padx=5)

        # 2. 列表展示区域
        lb_frame = tk.Frame(m_win)
        lb_frame.pack(fill="both", expand=True, padx=20)
        
        scrollbar = tk.Scrollbar(lb_frame)
        scrollbar.pack(side="right", fill="y")
        
        lb = tk.Listbox(lb_frame, font=("Microsoft YaHei", 9), height=10, yscrollcommand=scrollbar.set)
        lb.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lb.yview)

        def refresh_list():
            lb.delete(0, tk.END)
            self.schedule.sort()
            for t, c in self.schedule:
                lb.insert(tk.END, f"  [{t}]  {c}")

        def add_item():
            time_str = f"{h_cb.get()}:{m_cb.get()}"
            content = c_ent.get().strip()
            if content:
                # 覆盖同时间的旧任务
                self.schedule = [item for item in self.schedule if item[0] != time_str]
                self.schedule.append([time_str, content])
                self.save_all_data()
                refresh_list()
                c_ent.delete(0, tk.END)
            else:
                messagebox.showwarning("提示", "请输入任务内容")

        def del_item():
            selection = lb.curselection()
            if selection:
                item_text = lb.get(selection[0])
                # 解析出时间戳 [HH:MM]
                time_key = item_text.split(']')[0].split('[')[1].strip()
                self.schedule = [item for item in self.schedule if item[0] != time_key]
                self.save_all_data()
                refresh_list()

        # 3. 操作按钮区域
        btn_f = tk.Frame(m_win, pady=15)
        btn_f.pack()
        tk.Button(btn_f, text=" 添加 / 更新 ", command=add_item, bg="#a3be8c", width=12).pack(side="left", padx=10)
        tk.Button(btn_f, text=" 删除选中 ", command=del_item, bg="#bf616a", fg="white", width=12).pack(side="left", padx=10)

        refresh_list()

    # --- 其他原有功能保持不变 ---
    def play_alert_sound(self):
        try: winsound.Beep(523, 500)
        except: pass

    def show_auto_close_toast(self, task_name):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg="#ebcb8b")
        w, h = 280, 80
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        toast.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 50}")
        tk.Label(toast, text="⏰ 纪律执行时间", font=("Microsoft YaHei", 10, "bold"), bg="#ebcb8b").pack(pady=5)
        tk.Label(toast, text=task_name, font=("Microsoft YaHei", 11), bg="#ebcb8b", wraplength=250).pack()
        toast.after(10000, toast.destroy)

    def scheduler_engine(self):
        while True:
            now_hm = datetime.datetime.now().strftime("%H:%M")
            curr_c, next_i = "自由时间", "今日已完成"
            for i, (t, task) in enumerate(self.schedule):
                if now_hm == t and self.last_notified != t:
                    self.last_notified = t
                    threading.Thread(target=self.play_alert_sound, daemon=True).start()
                    notification.notify(title="任务提醒", message=task)
                    self.root.after(0, lambda t=task: self.show_auto_close_toast(t))
                if now_hm >= t:
                    curr_c = task
                    if i + 1 < len(self.schedule):
                        next_i = f"NEXT ({self.schedule[i+1][0]}): {self.schedule[i+1][1]}"
                elif i == 0 and now_hm < t:
                    next_i = f"NEXT ({t}): {task}"
            self.label_task.config(text=curr_c)
            self.label_next.config(text=next_i)
            time.sleep(10)

    def save_all_data(self):
        self.schedule.sort()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"schedule": self.schedule, "settings": self.settings}, f, ensure_ascii=False, indent=2)

    def save_window_state(self, event=None):
        self.settings["geometry"] = self.root.winfo_geometry()
        self.save_all_data()

    def safe_exit(self):
        self.save_window_state()
        self.root.quit()

    def start_move(self, event): self.x, self.y = event.x, event.y
    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")
    def update_clock(self):
        self.label_time.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)
    def minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<FocusIn>", lambda e: self.root.overrideredirect(True))

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam') # 使用 clam 主题让 Combobox 更好看
    app = PersistentReminder(root)
    root.mainloop()