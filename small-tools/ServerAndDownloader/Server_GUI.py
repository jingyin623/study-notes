import os
import socket
import tkinter as tk
from tkinter import filedialog, messagebox
from flask import Flask, send_from_directory, abort
import threading

app = Flask(__name__)
SELECTED_DIR = ""

# --- 核心逻辑：获取本机局域网 IP ---
def get_host_ip():
    """获取本机局域网 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)) # 模拟连接，不需要真的连通
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(SELECTED_DIR, filename, as_attachment=True)

@app.route('/list/', defaults={'subpath': ''})
@app.route('/list/<path:subpath>')
def list_files(subpath):
    target_path = os.path.join(SELECTED_DIR, subpath)
    if not os.path.isdir(target_path):
        return {"items": []}
    items = []
    for name in os.listdir(target_path):
        is_dir = os.path.isdir(os.path.join(target_path, name))
        items.append({"name": name, "is_dir": is_dir})
    return {"items": items}

def start_server():
    global SELECTED_DIR
    if not SELECTED_DIR:
        messagebox.showerror("错误", "请先选择文件夹！")
        return
    
    # 开启服务后更新界面显示 IP
    try:
        local_ip = get_host_ip()
        lbl_ip_info.config(text=f"服务已启动！\n请在下载端输入 IP: {local_ip}", fg="red", font=("Arial", 12, "bold"))
        btn_start.config(state=tk.DISABLED)
        btn_select.config(state=tk.DISABLED)
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        messagebox.showerror("启动失败", f"无法启动服务: {e}")

def select_folder():
    global SELECTED_DIR
    path = filedialog.askdirectory()
    if path:
        SELECTED_DIR = os.path.normpath(path)
        lbl_path.config(text=f"当前共享目录: {SELECTED_DIR}")
        btn_start.config(state=tk.NORMAL)

# GUI 界面
root = tk.Tk()
root.title("局域网大文件传输-服务端")
root.geometry("450x280")

tk.Label(root, text="第一步：选择要发送的文件夹 (50GB)", font=("微软雅黑", 10)).pack(pady=10)
btn_select = tk.Button(root, text="选择文件夹", command=select_folder, width=15)
btn_select.pack()

lbl_path = tk.Label(root, text="未选择", fg="blue", wraplength=400)
lbl_path.pack(pady=10)

btn_start = tk.Button(root, text="开启服务", state=tk.DISABLED, width=15, bg="lightgreen",
                      command=lambda: threading.Thread(target=start_server, daemon=True).start())
btn_start.pack(pady=5)

# 动态显示 IP 的区域
lbl_ip_info = tk.Label(root, text="等待开启服务...", fg="gray")
lbl_ip_info.pack(pady=20)

tk.Label(root, text="提示：请确保两台电脑连接在同一个路由器下", font=("微软雅黑", 8), fg="gray").pack(side=tk.BOTTOM, pady=5)

root.mainloop()