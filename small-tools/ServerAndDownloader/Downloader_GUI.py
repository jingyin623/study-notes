import os
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

def start_download():
    ip = ent_ip.get()
    save_path = lbl_save_path.cget("text").replace("保存位置: ", "")
    
    if not ip or "未选择" in save_path:
        messagebox.showerror("错误", "请填写完整信息！")
        return

    btn_dl.config(state=tk.DISABLED)
    threading.Thread(target=sync_folder, args=(ip, "", save_path), daemon=True).start()

def sync_folder(ip, remote_subpath, local_root):
    base_url = f"http://{ip}:5000"
    try:
        list_url = f"{base_url}/list/{remote_subpath}"
        data = requests.get(list_url, timeout=5).json()
    except Exception as e:
        lbl_status.config(text=f"连接失败: {e}")
        return

    for item in data.get('items', []):
        rel_path = os.path.join(remote_subpath, item['name']).replace("\\", "/")
        if item['is_dir']:
            sync_folder(ip, rel_path, local_root)
        else:
            download_file(base_url, rel_path, local_root)
    
    lbl_status.config(text="全部下载完成！")

def download_file(base_url, rel_path, local_root):
    url = f"{base_url}/download/{rel_path}"
    local_file_path = os.path.join(local_root, rel_path)
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

    headers = {}
    if os.path.exists(local_file_path):
        headers['Range'] = f"bytes={os.path.getsize(local_file_path)}-"

    try:
        with requests.get(url, headers=headers, stream=True, timeout=10) as r:
            if r.status_code == 416: return # 已完成
            mode = 'ab' if r.status_code == 206 else 'wb'
            
            lbl_status.config(text=f"正在传输: {rel_path}")
            with open(local_file_path, mode) as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk: f.write(chunk)
    except:
        print(f"下载 {rel_path} 出错，稍后可重新运行续传")

def select_save_dir():
    path = filedialog.askdirectory()
    if path: lbl_save_path.config(text=f"保存位置: {path}")

# GUI 界面
root = tk.Tk()
root.title("局域网大文件传输-下载端")
root.geometry("450x300")

tk.Label(root, text="1. 输入服务端 IP (Win10的IP):").pack(pady=5)
ent_ip = tk.Entry(root)
ent_ip.insert(0, "192.168.1.X")
ent_ip.pack()

tk.Label(root, text="2. 选择本地保存位置:").pack(pady=5)
btn_path = tk.Button(root, text="浏览", command=select_save_dir)
btn_path.pack()
lbl_save_path = tk.Label(root, text="保存位置: 未选择", fg="green")
lbl_save_path.pack()

btn_dl = tk.Button(root, text="开始同步 (支持续传)", command=start_download, bg="orange")
btn_dl.pack(pady=20)

lbl_status = tk.Label(root, text="等待开始...", wraplength=400)
lbl_status.pack()

root.mainloop()