# -*- coding: utf-8 -*-
"""
Bilibili Subtitle Extractor (B站字幕提取器)
------------------------------------------
功能：在本地提取B站视频字幕（支持CC字幕与AI自动生成的字幕）。
输出：
1. 纯对话文本格式 (.txt) - 适合阅读、分析与存档
2. 带时间戳的标准SRT字幕格式 (.srt) - 适合视频剪辑与二次创作
"""

import sys
import os
import re
import requests

def format_time(seconds):
    """将秒数（浮点数）格式化为 SRT 格式的 HH:MM:SS,ms"""
    ms = int((seconds - int(seconds)) * 1000)
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def get_bilibili_subtitles(bvid):
    # 配置标准请求头，模拟浏览器访问，并带上 Referer 防止被B站拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
        "Accept": "application/json, text/plain, */*"
    }
    
    print(f"[*] 正在获取视频 {bvid} 的基本信息...")
    # 步骤一：调用B站官方接口获取视频的 aid, cid 和标题
    view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        res = requests.get(view_url, headers=headers, timeout=10)
        res_json = res.json()
        if res_json.get("code") != 0:
            print(f"[-] 获取视频信息失败: {res_json.get('message')} (错误码: {res_json.get('code')})")
            return
        
        video_data = res_json["data"]
        title = video_data["title"]
        # 清洗文件名中的系统非法字符
        title_clean = re.sub(r'[\\/:*?"<>|]', "_", title)
        cid = video_data["cid"]
        print(f"[+] 视频标题: {title}")
        print(f"[+] 核心CID: {cid}")
    except Exception as e:
        print(f"[-] 请求视频信息时出错: {e}")
        return

    # 步骤二：调用B站播放器接口获取字幕列表
    print("[*] 正在解析字幕列表...")
    player_url = f"https://api.bilibili.com/x/player/v2?cid={cid}&bvid={bvid}"
    try:
        res = requests.get(player_url, headers=headers, timeout=10)
        res_json = res.json()
        if res_json.get("code") != 0:
            print(f"[-] 获取字幕列表失败: {res_json.get('message')}")
            return
        
        subtitle_data = res_json.get("data", {}).get("subtitle", {})
        subtitles = subtitle_data.get("subtitles", [])
        
        if not subtitles:
            print("[-] 该视频未找到任何外挂字幕（CC字幕）或AI自动生成的字幕。")
            print("提示：如果该视频在网页端有字幕，请确认它是否为硬字幕（内嵌烧录在视频画面里的文字）。硬字幕无法通过API提取。")
            return
        
        print(f"[+] 成功找到 {len(subtitles)} 个字幕轨道:")
        for idx, sub in enumerate(subtitles):
            is_ai = "AI生成" if sub.get("ai_type") == 1 else "人工上传"
            print(f"    [{idx}] 语言: {sub['lan_doc']} ({sub['lan']}) | 类型: {is_ai}")
        
        # 默认选择第一个字幕轨道
        choice = 0
        if len(subtitles) > 1:
            try:
                choice_input = input(f"发现多个字幕，请选择要下载的字幕编号 (默认 0): ").strip()
                if choice_input:
                    choice = int(choice_input)
            except ValueError:
                print("[-] 输入无效，默认选择第 0 个字幕")
                choice = 0
                
        if choice < 0 or choice >= len(subtitles):
            print("[-] 编号超出范围，默认选择第 0 个字幕")
            choice = 0
                
        selected_sub = subtitles[choice]
        sub_url = selected_sub["subtitle_url"]
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
            
        # 步骤三：请求字幕的JSON文件并解析内容
        print(f"[*] 正在下载并解析字幕内容...")
        sub_res = requests.get(sub_url, headers=headers, timeout=10)
        sub_json = sub_res.json()
        
        body = sub_json.get("body", [])
        if not body:
            print("[-] 字幕文件内容为空，无法提取。")
            return
        
        # 步骤四：写入本地文件
        txt_filename = f"{title_clean}_纯文本对话.txt"
        srt_filename = f"{title_clean}_带时间戳.srt"
        
        # 1. 写入纯文本（满足您的TXT对话需求）
        with open(txt_filename, "w", encoding="utf-8") as f_txt:
            for item in body:
                content = item["content"].strip()
                if content:
                    f_txt.write(content + "\n")
                
        # 2. 写入标准SRT格式
        with open(srt_filename, "w", encoding="utf-8") as f_srt:
            for idx, item in enumerate(body, 1):
                start_time = format_time(item["from"])
                end_time = format_time(item["to"])
                content = item["content"].strip()
                f_srt.write(f"{idx}\n")
                f_srt.write(f"{start_time} --> {end_time}\n")
                f_srt.write(f"{content}\n\n")
                
        print(f"\n[√] 提取成功！已为您在当前目录下生成两个文件：")
        print(f"    1. 纯文本对话: {os.path.abspath(txt_filename)}")
        print(f"    2. 带时间戳SRT: {os.path.abspath(srt_filename)}")
        
    except Exception as e:
        print(f"[-] 处理字幕时发生异常: {e}")

if __name__ == "__main__":
    print("="*50)
    print("          Bilibili Subtitle Extractor")
    print("="*50)
    
    # 允许直接通过命令行参数传递
    if len(sys.argv) > 1:
        bvid_input = sys.argv[1]
    else:
        bvid_input = input("BV1wKM76rEB7").strip()
    
    # 使用正则表达式精确提取出 BV 号
    bv_match = re.search(r'(BV[a-zA-Z0-9]{10})', bvid_input)
    if bv_match:
        target_bvid = bv_match.group(1)
        get_bilibili_subtitles(target_bvid)
    else:
        print("[-] 未能在输入中识别出有效的BV号，请确认输入格式。")