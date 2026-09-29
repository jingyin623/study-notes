import os
import json
import random
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pygame

# 初始化 pygame 音频播放引擎
pygame.mixer.init()

# 获取当前 Python 脚本所在的目录绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 基于脚本所在目录定义配置文件路径及音频存放根目录
CONFIG_FILE = os.path.join(BASE_DIR, "phonetics_data.json")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

# 默认发音数据集
DEFAULT_PHONETICS = [
    ("A a", "Tag", "audio/元音/a.mp3", "元音"),
    ("E e", "Tee", "audio/元音/e.mp3", "元音"),
    ("I i", "wie", "audio/元音/i.mp3", "元音"),
]

# 全组件配色主题定义
THEMES = {
    "light": {
        "bg_main": "#f5f6fa",
        "bg_top": "#ebedf0",
        "bg_card": "#ffffff",
        "bg_header": "#e2e8f0",
        "fg_header_text": "#2c3e50",
        "fg_label": "#34495e",
        "sound_fg": "#2c3e50",
        "example_fg": "#7f8c8d",
        "card_border": "#dcdde1",
        "entry_bg": "#ffffff",
        "entry_fg": "#2c3e50",
        "btn_theme_bg": "#34495e",
        "btn_theme_fg": "#ffffff",
        "btn_theme_text": "🌙 夜间模式"
    },
    "dark": {
        "bg_main": "#1e1e2e",
        "bg_top": "#181825",
        "bg_card": "#313244",
        "bg_header": "#45475a",
        "fg_header_text": "#cdd6f4",
        "fg_label": "#cdd6f4",
        "sound_fg": "#89b4fa",
        "example_fg": "#bac2de",
        "card_border": "#585b70",
        "entry_bg": "#313244",
        "entry_fg": "#cdd6f4",
        "btn_theme_bg": "#f9e2af",
        "btn_theme_fg": "#11111b",
        "btn_theme_text": "☀️ 日间模式"
    }
}

