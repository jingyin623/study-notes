#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 source_dir（可以是 UNC 网络路径）提取一级子文件夹名，
并在 target_dir 下创建同名空文件夹。

示例:
  python make_dirs_specific.py
"""
from pathlib import Path

# ========== 在这里修改为你的路径 ==========
source_dir = Path(r"\\DSM918_MRjiang\Movies\9kg")  # UNC 网络路径
target_dir = Path(r"\\DSM918_MRjiang\Movies\9kg\三级")  # 存放目录
dry_run = False  # True 则仅打印不实际创建
# ==========================================

def create_same_named_dirs(source: Path, target: Path, dry_run: bool=False):
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"源目录不存在或不是目录: {source}")
    # 确保目标目录存在
    target.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    for child in source.iterdir():
        if child.is_dir():
            dest = target / child.name
            if dest.exists():
                skipped.append(dest)
            else:
                if not dry_run:
                    dest.mkdir(parents=True, exist_ok=True)
                created.append(dest)

    return created, skipped

def main():
    try:
        created, skipped = create_same_named_dirs(source_dir, target_dir, dry_run)
    except Exception as e:
        print("发生错误：", e)
        return

    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}")
    print(f"模拟模式 (dry_run): {dry_run}")
    print("已创建：")
    for p in created:
        print("  +", p)
    if not created:
        print("  （无）")
    if skipped:
        print("\n已存在并跳过：")
        for p in skipped:
            print("  -", p)

if __name__ == "__main__":
    main()
