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