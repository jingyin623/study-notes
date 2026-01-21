"""
Docstring for small-tools.download.download
使用 yt-dlp 下载 YouTube 视频及其双语字幕
功能：
1. 从指定的 YouTube 视频链接下载视频文件
2. 抓取自动生成的英文和简体中文字幕，并转换为常见的 SRT 格式
3. 支持使用 cookies 文件以处理需要登录才能访问的视频
使用方法：
1. 确保已安装 yt-dlp，并将其添加到系统 PATH 中
2. 准备好包含登录信息的 cookies 文件（例如从浏览器导出的 cookies）
3. 运行脚本，视频链接和 cookies 文件路径可在代码中修改
"""
import os

COOKIE_FILE = "youtube.com_cookies.txt" 
urls = ["https://www.youtube.com/watch?v=k9TUPpGqYTo"]

for url in urls:
    print(f"🚀 正在下载视频并抓取双语字幕: {url}")
    # --write-auto-subs: 下载自动生成的字幕
    # --sub-lang "en,zh-Hans": 尝试下载英文和简体中文
    # --convert-subs "srt": 转换成最常见的字幕格式
    os.system(f'yt-dlp -f "bestvideo[height<=480]+bestaudio/best" --cookies {COOKIE_FILE} --write-auto-subs --sub-lang "en,zh-Hans" --convert-subs "srt" {url}')

print("✅ 下载完成！请在文件夹里找同名的 .srt 文件。")