class ResizableMP3GermanPhoneticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("德语发音点读训练器")
        self.root.minsize(1050, 420)
        
        # 主题控制
        self.is_dark_mode = False
        self.theme = THEMES["light"]

        # 配置 TTK 样式
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.root.configure(bg=self.theme["bg_main"])

        # 读取配置数据
        win_size, card_size, self.phonetics_list = self.load_data()

        # 还原上次保存的窗口大小与卡片宽高
        self.root.geometry(f"{max(win_size[0], 1050)}x{max(win_size[1], 420)}")
        self.card_w_var = tk.IntVar(value=card_size[0])
        self.card_h_var = tk.IntVar(value=card_size[1])
        self.cols = 6

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 状态控制
        self.delete_mode = False
        self.move_mode = False
        self.selected_indices = set()
        self.is_topmost = False
        self._shuffled_cache = None

        # ---------------- 顶部工具栏 ----------------
        self.top_frame = tk.Frame(root, bg=self.theme["bg_top"], pady=12)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=15)

        # 1. 分组筛选容器
        self.frame_group = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_group.grid(row=0, column=0, sticky="ew", padx=3)
        self.lbl_group = tk.Label(self.frame_group, text="分组:", font=("Helvetica", 10, "bold"), bg=self.theme["bg_top"], fg=self.theme["fg_label"])
        self.lbl_group.pack(side=tk.LEFT, padx=(0, 2))
        self.group_filter_var = tk.StringVar(value="全部分组")
        self.group_combo = ttk.Combobox(
            self.frame_group, textvariable=self.group_filter_var,
            state="readonly", font=("Helvetica", 9)
        )
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.group_combo.bind("<<ComboboxSelected>>", lambda e: self.on_group_filter_change())

        # 2. 排序方式容器
        self.frame_sort = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_sort.grid(row=0, column=1, sticky="ew", padx=3)
        self.lbl_sort = tk.Label(self.frame_sort, text="排序:", font=("Helvetica", 10, "bold"), bg=self.theme["bg_top"], fg=self.theme["fg_label"])
        self.lbl_sort.pack(side=tk.LEFT, padx=(0, 2))
        self.sort_var = tk.StringVar(value="默认顺序")
        self.sort_combo = ttk.Combobox(
            self.frame_sort, textvariable=self.sort_var, 
            values=["默认顺序", "音素 (A-Z)", "例词 (A-Z)", "🔀 随机打乱"],
            state="readonly", font=("Helvetica", 9)
        )
        self.sort_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.on_sort_change())

        # 3. 卡片尺寸容器
        self.frame_size = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_size.grid(row=0, column=2, sticky="ew", padx=3)
        self.lbl_w = tk.Label(self.frame_size, text="宽:", font=("Helvetica", 9, "bold"), bg=self.theme["bg_top"], fg=self.theme["fg_label"])
        self.lbl_w.pack(side=tk.LEFT)
        self.spin_w = tk.Spinbox(
            self.frame_size, from_=80, to=400, increment=10, textvariable=self.card_w_var, 
            width=3, font=("Helvetica", 9), command=self.on_size_change,
            bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["entry_fg"]
        )
        self.spin_w.pack(side=tk.LEFT, padx=(2, 4))
        self.spin_w.bind("<Return>", lambda e: self.on_size_change())

        self.lbl_h = tk.Label(self.frame_size, text="高:", font=("Helvetica", 9, "bold"), bg=self.theme["bg_top"], fg=self.theme["fg_label"])
        self.lbl_h.pack(side=tk.LEFT)
        self.spin_h = tk.Spinbox(
            self.frame_size, from_=50, to=300, increment=10, textvariable=self.card_h_var, 
            width=3, font=("Helvetica", 9), command=self.on_size_change,
            bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["entry_fg"]
        )
        self.spin_h.pack(side=tk.LEFT, padx=(2, 0))
        self.spin_h.bind("<Return>", lambda e: self.on_size_change())

        # 4. 主题切换按钮
        self.frame_theme = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_theme.grid(row=0, column=3, sticky="ew", padx=3)
        self.btn_theme = tk.Button(
            self.frame_theme, text=self.theme["btn_theme_text"], font=("Helvetica", 9, "bold"),
            bg=self.theme["btn_theme_bg"], fg=self.theme["btn_theme_fg"],
            activebackground="#2c3e50", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_theme
        )
        self.btn_theme.pack(fill=tk.X, expand=True)

        # 5. 添加单个发音按钮容器
        self.frame_add = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_add.grid(row=0, column=4, sticky="ew", padx=3)
        btn_add = tk.Button(
            self.frame_add, text="➕ 单个添加", font=("Helvetica", 9, "bold"),
            bg="#2ecc71", fg="white", activebackground="#27ae60", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.open_add_dialog
        )
        btn_add.pack(fill=tk.X, expand=True)

        # 6. 批量导入按钮容器
        self.frame_batch = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_batch.grid(row=0, column=5, sticky="ew", padx=3)
        btn_batch = tk.Button(
            self.frame_batch, text="📥 批量导入", font=("Helvetica", 9, "bold"),
            bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.open_batch_import_dialog
        )
        btn_batch.pack(fill=tk.X, expand=True)

        # 7. 词块转移按钮容器
        self.frame_move = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_move.grid(row=0, column=6, sticky="ew", padx=3)
        self.btn_move_mode = tk.Button(
            self.frame_move, text="📦 词块转移", font=("Helvetica", 9, "bold"),
            bg="#9b59b6", fg="white", activebackground="#8e44ad", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_move_mode
        )
        self.btn_move_mode.pack(fill=tk.X, expand=True)

        self.btn_confirm_move = tk.Button(
            self.frame_move, text="🚀 转移 (0)", font=("Helvetica", 9, "bold"),
            bg="#8e44ad", fg="white", activebackground="#71368a", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.confirm_move
        )

        # 8. 删除模式容器
        self.frame_delete = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_delete.grid(row=0, column=7, sticky="ew", padx=3)
        self.btn_delete_mode = tk.Button(
            self.frame_delete, text="🗑️ 卡片删除", font=("Helvetica", 9, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_delete_mode
        )
        self.btn_delete_mode.pack(fill=tk.X, expand=True)

        self.btn_confirm_delete = tk.Button(
            self.frame_delete, text="🔥 确认删除 (0)", font=("Helvetica", 9, "bold"),
            bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.confirm_delete
        )

        # 9. 窗口置顶容器
        self.frame_topmost = tk.Frame(self.top_frame, bg=self.theme["bg_top"])
        self.frame_topmost.grid(row=0, column=8, sticky="ew", padx=3)
        self.btn_topmost = tk.Button(
            self.frame_topmost, text="📌 窗口置顶", font=("Helvetica", 9, "bold"),
            bg="#34495e", fg="white", activebackground="#2c3e50", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_topmost
        )
        self.btn_topmost.pack(fill=tk.X, expand=True)

        column_minsizes = [100, 100, 95, 95, 90, 90, 90, 90, 85]
        for col_idx, min_w in enumerate(column_minsizes):
            self.top_frame.columnconfigure(col_idx, weight=1, minsize=min_w)

        # ---------------- 滚动卡片容器 ----------------
        self.container = tk.Frame(root, bg=self.theme["bg_main"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.canvas = tk.Canvas(self.container, bg=self.theme["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme["bg_main"])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.apply_theme_styles()
        self.update_group_filter_options()
        self._render_all_cards()

    def apply_theme_styles(self):
        """同步更新组件与 TTK 控件主题样式"""
        if self.is_dark_mode:
            self.style.configure("TCombobox", fieldbackground="#313244", background="#45475a", foreground="#cdd6f4", arrowcolor="#cdd6f4")
            self.style.map("TCombobox", fieldbackground=[("readonly", "#313244")], foreground=[("readonly", "#cdd6f4")])
            self.style.configure("TScrollbar", background="#45475a", troughcolor="#1e1e2e", arrowcolor="#cdd6f4")
        else:
            self.style.configure("TCombobox", fieldbackground="#ffffff", background="#ebedf0", foreground="#2c3e50", arrowcolor="#2c3e50")
            self.style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#2c3e50")])
            self.style.configure("TScrollbar", background="#dcdde1", troughcolor="#f5f6fa", arrowcolor="#2c3e50")

    def toggle_theme(self):
        """切换日间/夜间模式全控件全色彩响应"""
        self.is_dark_mode = not self.is_dark_mode
        self.theme = THEMES["dark"] if self.is_dark_mode else THEMES["light"]
        
        # 更新全视图背景
        self.root.configure(bg=self.theme["bg_main"])
        self.top_frame.configure(bg=self.theme["bg_top"])
        self.container.configure(bg=self.theme["bg_main"])
        self.canvas.configure(bg=self.theme["bg_main"])
        self.scrollable_frame.configure(bg=self.theme["bg_main"])

        # 更新顶部工具栏及子级容器背景与文字
        for child in self.top_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=self.theme["bg_top"])
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, tk.Label):
                        sub_child.configure(bg=self.theme["bg_top"], fg=self.theme["fg_label"])
                    elif isinstance(sub_child, tk.Spinbox):
                        sub_child.configure(
                            bg=self.theme["entry_bg"], fg=self.theme["entry_fg"],
                            insertbackground=self.theme["entry_fg"]
                        )

        # 更新主题切换按钮
        self.btn_theme.config(
            text=self.theme["btn_theme_text"],
            bg=self.theme["btn_theme_bg"],
            fg=self.theme["btn_theme_fg"]
        )

        # 应用 TTK 下拉框与滚动条样式
        self.apply_theme_styles()

        # 重新渲染卡片及组标题
        self._render_all_cards()

    def on_closing(self):
        self.save_data()
        self.root.destroy()

    def get_all_groups(self):
        groups = []
        for item in self.phonetics_list:
            grp = item[3] if len(item) > 3 else "未分类"
            if grp not in groups:
                groups.append(grp)
        if "未分类" not in groups:
            groups.append("未分类")
        return groups

    def update_group_filter_options(self):
        groups = ["全部分组"] + self.get_all_groups()
        self.group_combo["values"] = groups
        if self.group_filter_var.get() not in groups:
            self.group_filter_var.set("全部分组")

    def on_group_filter_change(self):
        self._shuffled_cache = None
        self._render_all_cards()

    def load_data(self):
        default_win_size = [1200, 750]
        default_card_size = [160, 90]
        default_phonetics = list(DEFAULT_PHONETICS)

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        win_size = data.get("window_size", default_win_size)
                        card_size = data.get("card_size", default_card_size)
                        raw_phonetics = data.get("phonetics", default_phonetics)
                        phonetics = []
                        for item in raw_phonetics:
                            if len(item) == 3:
                                phonetics.append((item[0], item[1], item[2], "未分类"))
                            else:
                                phonetics.append(tuple(item))
                        return win_size, card_size, phonetics
            except Exception as e:
                print(f"读取配置失败，使用默认配置: {e}")
        
        return default_win_size, default_card_size, default_phonetics

    def save_data(self, win_size=None, card_size=None, data_list=None):
        if win_size is None:
            win_w = self.root.winfo_width()
            win_h = self.root.winfo_height()
            win_size = [win_w, win_h] if win_w > 100 and win_h > 100 else [1200, 750]

        if card_size is None:
            card_size = [self.card_w_var.get(), self.card_h_var.get()]

        if data_list is None:
            data_list = self.phonetics_list

        config_data = {
            "window_size": win_size,
            "card_size": card_size,
            "phonetics": data_list
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")

    def on_size_change(self):
        try:
            w = max(80, int(self.card_w_var.get()))
            h = max(50, int(self.card_h_var.get()))
            self.card_w_var.set(w)
            self.card_h_var.set(h)
        except ValueError:
            return
        
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:
            card_total_w = w + 4
            self.cols = max(1, canvas_width // card_total_w)
        self._render_all_cards()

    def on_canvas_resize(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

        card_w = max(80, self.card_w_var.get())
        card_total_w = card_w + 4
        new_cols = max(1, canvas_width // card_total_w)

        if new_cols != self.cols:
            self.cols = new_cols
            self._render_all_cards()

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes("-topmost", self.is_topmost)
        
        if self.is_topmost:
            self.btn_topmost.config(text="📌 取消置顶", bg="#8e44ad", activebackground="#9b59b6")
        else:
            self.btn_topmost.config(text="📌 窗口置顶", bg="#34495e", activebackground="#2c3e50")

    def on_sort_change(self):
        self._shuffled_cache = None
        self._render_all_cards()

    def toggle_delete_mode(self):
        if self.move_mode:
            self.toggle_move_mode()

        self.delete_mode = not self.delete_mode
        self.selected_indices.clear()

        if self.delete_mode:
            self.btn_delete_mode.config(text="✖️ 退出删除", bg="#7f8c8d", activebackground="#95a5a6")
            self.btn_confirm_delete.config(text="🔥 删除 (0)")
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            self.btn_confirm_delete.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        else:
            self.btn_delete_mode.config(text="🗑️ 卡片删除", bg="#e67e22", activebackground="#d35400")
            self.btn_confirm_delete.pack_forget()
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(fill=tk.X, expand=True)

        self._render_all_cards()

    def toggle_move_mode(self):
        if self.delete_mode:
            self.toggle_delete_mode()

        self.move_mode = not self.move_mode
        self.selected_indices.clear()

        if self.move_mode:
            self.btn_move_mode.config(text="✖️ 退出转移", bg="#7f8c8d", activebackground="#95a5a6")
            self.btn_confirm_move.config(text="🚀 转移 (0)")
            self.btn_move_mode.pack_forget()
            self.btn_move_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            self.btn_confirm_move.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        else:
            self.btn_move_mode.config(text="📦 词块转移", bg="#9b59b6", activebackground="#8e44ad")
            self.btn_confirm_move.pack_forget()
            self.btn_move_mode.pack_forget()
            self.btn_move_mode.pack(fill=tk.X, expand=True)

        self._render_all_cards()

    def confirm_move(self):
        if not self.selected_indices:
            messagebox.showinfo("提示", "请先选择需要转移的词块卡片！", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("选择目标转移分类")
        dialog.geometry("380x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog, 
            text=f"将选中的 {len(self.selected_indices)} 个词块转移至：", 
            font=("Helvetica", 10, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        existing_groups = self.get_all_groups()
        combo_target = ttk.Combobox(dialog, values=existing_groups, font=("Helvetica", 10), width=28)
        combo_target.set(existing_groups[0] if existing_groups else "未分类")
        combo_target.pack(padx=20, pady=(0, 20))

        def execute_move():
            target_group = combo_target.get().strip() or "未分类"
            
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

            target_audio_dir = os.path.join(AUDIO_DIR, target_group)
            os.makedirs(target_audio_dir, exist_ok=True)

            moved_count = 0
            for idx in self.selected_indices:
                item = self.phonetics_list[idx]
                label, word, old_rel_path, old_group = item[0], item[1], item[2], item[3] if len(item) > 3 else "未分类"

                if old_group == target_group:
                    continue

                filename = os.path.basename(old_rel_path)
                old_abs_path = old_rel_path if os.path.isabs(old_rel_path) else os.path.join(BASE_DIR, old_rel_path)

                dest_filename = filename
                target_abs_path = os.path.join(target_audio_dir, dest_filename)

                if os.path.exists(old_abs_path) and os.path.abspath(old_abs_path) != os.path.abspath(target_abs_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(target_abs_path):
                        dest_filename = f"{base}_{counter}{ext}"
                        target_abs_path = os.path.join(target_audio_dir, dest_filename)
                        counter += 1

                    try:
                        shutil.move(old_abs_path, target_abs_path)
                    except Exception as e:
                        print(f"移动文件失败 [{filename}]: {e}")

                new_rel_path = f"audio/{target_group}/{dest_filename}"
                self.phonetics_list[idx] = (label, word, new_rel_path, target_group)
                moved_count += 1

            self.save_data()
            self.update_group_filter_options()
            self.toggle_move_mode()
            dialog.destroy()
            messagebox.showinfo("成功", f"成功将 {moved_count} 个词块转移至【{target_group}】！", parent=self.root)

        btn_confirm = tk.Button(
            dialog, text="确认转移", font=("Helvetica", 10, "bold"),
            bg="#8e44ad", fg="white", activebackground="#71368a", activeforeground="white",
            relief="flat", padx=15, pady=6, cursor="hand2", command=execute_move
        )
        btn_confirm.pack()

    def rename_group(self, old_group_name):
        if old_group_name == "未分类":
            messagebox.showwarning("提示", "“未分类”为系统默认固定分组，无法修改名称！", parent=self.root)
            return

        new_group_name = simpledialog.askstring("修改分组名称", f"请输入【{old_group_name}】的新名称：", parent=self.root)
        if new_group_name is None:
            return

        new_group_name = new_group_name.strip()
        if not new_group_name or new_group_name == old_group_name:
            return

        old_audio_dir = os.path.join(AUDIO_DIR, old_group_name)
        new_audio_dir = os.path.join(AUDIO_DIR, new_group_name)

        if os.path.exists(old_audio_dir):
            try:
                os.makedirs(AUDIO_DIR, exist_ok=True)
                if not os.path.exists(new_audio_dir):
                    os.rename(old_audio_dir, new_audio_dir)
            except Exception as e:
                print(f"重命名音频目录失败: {e}")

        updated_list = []
        for item in self.phonetics_list:
            grp = item[3] if len(item) > 3 else "未分类"
            if grp == old_group_name:
                filename = os.path.basename(item[2])
                new_rel_path = f"audio/{new_group_name}/{filename}"
                updated_list.append((item[0], item[1], new_rel_path, new_group_name))
            else:
                updated_list.append(item)

        self.phonetics_list = updated_list

        if self.group_filter_var.get() == old_group_name:
            self.group_filter_var.set(new_group_name)

        self.save_data()
        self.update_group_filter_options()
        self._render_all_cards()

    def delete_group(self, group_name):
        if group_name == "未分类":
            messagebox.showwarning("提示", "“未分类”为系统默认固定分组，无法被删除！", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("删除分组确认")
        dialog.geometry("420x210")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        lbl_msg = tk.Label(
            dialog,
            text=f"请选择如何处理分组【{group_name}】下的词块及 MP3 文件：",
            font=("Helvetica", 10, "bold"),
            wraplength=380,
            justify="left"
        )
        lbl_msg.pack(padx=20, pady=(20, 15))

        action_choice = [None]

        def choice_move():
            action_choice[0] = 'move'
            dialog.destroy()

        def choice_delete():
            action_choice[0] = 'delete'
            dialog.destroy()

        def choice_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        btn_move = tk.Button(
            btn_frame, text="📦 移入【未分类】\n(保留卡片与音频)", font=("Helvetica", 9),
            bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white",
            relief="flat", cursor="hand2", pady=6, command=choice_move
        )
        btn_move.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        btn_del = tk.Button(
            btn_frame, text="💣 彻底删除\n(清理卡片与音频文件)", font=("Helvetica", 9, "bold"),
            bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white",
            relief="flat", cursor="hand2", pady=6, command=choice_delete
        )
        btn_del.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        btn_cancel = tk.Button(
            dialog, text="取消", font=("Helvetica", 9),
            bg="#95a5a6", fg="white", activebackground="#7f8c8d", activeforeground="white",
            relief="flat", cursor="hand2", width=10, command=choice_cancel
        )
        btn_cancel.pack(pady=(0, 15))

        self.root.wait_window(dialog)

        choice = action_choice[0]
        if not choice:
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass

        src_group_dir = os.path.join(AUDIO_DIR, group_name)

        if choice == 'move':
            uncategorized_dir = os.path.join(AUDIO_DIR, "未分类")
            os.makedirs(uncategorized_dir, exist_ok=True)

            updated_list = []
            for item in self.phonetics_list:
                grp = item[3] if len(item) > 3 else "未分类"
                if grp == group_name:
                    old_rel_path = item[2]
                    filename = os.path.basename(old_rel_path)
                    
                    old_abs_path = old_rel_path if os.path.isabs(old_rel_path) else os.path.join(BASE_DIR, old_rel_path)
                    
                    dest_filename = filename
                    if os.path.exists(old_abs_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(uncategorized_dir, dest_filename)):
                            dest_filename = f"{base}_{counter}{ext}"
                            counter += 1
                        
                        target_path = os.path.join(uncategorized_dir, dest_filename)
                        try:
                            shutil.move(old_abs_path, target_path)
                        except Exception as e:
                            print(f"移动音频文件失败 [{filename}]: {e}")

                    new_rel_path = f"audio/未分类/{dest_filename}"
                    updated_list.append((item[0], item[1], new_rel_path, "未分类"))
                else:
                    updated_list.append(item)

            self.phonetics_list = updated_list

            if os.path.exists(src_group_dir):
                try:
                    shutil.rmtree(src_group_dir, ignore_errors=True)
                except Exception as e:
                    print(f"清理分类音频文件夹失败: {e}")

        elif choice == 'delete':
            self.phonetics_list = [
                item for item in self.phonetics_list
                if (item[3] if len(item) > 3 else "未分类") != group_name
            ]

            if os.path.exists(src_group_dir):
                try:
                    shutil.rmtree(src_group_dir, ignore_errors=True)
                except Exception as e:
                    print(f"彻底删除分类音频文件夹失败: {e}")

        if self.group_filter_var.get() == group_name:
            self.group_filter_var.set("未分类")

        self.save_data()
        self.update_group_filter_options()
        self._render_all_cards()

    def open_batch_import_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("批量导入 MP3 发音卡片")
        dialog.geometry("480x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="导入的目标分组:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        existing_groups = self.get_all_groups()
        if not existing_groups:
            existing_groups = ["未分类", "元音", "变元音", "辅音", "复合元音"]
        combo_group = ttk.Combobox(dialog, values=existing_groups, font=("Helvetica", 10), width=32)
        combo_group.set(existing_groups[0] if existing_groups else "未分类")
        combo_group.pack(padx=20, pady=(0, 10))

        tip_text = (
            "💡 自动识别规则说明：\n"
            " • 优先根据文件名 '音素_例词.mp3'（例如 'Sch_Schule.mp3'）\n"
            "   自动解析为：音素为 Sch，例词为 Schule。\n"
            " • 若文件名不含下划线（例如 'Tag.mp3'），\n"
            "   音素与例词均默认自动设定为 'Tag'。"
        )
        lbl_tip = tk.Label(
            dialog, text=tip_text, font=("Helvetica", 9), fg="#34495e", justify="left",
            bg="#ecf0f1", bd=1, relief="solid", padx=12, pady=8
        )
        lbl_tip.pack(fill="x", padx=20, pady=(0, 12))

        selected_paths = []
        lbl_status = tk.Label(dialog, text="未选择任何 MP3 文件", font=("Helvetica", 9, "bold"), fg="#e74c3c")
        lbl_status.pack(pady=(0, 10))

        def select_files():
            nonlocal selected_paths
            files = filedialog.askopenfilenames(
                title="选择一个或多个 MP3 音频文件",
                filetypes=[("Audio Files", "*.mp3"), ("All Files", "*.*")]
            )
            if files:
                selected_paths = list(files)
                lbl_status.config(text=f"已选取 {len(selected_paths)} 个 MP3 文件", fg="#27ae60")

        def select_folder():
            nonlocal selected_paths
            folder = filedialog.askdirectory(title="选择包含 MP3 的文件夹")
            if folder:
                found_files = []
                for root_dir, _, filenames in os.walk(folder):
                    for fn in filenames:
                        if fn.lower().endswith(".mp3"):
                            found_files.append(os.path.join(root_dir, fn))
                selected_paths = found_files
                lbl_status.config(text=f"文件夹中共扫描到 {len(selected_paths)} 个 MP3 文件", fg="#27ae60")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(padx=20, pady=(0, 15))

        btn_files = tk.Button(btn_frame, text="📁 选择多个文件", font=("Helvetica", 9, "bold"), command=select_files, width=15, pady=4)
        btn_files.pack(side="left", padx=8)

        btn_folder = tk.Button(btn_frame, text="📂 选择整个文件夹", font=("Helvetica", 9, "bold"), command=select_folder, width=15, pady=4)
        btn_folder.pack(side="left", padx=8)

        def execute_import():
            group = combo_group.get().strip() or "未分类"
            if not selected_paths:
                messagebox.showwarning("提示", "请先选择需要导入的 MP3 文件或文件夹！", parent=dialog)
                return

            group_audio_dir = os.path.join(AUDIO_DIR, group)
            os.makedirs(group_audio_dir, exist_ok=True)

            imported_count = 0
            for src_path in selected_paths:
                filename = os.path.basename(src_path)
                stem, ext = os.path.splitext(filename)

                if "_" in stem:
                    parts = stem.split("_", 1)
                    label = parts[0].strip() or stem
                    word = parts[1].strip() or stem
                else:
                    label = stem
                    word = stem

                dest_filename = filename
                dest_path = os.path.join(group_audio_dir, dest_filename)
                
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_filename = f"{stem}_{counter}{ext}"
                        dest_path = os.path.join(group_audio_dir, dest_filename)
                        counter += 1

                    try:
                        shutil.copy2(src_path, dest_path)
                    except Exception as e:
                        print(f"拷贝文件失败 [{src_path}]: {e}")
                        continue

                relative_path = f"audio/{group}/{dest_filename}"
                self.phonetics_list.append((label, word, relative_path, group))
                imported_count += 1

            self.save_data()
            self.update_group_filter_options()
            self._render_all_cards()
            dialog.destroy()
            messagebox.showinfo("成功", f"成功批量导入 {imported_count} 个发音卡片到分组【{group}】！", parent=self.root)

        btn_confirm = tk.Button(
            dialog, text="🚀 开始导入", font=("Helvetica", 10, "bold"),
            bg="#2980b9", fg="white", activebackground="#3498db", activeforeground="white",
            relief="flat", padx=15, pady=6, cursor="hand2", command=execute_import
        )
        btn_confirm.pack(pady=5)

    def _render_all_cards(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        selected_group = self.group_filter_var.get()
        sort_mode = self.sort_var.get()

        all_groups = self.get_all_groups()
        if selected_group != "全部分组":
            groups_to_show = [selected_group] if selected_group in all_groups else []
        else:
            groups_to_show = all_groups

        current_row = 0

        for group_name in groups_to_show:
            group_items = [(idx, item) for idx, item in enumerate(self.phonetics_list)
                           if (item[3] if len(item) > 3 else "未分类") == group_name]

            if not group_items:
                continue

            if sort_mode == "音素 (A-Z)":
                group_items.sort(key=lambda x: x[1][0].lower())
            elif sort_mode == "例词 (A-Z)":
                group_items.sort(key=lambda x: x[1][1].lower())
            elif sort_mode == "🔀 随机打乱":
                random.shuffle(group_items)

            # 1. 分组标题标头
            header_frame = tk.Frame(self.scrollable_frame, bg=self.theme["bg_header"], bd=0)
            header_frame.grid(row=current_row, column=0, columnspan=self.cols, sticky="ew", pady=(10, 4), padx=2)

            header_label = tk.Label(
                header_frame, text=f"📂  {group_name}  ({len(group_items)})", 
                font=("Helvetica", 11, "bold"), bg=self.theme["bg_header"], fg=self.theme["fg_header_text"],
                anchor="w", padx=10, pady=5
            )
            header_label.pack(side=tk.LEFT)

            if group_name != "未分类":
                btn_rename = tk.Button(
                    header_frame, text="✏️ 修改组名", font=("Helvetica", 9),
                    bg=self.theme["bg_card"], fg=self.theme["fg_header_text"],
                    activebackground="#f1f2f6", activeforeground="#2c3e50",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.rename_group(g)
                )
                btn_rename.pack(side=tk.LEFT, padx=(10, 2))

                btn_delete_grp = tk.Button(
                    header_frame, text="🗑️ 删除分组", font=("Helvetica", 9),
                    bg=self.theme["bg_card"], fg="#c0392b",
                    activebackground="#f1f2f6", activeforeground="#e74c3c",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.delete_group(g)
                )
                btn_delete_grp.pack(side=tk.LEFT, padx=(2, 0))

            current_row += 1

            # 2. 渲染卡片
            for card_idx, (orig_idx, item) in enumerate(group_items):
                label_text = item[0]
                example_word = item[1]
                mp3_path = item[2]

                r = current_row + (card_idx // self.cols)
                c = card_idx % self.cols

                self._create_card(r, c, orig_idx, label_text, example_word, mp3_path)

            rows_used = (len(group_items) + self.cols - 1) // self.cols
            current_row += rows_used

    def _create_card(self, row, col, orig_idx, label_text, example_word, mp3_path):
        is_selected = orig_idx in self.selected_indices

        if self.move_mode:
            bg_color = "#d6a2e8" if is_selected else self.theme["bg_card"]
            border_color = "#8e44ad" if is_selected else self.theme["card_border"]
            sound_fg = "#8e44ad" if is_selected else self.theme["sound_fg"]
            example_fg = "#5e2a73" if is_selected else self.theme["example_fg"]
        else:
            bg_color = "#fab1a0" if is_selected else self.theme["bg_card"]
            border_color = "#e74c3c" if is_selected else self.theme["card_border"]
            sound_fg = "#c0392b" if is_selected else self.theme["sound_fg"]
            example_fg = "#636e72" if is_selected else self.theme["example_fg"]

        card_w = self.card_w_var.get()
        card_h = self.card_h_var.get()

        card = tk.Frame(
            self.scrollable_frame, bd=1, relief="solid", bg=bg_color, 
            highlightbackground=border_color, highlightthickness=2 if is_selected else 1,
            width=card_w, height=card_h, cursor="hand2"
        )
        card.pack_propagate(False)
        card.grid_propagate(False)
        card.grid(row=row, column=col, padx=2, pady=2)

        lbl_sound = tk.Label(
            card, text=label_text, font=("Helvetica", 15, "bold"), 
            bg=bg_color, fg=sound_fg, cursor="hand2"
        )
        lbl_sound.pack(expand=True, pady=(8, 0))

        lbl_example = tk.Label(
            card, text=f"{example_word}", font=("Helvetica", 10), 
            bg=bg_color, fg=example_fg, cursor="hand2"
        )
        lbl_example.pack(expand=True, pady=(0, 8))

        for widget in (card, lbl_sound, lbl_example):
            widget.bind("<Button-1>", lambda event, i=orig_idx, p=mp3_path: self.on_card_click(i, p))

    def on_card_click(self, orig_idx, mp3_path):
        if self.delete_mode:
            if orig_idx in self.selected_indices:
                self.selected_indices.remove(orig_idx)
            else:
                self.selected_indices.add(orig_idx)

            self.btn_confirm_delete.config(text=f"🔥 删除 ({len(self.selected_indices)})")
            self._render_all_cards()
        elif self.move_mode:
            if orig_idx in self.selected_indices:
                self.selected_indices.remove(orig_idx)
            else:
                self.selected_indices.add(orig_idx)

            self.btn_confirm_move.config(text=f"🚀 转移 ({len(self.selected_indices)})")
            self._render_all_cards()
        else:
            self.play_mp3_async(mp3_path)

    def confirm_delete(self):
        if not self.selected_indices:
            messagebox.showinfo("提示", "未选中任何卡片！")
            return

        if messagebox.askyesno("确认删除", f"确定要永久删除选中的 {len(self.selected_indices)} 个发音卡片吗？"):
            for idx in sorted(self.selected_indices, reverse=True):
                del self.phonetics_list[idx]

            self._shuffled_cache = None
            self.save_data()
            self.update_group_filter_options()
            self.toggle_delete_mode()

    def open_add_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加自定义发音卡片")
        dialog.geometry("440x360")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="音素/字母标识 (如: Sch):", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(12, 2))
        entry_label = tk.Entry(dialog, font=("Helvetica", 10), width=32)
        entry_label.pack(padx=20, pady=(0, 8))

        tk.Label(dialog, text="代表例词 (如: Schule):", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(4, 2))
        entry_word = tk.Entry(dialog, font=("Helvetica", 10), width=32)
        entry_word.pack(padx=20, pady=(0, 8))

        tk.Label(dialog, text="所属分组 (选择或直接输入新分组名称):", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(4, 2))
        existing_groups = self.get_all_groups()
        if not existing_groups:
            existing_groups = ["未分类", "元音", "变元音", "辅音", "复合元音"]
        combo_group = ttk.Combobox(dialog, values=existing_groups, font=("Helvetica", 10), width=30)
        combo_group.set(existing_groups[0] if existing_groups else "未分类")
        combo_group.pack(padx=20, pady=(0, 8))

        selected_file = tk.StringVar()

        def select_file():
            path = filedialog.askopenfilename(
                title="选择对应的 MP3 音频文件",
                filetypes=[("Audio Files", "*.mp3"), ("All Files", "*.*")]
            )
            if path:
                selected_file.set(path)

        tk.Label(dialog, text="选择 MP3 音频文件:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(4, 2))
        file_frame = tk.Frame(dialog)
        file_frame.pack(fill="x", padx=20, pady=(0, 12))

        entry_file = tk.Entry(file_frame, textvariable=selected_file, font=("Helvetica", 9), state="readonly")
        entry_file.pack(side="left", expand=True, fill="x")

        btn_browse = tk.Button(file_frame, text="浏览...", command=select_file)
        btn_browse.pack(side="right", padx=(5, 0))

        def save_card():
            label = entry_label.get().strip()
            word = entry_word.get().strip()
            group = combo_group.get().strip() or "未分类"
            src_file_path = selected_file.get().strip()

            if not label or not word or not src_file_path:
                messagebox.showwarning("提示", "请完整填写音素、例词、分组并选择 MP3 文件！", parent=dialog)
                return

            try:
                group_audio_dir = os.path.join(AUDIO_DIR, group)
                os.makedirs(group_audio_dir, exist_ok=True)

                file_name = os.path.basename(src_file_path)
                dest_file_path = os.path.join(group_audio_dir, file_name)

                if os.path.abspath(src_file_path) != os.path.abspath(dest_file_path):
                    shutil.copy2(src_file_path, dest_file_path)

                relative_path = f"audio/{group}/{file_name}"

                new_item = (label, word, relative_path, group)
                self.phonetics_list.append(new_item)
                self._shuffled_cache = None
                self.save_data()

                self.update_group_filter_options()
                self._render_all_cards()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"拷贝音频文件失败: {e}", parent=dialog)

        btn_save = tk.Button(
            dialog, text="保存并生成卡片", font=("Helvetica", 11, "bold"),
            bg="#34495e", fg="white", activebackground="#2c3e50", activeforeground="white",
            relief="flat", padx=15, pady=5, command=save_card
        )
        btn_save.pack(pady=5)

    def play_mp3_async(self, mp3_path):
        threading.Thread(target=self._play_mp3, args=(mp3_path,), daemon=True).start()

    def _play_mp3(self, mp3_path):
        full_path = mp3_path if os.path.isabs(mp3_path) else os.path.join(BASE_DIR, mp3_path)

        if os.path.exists(full_path):
            try:
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"播放失败 [{full_path}]: {e}")
        else:
            print(f"未找到音频文件: {full_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ResizableMP3GermanPhoneticsApp(root)
    root.mainloop()