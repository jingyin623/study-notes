"""
Docstring for small-tools.findDuplicateFolders.find_null_folders_delete
无限循环空文件夹清理器 - 专业版
功能：
1. 扫描指定路径下的所有空文件夹（包括多层嵌套的空文件夹）
2. 显示扫描结果，允许用户选择性删除空文件夹
3. 支持一键全自动循环删除，直到所有层级的空文件夹均被清理干净
使用方法：
1. 运行脚本后，输入需要扫描的路径（支持多个路径，用逗号分隔）
2. 使用界面上的按钮进行手动删除或启动全自动清理
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --- 1. 核心扫描逻辑 ---
def find_empty_folders(paths_str):
    if not paths_str: return []
    paths = [p.strip() for p in paths_str.replace('，', ',').split(',') if p.strip()]
    empty_folders = []
    
    for p in paths:
        drive_path = p + '\\' if (p.endswith(':') and len(p) == 2) else p
        # topdown=False 确保先处理最深层的子目录
        for root, dirs, _ in os.walk(drive_path, topdown=False):
            for name in dirs:
                full_path = os.path.join(root, name)
                try:
                    if not os.listdir(full_path):
                        empty_folders.append(full_path)
                except Exception:
                    continue
    return empty_folders

# --- 2. 界面与交互逻辑 ---
class InfiniteCleanerApp:
    def __init__(self, initial_paths):
        self.root = tk.Tk()
        self.root.title("无限循环空文件夹清理器 - 专业版")
        self.root.geometry("1000x650")
        self.paths_str = initial_paths
        self.is_auto_running = False # 自动清理状态位
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        self.status_var = tk.StringVar(value="等待操作...")
        tk.Label(self.root, textvariable=self.status_var, fg="blue", pady=5).pack()

        columns = ("path",)
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("path", text="待清理的空文件夹路径")
        self.tree.column("path", width=900)

        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="top", fill="both", expand=True, padx=10)
        vsb.pack(side="right", fill="y")

        # 按钮区
        btn_frame = tk.Frame(self.root, pady=20)
        btn_frame.pack()

        tk.Button(btn_frame, text="🗑️ 安全删除", bg="#e1e1e1", 
                  command=lambda: self.execute_delete(True), padx=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="⚡ 快速清理", bg="#ffcccc", 
                  command=lambda: self.execute_delete(False), padx=15).pack(side=tk.LEFT, padx=5)

        # 新增的一键自动清理按钮
        self.auto_btn = tk.Button(btn_frame, text="🚀 一键自动清理 (全自动)", bg="#b2d8d8", 
                                  command=self.start_auto_clean, padx=15)
        self.auto_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 手动重新扫描", bg="#d1e7dd", 
                  command=self.refresh_list, padx=15).pack(side=tk.LEFT, padx=5)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_list(self):
        self.status_var.set("正在深度扫描中，请稍候...")
        self.root.update_idletasks()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        new_list = find_empty_folders(self.paths_str)
        
        if new_list:
            for path in new_list:
                self.tree.insert("", tk.END, values=(path,))
            self.status_var.set(f"扫描完成：发现 {len(new_list)} 个空文件夹")
            first_id = self.tree.get_children()[0]
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)
            return True
        else:
            self.status_var.set("当前扫描范围内已无空文件夹！")
            if not self.is_auto_running: # 如果不是在自动模式中，才弹窗
                messagebox.showinfo("完成", "所有层级的空文件夹已清理干净！")
            return False

    def start_auto_clean(self):
        """一键全自动清理的触发器"""
        if not self.tree.get_children():
            if not self.refresh_list(): return

        confirm = messagebox.askyesno("全自动清理", "程序将自动循环删除所有空文件夹，直到清空为止。\n是否继续？")
        if confirm:
            self.is_auto_running = True
            self.auto_btn.config(state=tk.DISABLED, text="正在自动处理...")
            self.auto_loop()

    def auto_loop(self):
        """全自动清理的递归循环"""
        items = self.tree.get_children()
        if items:
            target_id = items[0]
            folder_path = self.tree.item(target_id, "values")[0]
            try:
                os.rmdir(folder_path)
            except:
                pass
            self.tree.delete(target_id)
            # 使用 after 避免界面卡死，给 UI 刷新时间
            self.root.after(10, self.auto_loop)
        else:
            # 列表空了，重扫
            if self.refresh_list():
                # 重扫后还有，继续跑
                self.root.after(100, self.auto_loop)
            else:
                # 彻底没了
                self.is_auto_running = False
                self.auto_btn.config(state=tk.NORMAL, text="🚀 一键自动清理 (全自动)")
                messagebox.showinfo("全自动任务完成", "已完成所有层级的深度清理！")

    def execute_delete(self, need_confirm):
        selected = self.tree.selection()
        if not selected: 
            self.refresh_list()
            return
        
        target_id = selected[0]
        folder_path = self.tree.item(target_id, "values")[0]

        if need_confirm:
            if not messagebox.askyesno("确认", f"确定删除？\n{folder_path}"): return

        try:
            os.rmdir(folder_path)
            self.tree.delete(target_id)
            
            remaining = self.tree.get_children()
            if remaining:
                next_id = remaining[0]
                self.tree.selection_set(next_id)
                self.tree.focus(next_id)
            else:
                self.refresh_list()
        except Exception:
            self.tree.delete(target_id)
            if not self.tree.get_children(): self.refresh_list()

    def on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            p = self.tree.item(sel[0], "values")[0]
            if os.path.exists(p):
                subprocess.run(['explorer', '/select,', os.path.normpath(p)])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root_temp = tk.Tk()
    root_temp.withdraw()
    init_paths = simpledialog.askstring("初始化", "请输入扫描路径 (如 E:, F:):")
    root_temp.destroy()
    
    if init_paths:
        app = InfiniteCleanerApp(init_paths)
        app.run()