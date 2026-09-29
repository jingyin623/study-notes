# -*- coding: utf-8 -*-
"""
Excel 单词提取工具 v2.0

功能描述:
该工具用于从用户指定的Excel (.xlsx, .xls) 或 CSV 文件中，
提取第一列的所有非空文本数据，并将这些单词以逗号分隔的列表形式
写入到用户指定的TXT文件中。

使用方法:
1. 运行此脚本。
2. 点击“源 Excel 文件...”选择包含单词的Excel或CSV文件。
3. 点击“保存为(TXT)...”选择保存结果的TXT文件路径。
4. 点击“立即提取并创建文件”按钮执行操作。

注意:
- 脚本会自动处理目标文件夹的创建。
- 提取的单词将格式化为：[word1,word2,word3,...]
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
from pathlib import Path

# 获取当前文件的绝对路径 (包含文件名)
current_file_path = Path(__file__).resolve()

# 获取当前文件所在的文件夹路径 (不含文件名)
CURRENT_DIR = current_file_path.parent


class WordExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 单词提取工具 v2.0")
        self.root.geometry("550x280")

        # 定义存储路径的变量
        self.source_path = tk.StringVar()
        self.target_file_path = tk.StringVar()  # 现在直接存储完整的文件路径

        self.create_widgets()

    def create_widgets(self):
        # 1. 源文件选择区
        frame_src = tk.Frame(self.root, pady=15)
        frame_src.pack(fill="x", padx=20)

        tk.Label(frame_src, text="源 Excel 文件:", width=12, anchor="w").pack(
            side="left"
        )
        tk.Entry(frame_src, textvariable=self.source_path).pack(
            side="left", fill="x", expand=True, padx=5
        )
        tk.Button(frame_src, text="浏览...", width=8, command=self.select_source).pack(
            side="right"
        )

        # 2. 目标文件路径区 (支持手动输入文件名)
        frame_dst = tk.Frame(self.root, pady=15)
        frame_dst.pack(fill="x", padx=20)

        tk.Label(frame_dst, text="保存为(TXT):", width=12, anchor="w").pack(side="left")
        tk.Entry(frame_dst, textvariable=self.target_file_path).pack(
            side="left", fill="x", expand=True, padx=5
        )
        tk.Button(frame_dst, text="另存为...", width=8, command=self.save_as_file).pack(
            side="right"
        )

        # 3. 提交按钮
        self.btn_run = tk.Button(
            self.root,
            text="立即提取并创建文件",
            bg="#28a745",  # 绿色，代表执行
            fg="white",
            font=("微软雅黑", 10, "bold"),
            height=2,
            command=self.process_data,
        )
        self.btn_run.pack(pady=30, fill="x", padx=100)

    def select_source(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        if path:
            self.source_path.set(path)

    def save_as_file(self):
        # 弹出“另存为”对话框，默认后缀 .txt
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="extracted_words.txt",
        )
        if path:
            self.target_file_path.set(path)

    def process_data(self):
        src = self.source_path.get().strip()
        dst = self.target_file_path.get().strip()

        # 1. 基础校验
        if not src or not dst:
            messagebox.showwarning("校验失败", "请指定源文件和保存路径！")
            return

        # 确保后缀是 .txt
        if not dst.lower().endswith(".txt"):
            dst += ".txt"

        try:
            # 2. 自动创建目录逻辑
            target_dir = os.path.dirname(dst)
            if target_dir and not os.path.exists(target_dir):
                # 如果用户输入的路径包含不存在的文件夹，递归创建它们
                os.makedirs(target_dir)
                print(f"检测到目录不存在，已创建: {target_dir}")

            # 3. 读取数据
            if src.endswith(".csv"):
                df = pd.read_csv(src)
            else:
                df = pd.read_excel(src)

            # 提取第一列，去空，转字符串
            words = df.iloc[:, 0].dropna().astype(str).tolist()

            # 4. 写入文件
            with open(dst, "w", encoding="utf-8") as f:
                f.write(f"[")
                for word in words:
                    f.write(f"{word.strip()},")
                f.write(f"]")

            messagebox.showinfo(
                "任务成功", f"恭喜！\n已提取 {len(words)} 个单词到：\n{dst}"
            )

            # 可选：处理完后自动打开所在的文件夹
            os.startfile(os.path.dirname(dst))

        except Exception as e:
            messagebox.showerror("运行异常", f"处理过程中出错：\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WordExtractorApp(root)
    root.mainloop()
