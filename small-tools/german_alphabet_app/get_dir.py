#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 Nginx sites-enabled 清理与重建命令
运行后输入目录路径即可
"""

from pathlib import Path

def main():
    path_str = input("请输入文件夹路径: ").strip()
    
    if not path_str:
        print("错误: 路径不能为空")
        return

    target_dir = Path(path_str)

    if not target_dir.is_dir():
        print(f"错误: 目录不存在 → {target_dir}")
        return

    # 只取普通文件，按名字排序
    files = sorted([f.name for f in target_dir.iterdir() if f.is_file()])

    if not files:
        print("目录下没有文件")
        return

    print("\n# ===== 1. 删除旧软链接 =====")
    for name in files:
        print(f"sudo rm /etc/nginx/sites-enabled/{name}")

    print("\n# ===== 2. 重新创建软链接 =====")
    for name in files:
        print(f"sudo ln -s /etc/nginx/sites-available/{name} /etc/nginx/sites-enabled/{name}")

if __name__ == "__main__":
    main()