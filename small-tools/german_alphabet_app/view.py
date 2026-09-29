import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

class PhoneticsView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller

        self.root.title("德语发音点读训练器 (MVC 重构版)")
        self.root.minsize(1050, 420)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.card_w_var = tk.IntVar()
        self.card_h_var = tk.IntVar()
        self.cols = 6

        self._build_ui()

    def _build_ui(self):
        # 顶部工具栏容器
        self.top_frame = tk.Frame(self.root, pady=12)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=15)

        # 1. 分组筛选容器
        self.frame_group = tk.Frame(self.top_frame)
        self.frame_group.grid(row=0, column=0, sticky="ew", padx=3)
        self.lbl_group = tk.Label(self.frame_group, text="分组:", font=("Helvetica", 10, "bold"))
        self.lbl_group.pack(side=tk.LEFT, padx=(0, 2))
        self.group_filter_var = tk.StringVar(value="全部分组")
        self.group_combo = ttk.Combobox(self.frame_group, textvariable=self.group_filter_var, state="readonly", font=("Helvetica", 9))
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 2. 排序方式容器
        self.frame_sort = tk.Frame(self.top_frame)
        self.frame_sort.grid(row=0, column=1, sticky="ew", padx=3)
        self.lbl_sort = tk.Label(self.frame_sort, text="排序:", font=("Helvetica", 10, "bold"))
        self.lbl_sort.pack(side=tk.LEFT, padx=(0, 2))
        self.sort_var = tk.StringVar(value="默认顺序")
        self.sort_combo = ttk.Combobox(
            self.frame_sort, textvariable=self.sort_var, 
            values=["默认顺序", "音素 (A-Z)", "例词 (A-Z)", "🔀 随机打乱"],
            state="readonly", font=("Helvetica", 9)
        )
        self.sort_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 3. 卡片尺寸容器
        self.frame_size = tk.Frame(self.top_frame)
        self.frame_size.grid(row=0, column=2, sticky="ew", padx=3)
        self.lbl_w = tk.Label(self.frame_size, text="宽:", font=("Helvetica", 9, "bold"))
        self.lbl_w.pack(side=tk.LEFT)
        self.spin_w = tk.Spinbox(self.frame_size, from_=80, to=400, increment=10, textvariable=self.card_w_var, width=3, font=("Helvetica", 9))
        self.spin_w.pack(side=tk.LEFT, padx=(2, 4))

        self.lbl_h = tk.Label(self.frame_size, text="高:", font=("Helvetica", 9, "bold"))
        self.lbl_h.pack(side=tk.LEFT)
        self.spin_h = tk.Spinbox(self.frame_size, from_=50, to=300, increment=10, textvariable=self.card_h_var, width=3, font=("Helvetica", 9))
        self.spin_h.pack(side=tk.LEFT, padx=(2, 0))

        # 4. 主题切换按钮
        self.frame_theme = tk.Frame(self.top_frame)
        self.frame_theme.grid(row=0, column=3, sticky="ew", padx=3)
        self.btn_theme = tk.Button(self.frame_theme, font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2", pady=4)
        self.btn_theme.pack(fill=tk.X, expand=True)

        # 5. 单个添加按钮容器
        self.frame_add = tk.Frame(self.top_frame)
        self.frame_add.grid(row=0, column=4, sticky="ew", padx=3)
        self.btn_add = tk.Button(
            self.frame_add, text="➕ 单个添加", font=("Helvetica", 9, "bold"),
            bg="#2ecc71", fg="white", activebackground="#27ae60", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )
        self.btn_add.pack(fill=tk.X, expand=True)

        # 6. 批量导入按钮容器
        self.frame_batch = tk.Frame(self.top_frame)
        self.frame_batch.grid(row=0, column=5, sticky="ew", padx=3)
        self.btn_batch = tk.Button(
            self.frame_batch, text="📥 批量导入", font=("Helvetica", 9, "bold"),
            bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )
        self.btn_batch.pack(fill=tk.X, expand=True)

        # 7. 词块转移按钮容器
        self.frame_move = tk.Frame(self.top_frame)
        self.frame_move.grid(row=0, column=6, sticky="ew", padx=3)
        self.btn_move_mode = tk.Button(
            self.frame_move, text="📦 词块转移", font=("Helvetica", 9, "bold"),
            bg="#9b59b6", fg="white", activebackground="#8e44ad", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )
        self.btn_move_mode.pack(fill=tk.X, expand=True)

        self.btn_confirm_move = tk.Button(
            self.frame_move, text="🚀 转移 (0)", font=("Helvetica", 9, "bold"),
            bg="#8e44ad", fg="white", activebackground="#71368a", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )

        # 8. 删除模式容器
        self.frame_delete = tk.Frame(self.top_frame)
        self.frame_delete.grid(row=0, column=7, sticky="ew", padx=3)
        self.btn_delete_mode = tk.Button(
            self.frame_delete, text="🗑️ 卡片删除", font=("Helvetica", 9, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )
        self.btn_delete_mode.pack(fill=tk.X, expand=True)

        self.btn_confirm_delete = tk.Button(
            self.frame_delete, text="🔥 确认删除 (0)", font=("Helvetica", 9, "bold"),
            bg="#e74c3c", fg="white", activebackground="#c0392b", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )

        # 9. 窗口置顶容器
        self.frame_topmost = tk.Frame(self.top_frame)
        self.frame_topmost.grid(row=0, column=8, sticky="ew", padx=3)
        self.btn_topmost = tk.Button(
            self.frame_topmost, text="📌 窗口置顶", font=("Helvetica", 9, "bold"),
            bg="#34495e", fg="white", activebackground="#2c3e50", activeforeground="white",
            relief="flat", cursor="hand2", pady=4
        )
        self.btn_topmost.pack(fill=tk.X, expand=True)

        column_minsizes = [100, 100, 95, 95, 90, 90, 90, 90, 85]
        for col_idx, min_w in enumerate(column_minsizes):
            self.top_frame.columnconfigure(col_idx, weight=1, minsize=min_w)

        # 滚动卡片容器
        self.container = tk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.canvas = tk.Canvas(self.container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def bind_events(self):
        self.group_combo.bind("<<ComboboxSelected>>", lambda e: self.controller.on_group_filter_changed(self.group_filter_var.get()))
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.controller.on_sort_changed(self.sort_var.get()))
        
        self.spin_w.config(command=self._on_card_size_changed)
        self.spin_w.bind("<Return>", lambda e: self._on_card_size_changed())
        self.spin_h.config(command=self._on_card_size_changed)
        self.spin_h.bind("<Return>", lambda e: self._on_card_size_changed())

        self.btn_theme.config(command=self.controller.toggle_theme)
        self.btn_add.config(command=self.open_add_dialog)
        self.btn_batch.config(command=self.open_batch_import_dialog)
        self.btn_move_mode.config(command=self.controller.toggle_move_mode)
        self.btn_confirm_move.config(command=self.open_confirm_move_dialog)
        self.btn_delete_mode.config(command=self.controller.toggle_delete_mode)
        self.btn_confirm_delete.config(command=self.controller.confirm_delete)
        self.btn_topmost.config(command=self.controller.toggle_topmost)
        self.root.protocol("WM_DELETE_WINDOW", self.controller.on_closing)

    def _on_card_size_changed(self):
        try:
            w = max(80, int(self.card_w_var.get()))
            h = max(50, int(self.card_h_var.get()))
            self.card_w_var.set(w)
            self.card_h_var.set(h)
            self.controller.on_size_changed(w, h)
        except ValueError:
            pass

    def _on_canvas_resize(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

        card_w = max(80, self.card_w_var.get())
        card_total_w = card_w + 4
        new_cols = max(1, canvas_width // card_total_w)

        if new_cols != self.cols:
            self.cols = new_cols
            self.render_all_cards()

    def update_theme(self, theme, is_dark):
        self.root.configure(bg=theme["bg_main"])
        self.top_frame.configure(bg=theme["bg_top"])
        self.container.configure(bg=theme["bg_main"])
        self.canvas.configure(bg=theme["bg_main"])
        self.scrollable_frame.configure(bg=theme["bg_main"])

        for child in self.top_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=theme["bg_top"])
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, tk.Label):
                        sub_child.configure(bg=theme["bg_top"], fg=theme["fg_label"])
                    elif isinstance(sub_child, tk.Spinbox):
                        sub_child.configure(
                            bg=theme["entry_bg"], fg=theme["entry_fg"],
                            insertbackground=theme["entry_fg"]
                        )

        self.btn_theme.config(
            text=theme["btn_theme_text"],
            bg=theme["btn_theme_bg"],
            fg=theme["btn_theme_fg"]
        )

        if is_dark:
            self.style.configure("TCombobox", fieldbackground="#313244", background="#45475a", foreground="#cdd6f4", arrowcolor="#cdd6f4")
            self.style.map("TCombobox", fieldbackground=[("readonly", "#313244")], foreground=[("readonly", "#cdd6f4")])
            self.style.configure("TScrollbar", background="#45475a", troughcolor="#1e1e2e", arrowcolor="#cdd6f4")
        else:
            self.style.configure("TCombobox", fieldbackground="#ffffff", background="#ebedf0", foreground="#2c3e50", arrowcolor="#2c3e50")
            self.style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#2c3e50")])
            self.style.configure("TScrollbar", background="#dcdde1", troughcolor="#f5f6fa", arrowcolor="#2c3e50")

    def update_groups_combobox(self, groups, current_selected):
        combo_groups = ["全部分组"] + groups
        self.group_combo["values"] = combo_groups
        if current_selected in combo_groups:
            self.group_filter_var.set(current_selected)
        else:
            self.group_filter_var.set("全部分组")

    def update_mode_buttons(self, move_mode, delete_mode, is_topmost, selected_count):
        if move_mode:
            self.btn_move_mode.config(text="✖️ 退出转移", bg="#7f8c8d", activebackground="#95a5a6")
            self.btn_confirm_move.config(text=f"🚀 转移 ({selected_count})")
            self.btn_move_mode.pack_forget()
            self.btn_move_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            self.btn_confirm_move.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        else:
            self.btn_move_mode.config(text="📦 词块转移", bg="#9b59b6", activebackground="#8e44ad")
            self.btn_confirm_move.pack_forget()
            self.btn_move_mode.pack_forget()
            self.btn_move_mode.pack(fill=tk.X, expand=True)

        if delete_mode:
            self.btn_delete_mode.config(text="✖️ 退出删除", bg="#7f8c8d", activebackground="#95a5a6")
            self.btn_confirm_delete.config(text=f"🔥 删除 ({selected_count})")
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
            self.btn_confirm_delete.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))
        else:
            self.btn_delete_mode.config(text="🗑️ 卡片删除", bg="#e67e22", activebackground="#d35400")
            self.btn_confirm_delete.pack_forget()
            self.btn_delete_mode.pack_forget()
            self.btn_delete_mode.pack(fill=tk.X, expand=True)

        if is_topmost:
            self.btn_topmost.config(text="📌 取消置顶", bg="#8e44ad", activebackground="#9b59b6")
        else:
            self.btn_topmost.config(text="📌 窗口置顶", bg="#34495e", activebackground="#2c3e50")

    def render_all_cards(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        grouped_items = self.controller.model.get_grouped_items()
        theme = self.controller.model.theme
        current_row = 0

        for group_name, group_items in grouped_items.items():
            header_frame = tk.Frame(self.scrollable_frame, bg=theme["bg_header"], bd=0)
            header_frame.grid(row=current_row, column=0, columnspan=self.cols, sticky="ew", pady=(10, 4), padx=2)

            header_label = tk.Label(
                header_frame, text=f"📂  {group_name}  ({len(group_items)})", 
                font=("Helvetica", 11, "bold"), bg=theme["bg_header"], fg=theme["fg_header_text"],
                anchor="w", padx=10, pady=5
            )
            header_label.pack(side=tk.LEFT)

            if group_name != "未分类":
                btn_rename = tk.Button(
                    header_frame, text="✏️ 修改组名", font=("Helvetica", 9),
                    bg=theme["bg_card"], fg=theme["fg_header_text"],
                    activebackground="#f1f2f6", activeforeground="#2c3e50",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.open_rename_group_dialog(g)
                )
                btn_rename.pack(side=tk.LEFT, padx=(10, 2))

                btn_delete_grp = tk.Button(
                    header_frame, text="🗑️ 删除分组", font=("Helvetica", 9),
                    bg=theme["bg_card"], fg="#c0392b",
                    activebackground="#f1f2f6", activeforeground="#e74c3c",
                    relief="groove", bd=1, cursor="hand2", padx=6, pady=2,
                    command=lambda g=group_name: self.open_delete_group_dialog(g)
                )
                btn_delete_grp.pack(side=tk.LEFT, padx=(2, 0))

            current_row += 1

            for card_idx, (orig_idx, item) in enumerate(group_items):
                label_text, example_word, mp3_path = item[0], item[1], item[2]
                r = current_row + (card_idx // self.cols)
                c = card_idx % self.cols

                self._create_card(r, c, orig_idx, label_text, example_word, mp3_path, theme)

            rows_used = (len(group_items) + self.cols - 1) // self.cols
            current_row += rows_used

    def _create_card(self, row, col, orig_idx, label_text, example_word, mp3_path, theme):
        is_selected = orig_idx in self.controller.model.selected_indices
        move_mode = self.controller.model.move_mode

        if move_mode:
            bg_color = "#d6a2e8" if is_selected else theme["bg_card"]
            border_color = "#8e44ad" if is_selected else theme["card_border"]
            sound_fg = "#8e44ad" if is_selected else theme["sound_fg"]
            example_fg = "#5e2a73" if is_selected else theme["example_fg"]
        else:
            bg_color = "#fab1a0" if is_selected else theme["bg_card"]
            border_color = "#e74c3c" if is_selected else theme["card_border"]
            sound_fg = "#c0392b" if is_selected else theme["sound_fg"]
            example_fg = "#636e72" if is_selected else theme["example_fg"]

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
            widget.bind("<Button-1>", lambda event, i=orig_idx, p=mp3_path: self.controller.on_card_clicked(i, p))

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
        existing_groups = self.controller.model.get_all_groups()
        combo_group = ttk.Combobox(dialog, values=existing_groups, font=("Helvetica", 10), width=30)
        combo_group.set(existing_groups[0] if existing_groups else "未分类")
        combo_group.pack(padx=20, pady=(0, 8))

        selected_file = tk.StringVar()
        def select_file():
            path = filedialog.askopenfilename(title="选择对应的 MP3 音频文件", filetypes=[("Audio Files", "*.mp3"), ("All Files", "*.*")])
            if path:
                selected_file.set(path)

        tk.Label(dialog, text="选择 MP3 音频文件:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(4, 2))
        file_frame = tk.Frame(dialog)
        file_frame.pack(fill="x", padx=20, pady=(0, 12))
        tk.Entry(file_frame, textvariable=selected_file, font=("Helvetica", 9), state="readonly").pack(side="left", expand=True, fill="x")
        tk.Button(file_frame, text="浏览...", command=select_file).pack(side="right", padx=(5, 0))

        def save_card():
            label = entry_label.get().strip()
            word = entry_word.get().strip()
            group = combo_group.get().strip() or "未分类"
            src_file_path = selected_file.get().strip()
            if not label or not word or not src_file_path:
                messagebox.showwarning("提示", "请完整填写音素、例词、分组并选择 MP3 文件！", parent=dialog)
                return
            self.controller.add_card(label, word, group, src_file_path)
            dialog.destroy()

        tk.Button(dialog, text="保存并生成卡片", font=("Helvetica", 11, "bold"), bg="#34495e", fg="white", relief="flat", padx=15, pady=5, command=save_card).pack(pady=5)

    def open_batch_import_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("批量导入 MP3 发音卡片")
        dialog.geometry("480x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="导入的目标分组:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        existing_groups = self.controller.model.get_all_groups()
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
        tk.Label(dialog, text=tip_text, font=("Helvetica", 9), fg="#34495e", justify="left", bg="#ecf0f1", bd=1, relief="solid", padx=12, pady=8).pack(fill="x", padx=20, pady=(0, 12))

        selected_paths = []
        lbl_status = tk.Label(dialog, text="未选择任何 MP3 文件", font=("Helvetica", 9, "bold"), fg="#e74c3c")
        lbl_status.pack(pady=(0, 10))

        def select_files():
            nonlocal selected_paths
            files = filedialog.askopenfilenames(title="选择一个或多个 MP3 音频文件", filetypes=[("Audio Files", "*.mp3"), ("All Files", "*.*")])
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
        tk.Button(btn_frame, text="📁 选择多个文件", font=("Helvetica", 9, "bold"), command=select_files, width=15, pady=4).pack(side="left", padx=8)
        tk.Button(btn_frame, text="📂 选择整个文件夹", font=("Helvetica", 9, "bold"), command=select_folder, width=15, pady=4).pack(side="left", padx=8)

        def execute_import():
            group = combo_group.get().strip() or "未分类"
            if not selected_paths:
                messagebox.showwarning("提示", "请先选择需要导入的 MP3 文件或文件夹！", parent=dialog)
                return
            count = self.controller.batch_import_files(group, selected_paths)
            dialog.destroy()
            messagebox.showinfo("成功", f"成功批量导入 {count} 个发音卡片到分组【{group}】！", parent=self.root)

        tk.Button(dialog, text="🚀 开始导入", font=("Helvetica", 10, "bold"), bg="#2980b9", fg="white", relief="flat", padx=15, pady=6, command=execute_import).pack(pady=5)

    def open_confirm_move_dialog(self):
        if not self.controller.model.selected_indices:
            messagebox.showinfo("提示", "请先选择需要转移的词块卡片！", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("选择目标转移分类")
        dialog.geometry("380x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"将选中的 {len(self.controller.model.selected_indices)} 个词块转移至：", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 10))
        existing_groups = self.controller.model.get_all_groups()
        combo_target = ttk.Combobox(dialog, values=existing_groups, font=("Helvetica", 10), width=28)
        combo_target.set(existing_groups[0] if existing_groups else "未分类")
        combo_target.pack(padx=20, pady=(0, 20))

        def execute_move():
            target_group = combo_target.get().strip() or "未分类"
            count = self.controller.move_selected(target_group)
            dialog.destroy()
            messagebox.showinfo("成功", f"成功将 {count} 个词块转移至【{target_group}】！", parent=self.root)

        tk.Button(dialog, text="确认转移", font=("Helvetica", 10, "bold"), bg="#8e44ad", fg="white", relief="flat", padx=15, pady=6, command=execute_move).pack()

    def open_rename_group_dialog(self, old_group_name):
        if old_group_name == "未分类":
            messagebox.showwarning("提示", "“未分类”为系统默认固定分组，无法修改名称！", parent=self.root)
            return
        new_group_name = simpledialog.askstring("修改分组名称", f"请输入【{old_group_name}】的新名称：", parent=self.root)
        if new_group_name and new_group_name.strip() and new_group_name.strip() != old_group_name:
            self.controller.rename_group(old_group_name, new_group_name.strip())

    def open_delete_group_dialog(self, group_name):
        if group_name == "未分类":
            messagebox.showwarning("提示", "“未分类”为系统默认固定分组，无法被删除！", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("删除分组确认")
        dialog.geometry("420x210")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"请选择如何处理分组【{group_name}】下的词块及 MP3 文件：", font=("Helvetica", 10, "bold"), wraplength=380, justify="left").pack(padx=20, pady=(20, 15))

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        def choice_move():
            dialog.destroy()
            self.controller.delete_group(group_name, 'move')

        def choice_delete():
            dialog.destroy()
            self.controller.delete_group(group_name, 'delete')

        tk.Button(btn_frame, text="📦 移入【未分类】\n(保留卡片与音频)", font=("Helvetica", 9), bg="#3498db", fg="white", relief="flat", pady=6, command=choice_move).pack(side=tk.LEFT, expand=True, fill="x", padx=5)
        tk.Button(btn_frame, text="💣 彻底删除\n(清理卡片与音频文件)", font=("Helvetica", 9, "bold"), bg="#e74c3c", fg="white", relief="flat", pady=6, command=choice_delete).pack(side=tk.LEFT, expand=True, fill="x", padx=5)
        tk.Button(dialog, text="取消", font=("Helvetica", 9), bg="#95a5a6", fg="white", relief="flat", width=10, command=dialog.destroy).pack(pady=(0, 15))