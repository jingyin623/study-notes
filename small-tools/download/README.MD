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