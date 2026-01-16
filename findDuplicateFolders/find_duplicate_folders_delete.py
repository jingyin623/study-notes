# /***
# - * find_duplicate_folders_delete.py   
# - * 功能：扫描指定路径下的文件夹，找出同名文件夹中包含大量同名文件的情况，并支持删除重复文件。
# - *      支持用户自定义扫描路径和匹配文件个数阈值。
# - *      结果以图形界面展示，支持双击跳转到对应     文件夹位置，并提供删除功能。
# - * 主要步骤：
# - * 1. 获取用户输入的扫描路径和匹配文件个数阈值。
# - * 2. 遍历指定路径下的所有文件夹，构建文件夹名称到路径的映射。
# - * 3. 对同名文件夹进行深度对比，找出包含大量同名文件的文件夹对。
# - * 4. 使用 Tkinter 图形界面展示结果，支持双击跳转到对应文件夹位置，并提供删除功能。
# - * 注意事项：
# - * - 需要处理权限问题，避免因无法访问某些文件夹而导致程序崩溃。
# - * - 界面设计需简洁明了，方便用户查看和操作.   
# ***/


import os
import subprocess
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --- 1. 获取用户配置 ---
def get_user_config():
    temp_root = tk.Tk()
    temp_root.withdraw()
    paths_input = simpledialog.askstring("第一步：设置路径", "请输入扫描路径 (如 E:, F:)\n多个路径请用逗号隔开:", parent=temp_root)
    if not paths_input:
        temp_root.destroy()
        return None, None
    threshold_input = simpledialog.askinteger("第二步：设置过滤条件", "最少包含多少个同名文件才判定为重复？", initialvalue=3, minvalue=1, parent=temp_root)
    temp_root.destroy()
    return paths_input, threshold_input

# --- 2. 深度对比逻辑 ---
def find_deep_duplicates(raw_input, threshold):
    if not raw_input or threshold is None: return None
    paths = [p.strip() for p in raw_input.replace('，', ',').split(',') if p.strip()]
    folder_map = defaultdict(list)
    for p in paths:
        drive_path = p + '\\' if (p.endswith(':') and len(p) == 2) else p
        for root, dirs, _ in os.walk(drive_path):
            for name in dirs:
                full_path = os.path.join(root, name)
                folder_map[name].append(full_path)
    
    deep_results = []
    for folder_name, locations in folder_map.items():
        if len(locations) < 2: continue
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                path1, path2 = locations[i], locations[j]
                try:
                    files1 = {f for f in os.listdir(path1) if os.path.isfile(os.path.join(path1, f))}
                    files2 = {f for f in os.listdir(path2) if os.path.isfile(os.path.join(path2, f))}
                    common_files = files1.intersection(files2)
                    if len(common_files) >= threshold:
                        deep_results.append({"name": folder_name, "path1": path1, "path2": path2, "count": len(common_files), "common_files": list(common_files)})
                except Exception: continue
    return deep_results

# --- 3. 结果展示与交互窗口 ---
class CleanerApp:
    def __init__(self, data, threshold):
        self.root = tk.Tk()
        self.root.title(f"高效文件清理专家 (阈值: {threshold})")
        self.root.geometry("1100x700")
        self.data = data
        self.item_map = {}
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="操作指南：双击路径跳转 | 选中主行后点击下方按钮 | 清理后自动跳到下一组", fg="#555", pady=5).pack()

        # 表格
        columns = ("name", "match_count", "path")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="文件夹名")
        self.tree.heading("match_count", text="匹配文件数")
        self.tree.heading("path", text="完整路径 (双击跳转)")
        self.tree.column("name", width=150)
        self.tree.column("match_count", width=100, anchor="center")
        self.tree.column("path", width=800)

        for idx, item in enumerate(self.data):
            row_id = self.tree.insert("", tk.END, values=(item["name"], item["count"], item["path1"]))
            self.tree.insert("", tk.END, values=("", "└─ 待清理内容 ─>", item["path2"]))
            self.item_map[row_id] = item

        # 绑定事件
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # 布局
        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="top", fill="both", expand=True, padx=10)
        vsb.pack(side="right", fill="y")

        # 按钮区
        btn_frame = tk.Frame(self.root, pady=20)
        btn_frame.pack()

        tk.Button(btn_frame, text="🗑️ 安全删除 (需确认)", bg="#e1e1e1", command=lambda: self.execute_delete(True), padx=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="⚡ 快速清理 (无提示)", bg="#ffcc99", command=lambda: self.execute_delete(False), padx=15).pack(side=tk.LEFT, padx=10)

    def execute_delete(self, need_confirm):
        selected = self.tree.selection()
        if not selected: return
        
        # 确保选中的是父节点（有数据的行）
        current_id = selected[0]
        if current_id not in self.item_map:
            messagebox.showwarning("提示", "请选中包含文件夹名称的主行")
            return

        target_item = self.item_map[current_id]
        
        if need_confirm:
            if not messagebox.askyesno("确认", f"确定清理: {target_item['path2']} ?"): return

        # 执行删除
        done = 0
        for f in target_item['common_files']:
            p = os.path.join(target_item['path2'], f)
            try:
                if os.path.exists(p): os.remove(p); done += 1
            except: pass

        # 自动选中逻辑
        all_items = self.tree.get_children()
        idx = all_items.index(current_id)
        
        # 移除已处理的这组（父行和子提示行）
        self.tree.delete(all_items[idx+1]) # 删除提示行
        self.tree.delete(current_id)       # 删除主行
        
        # 挑选下一个
        remaining = self.tree.get_children()
        if remaining:
            # 如果删掉的是最后一个，就选新的最后一个，否则选当前位置的项
            next_idx = idx if idx < len(remaining) else len(remaining) - 1
            next_id = remaining[next_idx]
            
            # 如果刚好落在了子提示行上，再往上/下拨一位，确保选中主行
            if next_id not in self.item_map:
                if next_idx + 1 < len(remaining):
                    next_id = remaining[next_idx + 1]
                else:
                    next_id = remaining[next_idx - 1]
            
            self.tree.selection_set(next_id)
            self.tree.focus(next_id)
            self.tree.see(next_id)
        else:
            messagebox.showinfo("完成", "所有项目已处理完毕！")

    def on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            p = self.tree.item(sel[0], "values")[2]
            if p and os.path.exists(os.path.normpath(p)):
                subprocess.run(['explorer', '/select,', os.path.normpath(p)])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    target_paths, user_threshold = get_user_config()
    if target_paths and user_threshold:
        results = find_deep_duplicates(target_paths, user_threshold)
        if results:
            app = CleanerApp(results, user_threshold)
            app.run()
        else:
            messagebox.showinfo("完成", "未发现重复项。")