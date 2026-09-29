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

# 默认发音数据集（格式：音素, 例词, 相对路径, 分组）
DEFAULT_PHONETICS = [
    ("A a", "Tag", "audio/元音/a.mp3", "元音"),
    ("E e", "Tee", "audio/元音/e.mp3", "元音"),
    ("I i", "wie", "audio/元音/i.mp3", "元音"),
]

class ResizableMP3GermanPhoneticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("德语发音点读训练器")
        self.root.minsize(800, 420)  # 设置全局窗口最小宽高，保护顶部工具栏组件
        self.root.configure(bg="#f5f6fa")

        # 读取配置数据
        win_size, card_size, self.phonetics_list = self.load_data()

        # 还原上次保存的窗口大小与卡片宽高
        self.root.geometry(f"{max(win_size[0], 800)}x{max(win_size[1], 420)}")
        self.card_w_var = tk.IntVar(value=card_size[0])
        self.card_h_var = tk.IntVar(value=card_size[1])
        self.cols = 6

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 状态控制
        self.delete_mode = False
        self.selected_indices = set()
        self.is_topmost = False
        self._shuffled_cache = None

        # ---------------- 顶部工具栏 (Grid 布局实现最小宽度与等比例缩放) ----------------
        top_frame = tk.Frame(root, bg="#f5f6fa", pady=12)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15)

        # 1. 分组筛选容器 (Column 0)
        frame_group = tk.Frame(top_frame, bg="#f5f6fa")
        frame_group.grid(row=0, column=0, sticky="ew", padx=3)
        tk.Label(frame_group, text="分组:", font=("Helvetica", 10, "bold"), bg="#f5f6fa", fg="#34495e").pack(side=tk.LEFT, padx=(0, 2))
        self.group_filter_var = tk.StringVar(value="全部分组")
        self.group_combo = ttk.Combobox(
            frame_group, textvariable=self.group_filter_var,
            state="readonly", font=("Helvetica", 9)
        )
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.group_combo.bind("<<ComboboxSelected>>", lambda e: self.on_group_filter_change())

        # 2. 排序方式容器 (Column 1)
        frame_sort = tk.Frame(top_frame, bg="#f5f6fa")
        frame_sort.grid(row=0, column=1, sticky="ew", padx=3)
        tk.Label(frame_sort, text="排序:", font=("Helvetica", 10, "bold"), bg="#f5f6fa", fg="#34495e").pack(side=tk.LEFT, padx=(0, 2))
        self.sort_var = tk.StringVar(value="默认顺序")
        self.sort_combo = ttk.Combobox(
            frame_sort, textvariable=self.sort_var, 
            values=["默认顺序", "音素 (A-Z)", "例词 (A-Z)", "🔀 随机打乱"],
            state="readonly", font=("Helvetica", 9)
        )
        self.sort_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.on_sort_change())

        # 3. 卡片尺寸容器 (Column 2)
        frame_size = tk.Frame(top_frame, bg="#f5f6fa")
        frame_size.grid(row=0, column=2, sticky="ew", padx=3)
        tk.Label(frame_size, text="宽:", font=("Helvetica", 9, "bold"), bg="#f5f6fa", fg="#34495e").pack(side=tk.LEFT)
        spin_w = tk.Spinbox(
            frame_size, from_=80, to=400, increment=10, textvariable=self.card_w_var, 
            width=3, font=("Helvetica", 9), command=self.on_size_change
        )
        spin_w.pack(side=tk.LEFT, padx=(2, 4))
        spin_w.bind("<Return>", lambda e: self.on_size_change())

        tk.Label(frame_size, text="高:", font=("Helvetica", 9, "bold"), bg="#f5f6fa", fg="#34495e").pack(side=tk.LEFT)
        spin_h = tk.Spinbox(
            frame_size, from_=50, to=300, increment=10, textvariable=self.card_h_var, 
            width=3, font=("Helvetica", 9), command=self.on_size_change
        )
        spin_h.pack(side=tk.LEFT, padx=(2, 0))
        spin_h.bind("<Return>", lambda e: self.on_size_change())

        # 4. 添加发音按钮容器 (Column 3)
        frame_add = tk.Frame(top_frame, bg="#f5f6fa")
        frame_add.grid(row=0, column=3, sticky="ew", padx=3)
        btn_add = tk.Button(
            frame_add, text="➕ 添加自定义发音", font=("Helvetica", 9, "bold"),
            bg="#2ecc71", fg="white", activebackground="#27ae60", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.open_add_dialog
        )
        btn_add.pack(fill=tk.X, expand=True)

        # 5. 删除模式容器 (Column 4)
        frame_delete = tk.Frame(top_frame, bg="#f5f6fa")
        frame_delete.grid(row=0, column=4, sticky="ew", padx=3)
        self.btn_delete_mode = tk.Button(
            frame_delete, text="🗑️ 进入卡片删除", font=("Helvetica", 9, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_delete_mode
        )
        self.btn_delete_mode.pack(fill=tk.X, expand=True)

        self.btn_confirm_delete = tk.Button(
            frame_delete, text="🔥 确认删除 (0)", font=("Helvetica", 9, "bold"),
            bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.confirm_delete
        )

        # 6. 窗口置顶容器 (Column 5)
        frame_topmost = tk.Frame(top_frame, bg="#f5f6fa")
        frame_topmost.grid(row=0, column=5, sticky="ew", padx=3)
        self.btn_topmost = tk.Button(
            frame_topmost, text="📌 窗口置顶", font=("Helvetica", 9, "bold"),
            bg="#34495e", fg="white", activebackground="#2c3e50", activeforeground="white",
            relief="flat", cursor="hand2", pady=4, command=self.toggle_topmost
        )
        self.btn_topmost.pack(fill=tk.X, expand=True)

        # 设置每一列的权重 (weight=1 实现等比例放大) 以及 最小宽度限制 (minsize 防止缩小被遮挡)
        column_minsizes = [125, 125, 115, 135, 140, 105]
        for col_idx, min_w in enumerate(column_minsizes):
            top_frame.columnconfigure(col_idx, weight=1, minsize=min_w)

        # ---------------- 滚动卡片容器 ----------------
        container = tk.Frame(root, bg="#f5f6fa")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.canvas = tk.Canvas(container, bg="#f5f6fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f5f6fa")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.update_group_filter_options()
        self._render_all_cards()

    def on_closing(self):
        """关闭窗口时的回调函数：保存当前所有配置"""
        self.save_data()
        self.root.destroy()

    def get_all_groups(self):
        """动态获取当前所有已有的分组列表（确保“未分类”始终存在）"""
        groups = []
        for item in self.phonetics_list:
            grp = item[3] if len(item) > 3 else "未分类"
            if grp not in groups:
                groups.append(grp)
        if "未分类" not in groups:
            groups.append("未分类")
        return groups

    def update_group_filter_options(self):
        """更新顶部工具栏的分组筛选选项"""
        groups = ["全部分组"] + self.get_all_groups()
        self.group_combo["values"] = groups
        if self.group_filter_var.get() not in groups:
            self.group_filter_var.set("全部分组")

    def on_group_filter_change(self):
        self._shuffled_cache = None
        self._render_all_cards()

    def load_data(self):
        """读取 JSON 配置，自动兼容带分组与不带分组的旧格式"""
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
        """持久化保存配置到脚本所在目录下"""
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
            card_total_w = w + 12
            self.cols = max(1, canvas_width // card_total_w)
        self._render_all_cards()

    def on_canvas_resize(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

        card_w = max(80, self.card_w_var.get())
        card_total_w = card_w + 12
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
        self.delete_mode = not self.delete_mode
        self.selected_indices.clear()

        if self.delete_mode:
            self.btn_delete_mode.config(text="✖️ 退出删除", bg="#7f8c8d", activebackground="#95a5a6")
            self.btn_confirm_delete.config(text="🔥 删除 (0)")
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            self.btn_confirm_delete.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        else:
            self.btn_delete_mode.config(text="🗑️ 进入卡片删除", bg="#e67e22", activebackground="#d35400")
            self.btn_confirm_delete.pack_forget()
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(fill=tk.X, expand=True)

        self._render_all_cards()

    def rename_group(self, old_group_name):
        """修改分组名称的方法（受保护组名“未分类”除外）"""
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
        """删除分组逻辑：将该分组下的所有发音词块及对应 MP3 文件移入“未分类”中，并完全销毁原语音分类文件夹"""
        if group_name == "未分类":
            messagebox.showwarning("提示", "“未分类”为系统默认固定分组，无法被删除！", parent=self.root)
            return

        if messagebox.askyesno("确认删除分组", f"确定要删除分组【{group_name}】吗？\n\n注意：删除分组不会删除卡片，该分组下的所有发音词块及其 MP3 音频将自动移入【未分类】中。", parent=self.root):
            # 1. 停止播放并卸载音频，避免资源锁定
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

            uncategorized_dir = os.path.join(AUDIO_DIR, "未分类")
            os.makedirs(uncategorized_dir, exist_ok=True)
            src_group_dir = os.path.join(AUDIO_DIR, group_name)

            # 2. 遍历卡片数据，剪切 MP3 文件并更新内存数据
            updated_list = []
            for item in self.phonetics_list:
                grp = item[3] if len(item) > 3 else "未分类"
                if grp == group_name:
                    old_rel_path = item[2]
                    filename = os.path.basename(old_rel_path)
                    
                    old_abs_path = old_rel_path if os.path.isabs(old_rel_path) else os.path.join(BASE_DIR, old_rel_path)
                    new_abs_path = os.path.join(uncategorized_dir, filename)
                    
                    # 防重名覆盖处理
                    dest_filename = filename
                    if os.path.exists(old_abs_path):
                        if old_abs_path != new_abs_path:
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

            # 3. 彻底删除原分类在 audio/ 目录下的空文件夹
            if os.path.exists(src_group_dir):
                try:
                    shutil.rmtree(src_group_dir, ignore_errors=True)
                except Exception as e:
                    print(f"清理分类音频文件夹失败: {e}")

            if self.group_filter_var.get() == group_name:
                self.group_filter_var.set("未分类")

            self.save_data()
            self.update_group_filter_options()
            self._render_all_cards()

    def _render_all_cards(self):
        """按分组分块渲染卡片（对非“未分类”分组提供修改与删除功能）"""
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

            # 1. 渲染分组标题标头容器
            header_frame = tk.Frame(self.scrollable_frame, bg="#e2e8f0", bd=0)
            header_frame.grid(row=current_row, column=0, columnspan=self.cols, sticky="ew", pady=(14, 6), padx=6)

            header_label = tk.Label(
                header_frame, text=f"📂  {group_name}  ({len(group_items)})", 
                font=("Helvetica", 11, "bold"), bg="#e2e8f0", fg="#2c3e50",
                anchor="w", padx=10, pady=5
            )
            header_label.pack(side=tk.LEFT)

            # 仅对普通分组展示“修改组名”和“删除分组”按钮，固定分组“未分类”不显示
            if group_name != "未分类":
                btn_rename = tk.Button(
                    header_frame, text="✏️ 修改组名", font=("Helvetica", 9),
                    bg="#ffffff", fg="#34495e", activebackground="#f1f2f6", activeforeground="#2c3e50",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.rename_group(g)
                )
                btn_rename.pack(side=tk.LEFT, padx=(10, 2))

                btn_delete_grp = tk.Button(
                    header_frame, text="🗑️ 删除分组", font=("Helvetica", 9),
                    bg="#ffffff", fg="#c0392b", activebackground="#f1f2f6", activeforeground="#e74c3c",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.delete_group(g)
                )
                btn_delete_grp.pack(side=tk.LEFT, padx=(2, 0))

            current_row += 1

            # 2. 渲染该分组下的所有字母卡片
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
        bg_color = "#fab1a0" if is_selected else "#ffffff"
        border_color = "#e74c3c" if is_selected else "#dcdde1"

        card_w = self.card_w_var.get()
        card_h = self.card_h_var.get()

        card = tk.Frame(
            self.scrollable_frame, bd=1, relief="solid", bg=bg_color, 
            highlightbackground=border_color, highlightthickness=2 if is_selected else 1,
            width=card_w, height=card_h, cursor="hand2"
        )
        card.pack_propagate(False)
        card.grid_propagate(False)
        card.grid(row=row, column=col, padx=6, pady=6)

        lbl_sound = tk.Label(
            card, text=label_text, font=("Helvetica", 15, "bold"), 
            bg=bg_color, fg="#c0392b" if is_selected else "#2c3e50", cursor="hand2"
        )
        lbl_sound.pack(expand=True, pady=(8, 0))

        lbl_example = tk.Label(
            card, text=f"例: {example_word}", font=("Helvetica", 10), 
            bg=bg_color, fg="#636e72" if is_selected else "#7f8c8d", cursor="hand2"
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