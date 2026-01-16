# /*** 
#  * 文件名：find_null_folders_delete.py
#  * 功能：扫描指定路径下的文件夹，找出所有空文件夹，并支持删除这些空文件夹。
#  *      支持用户自定义扫描路径。
#  *      结果以图形界面展示，支持双击跳转到对应文件夹位置，并提供删除功能。
#  * 主要步骤：
#  * 1. 获取用户输入的扫描路径。
#  * 2. 遍历指定路径下的所有文件夹，找出空文件夹。
#  * 3. 使用 Tkinter 图形界面展示结果，支持双击跳转到对应文件夹位置，并提供删除功能。
#  * 注意事项：
#  * - 需要处理权限问题，避免因无法访问某些文件夹而导致程序崩溃。
#  * - 界面设计需简洁明了，方便用户查看和操作.
   
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
        for root, dirs, _ in os.walk(drive_path, topdown=False):
            for name in dirs:
                full_path = os.path.join(root, name)
                try:
                    # 如果目录下没有任何东西
                    if not os.listdir(full_path):
                        empty_folders.append(full_path)
                except Exception:
                    continue
    return empty_folders

# --- 2. 界面与交互逻辑 ---
class InfiniteCleanerApp:
    def __init__(self, initial_paths):
        self.root = tk.Tk()
        self.root.title("无限循环空文件夹清理器")
        self.root.geometry("1000x650")
        self.paths_str = initial_paths
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        # 状态栏
        self.status_var = tk.StringVar(value="等待操作...")
        tk.Label(self.root, textvariable=self.status_var, fg="blue", pady=5).pack()

        # 表格
        columns = ("path",)
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("path", text="待清理的空文件夹路径 (若清理完毕将自动重扫)")
        self.tree.column("path", width=900)

        # 布局
        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="top", fill="both", expand=True, padx=10)
        vsb.pack(side="right", fill="y")

        # 按钮区
        btn_frame = tk.Frame(self.root, pady=20)
        btn_frame.pack()

        tk.Button(btn_frame, text="🗑️ 安全删除", bg="#e1e1e1", 
                  command=lambda: self.execute_delete(True), padx=20).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="⚡ 快速清理 (连点模式)", bg="#ffcccc", 
                  command=lambda: self.execute_delete(False), padx=20).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="🔍 手动重新扫描", bg="#d1e7dd", 
                  command=self.refresh_list, padx=20).pack(side=tk.LEFT, padx=10)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_list(self):
        """重新扫描并刷新界面"""
        self.status_var.set("正在深度扫描中，请稍候...")
        self.root.update_idletasks()
        
        # 清空现有表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        new_list = find_empty_folders(self.paths_str)
        
        if new_list:
            for path in new_list:
                self.tree.insert("", tk.END, values=(path,))
            self.status_var.set(f"扫描完成：发现 {len(new_list)} 个空文件夹")
            # 自动选中第一行
            first_id = self.tree.get_children()[0]
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)
        else:
            self.status_var.set("当前扫描范围内已无空文件夹！")
            messagebox.showinfo("完成", "所有层级的空文件夹已清理干净！")

    def execute_delete(self, need_confirm):
        selected = self.tree.selection()
        if not selected: 
            self.refresh_list() # 如果没选中的了，尝试重扫
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
                # 自动跳到下一个
                next_id = remaining[0]
                self.tree.selection_set(next_id)
                self.tree.focus(next_id)
                self.tree.see(next_id)
            else:
                # 【核心改动】：如果列表空了，自动重新扫描
                self.refresh_list()
                
        except Exception as e:
            self.status_var.set(f"删除失败：{folder_path}")
            # 如果是因为非空导致失败，跳过它
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
    # 第一次获取路径
    root_temp = tk.Tk()
    root_temp.withdraw()
    init_paths = simpledialog.askstring("初始化", "请输入扫描路径 (如 E:, F:):")
    root_temp.destroy()
    
    if init_paths:
        app = InfiniteCleanerApp(init_paths)
        app.run()