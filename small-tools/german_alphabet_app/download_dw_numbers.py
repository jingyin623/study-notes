#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DW Learn German 数字 MP3 批量下载脚本
功能：
1. 下载 0~12 的德语发音 MP3
2. 用户交互选择保存目录
3. 自动重命名为「数字_读音.mp3」格式（例：0_null.mp3）
4. 支持断点续传判断（已存在则跳过）
5. 简单进度与错误提示
依赖：仅标准库 + requests（pip install requests）
"""

import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装 requests：pip install requests")
    sys.exit(1)

# 数字 → 德语读音 映射（与官网文件名一致）
NUMBER_MAP = {
    0: "null",
    1: "eins",
    2: "zwei",
    3: "drei",
    4: "vier",
    5: "fuenf",      # fünf
    6: "sechs",
    7: "sieben",
    8: "acht",
    9: "neun",
    10: "zehn",
    11: "elf",
    12: "zwoelf",    # zwölf
}

BASE_URL = "https://radiodownloaddw-a.akamaihd.net/Events/dwelle/deutschkurse/abc/ABC_{}.mp3"


def get_save_dir() -> Path:
    """交互获取保存目录，不存在则创建"""
    default = Path.cwd() / "dw_numbers_mp3"
    user_input = input(f"请输入保存目录（直接回车使用默认：{default}）:\n> ").strip()
    save_dir = Path(user_input) if user_input else default
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def download_file(url: str, dest: Path) -> bool:
    """下载单个文件，已存在则跳过"""
    if dest.exists():
        print(f"  [跳过] 已存在 → {dest.name}")
        return True
    try:
        resp = requests.get(url, timeout=15, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  [完成] {dest.name}")
        return True
    except Exception as e:
        print(f"  [失败] {dest.name} → {e}")
        return False


def main():
    print("=" * 50)
    print("DW 数字发音 MP3 下载工具 (0~12)")
    print("=" * 50)

    save_dir = get_save_dir()
    print(f"\n保存目录：{save_dir.resolve()}\n")

    success, fail = 0, 0
    for num, pronunciation in NUMBER_MAP.items():
        url = BASE_URL.format(pronunciation)
        filename = f"{num}_{pronunciation}.mp3"
        dest = save_dir / filename
        print(f"下载 {num} ({pronunciation}) ...")
        if download_file(url, dest):
            success += 1
        else:
            fail += 1

    print("\n" + "=" * 50)
    print(f"完成：成功 {success} 个，失败 {fail} 个")
    print(f"文件位置：{save_dir.resolve()}")
    print("=" * 50)


if __name__ == "__main__":
    main()