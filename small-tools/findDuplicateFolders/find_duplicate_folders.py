"""
Docstring for small-tools.findDuplicateFolders.find_duplicate_folders
 * 功能：扫描指定路径下的文件夹，找出同名文件夹中包含大量同名文件的情况。
 *      支持用户自定义扫描路径和匹配文件个数阈值。
 *      结果以图形界面展示，支持双击跳转到对应文件夹位置。
 * 
 * 主要步骤：
 * 1. 获取用户输入的扫描路径和匹配文件个数阈值。
 * 2. 遍历指定路径下的所有文件夹，构建文件夹名称到路径的映射。
 * 3. 对同名文件夹进行深度对比，找出包含大量同名文件的文件夹对。
 * 4. 使用 Tkinter 图形界面展示结果，支持双击跳转到对应文件夹位置。
 * 
 * 注意事项：
 * - 需要处理权限问题，避免因无法访问某些文件夹而导致程序崩溃。
 * - 界面设计需简洁明了，方便用户查看和操作。
"""

import os
import subprocess
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# --- 1. 获取用户输入（路径和阈值） ---
def get_user_config():
    temp_root = tk.Tk()
    temp_root.withdraw()
    
    # 获取扫描路径
    paths_input = simpledialog.askstring(
        "第一步：设置路径", 
        "请输入扫描路径 (如 E:, F:)\n多个路径请用逗号隔开:",
        parent=temp_root
    )
    
    if not paths_input:
        temp_root.destroy()
        return None, None

    # 获取匹配文件个数阈值
    threshold_input = simpledialog.askinteger(
        "第二步：设置过滤条件", 
        "同名文件夹内，最少包含多少个同名文件？",
        initialvalue=3,
        minvalue=1,
        parent=temp_root
    )
    
    temp_root.destroy()
    return paths_input, threshold_input

# --- 2. 深度对比逻辑 ---
def find_deep_duplicates(raw_input, threshold):
    if not raw_input or threshold is None:
        return None
    
    paths = [p.strip() for p in raw_input.replace('，', ',').split(',') if p.strip()]
    folder_map = defaultdict(list)
    
    # 扫描文件夹
    for p in paths:
        drive_path = p + '\\' if (p.endswith(':') and len(p) == 2) else p
        for root, dirs, _ in os.walk(drive_path):
            for name in dirs:
                full_path = os.path.join(root, name)
                folder_map[name].append(full_path)
    
    deep_results = []

    # 深度对比
    for folder_name, locations in folder_map.items():
        if len(locations) < 2:
            continue
            
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                path1 = locations[i]
                path2 = locations[j]
                
                try:
                    # 只对比当前文件夹下的文件，不递归子文件夹
                    files1 = {f for f in os.listdir(path1) if os.path.isfile(os.path.join(path1, f))}
                    files2 = {f for f in os.listdir(path2) if os.path.isfile(os.path.join(path2, f))}
                    
                    common_files = files1.intersection(files2)
                    
                    # 使用用户输入的 threshold 替代写死的 3
                    if len(common_files) >= threshold:
                        deep_results.append({
                            "name": folder_name,
                            "path1": path1,
                            "path2": path2,
                            "count": len(common_files)
                        })
                except PermissionError:
                    continue

    return deep_results

# --- 3. 跳转逻辑 ---
def open_folder(path):
    path = os.path.normpath(path)
    if os.path.exists(path):
        subprocess.run(['explorer', '/select,', path])
    else:
        messagebox.showerror("错误", "路径已不存在")

# --- 4. 结果展示窗口 ---
def show_results_gui(data, threshold):
    root = tk.Tk()
    root.title(f"深度扫描结果 (阈值: {threshold}个同名文件)")
    root.geometry("1000x600")

    columns = ("name", "match_count", "path")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    tree.heading("name", text="文件夹名")
    tree.heading("match_count", text="匹配文件数")
    tree.heading("path", text="完整路径 (双击跳转)")
    
    tree.column("name", width=150)
    tree.column("match_count", width=100, anchor="center")
    tree.column("path", width=700)

    for item in data:
        # 第一行显示主要信息
        tree.insert("", tk.END, values=(item["name"], item["count"], item["path1"]), tags=('group',))
        # 第二行显示对照路径
        tree.insert("", tk.END, values=("", "", item["path2"]), tags=('group',))

    tree.tag_configure('group', background='#ffffff')

    def on_click(event):
        selected = tree.selection()
        if selected:
            path = tree.item(selected[0], "values")[2]
            if path: open_folder(path)

    tree.bind("<Double-1>", on_click)
    
    vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    
    root.mainloop()

# --- 主程序 ---
if __name__ == "__main__":
    target_paths, user_threshold = get_user_config()
    if target_paths and user_threshold:
        results = find_deep_duplicates(target_paths, user_threshold)
        if results:
            show_results_gui(results, user_threshold)
        else:
            messagebox.showinfo("完成", f"未发现同名文件数 >= {user_threshold} 的同名文件夹。")