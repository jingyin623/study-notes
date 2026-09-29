import os
import re
from bs4 import BeautifulSoup

def batch_rename_mp3_from_html(html_file_path, mp3_folder_path):
    """
    根据 HTML 内容提取 音素_例词 与 MP3 原文件名的对应关系，并重命名文件夹下的文件。
    """
    if not os.path.exists(html_file_path):
        print(f"❌ 未找到 HTML 文件: {html_file_path}")
        return

    if not os.path.exists(mp3_folder_path):
        print(f"❌ 未找到 MP3 文件夹: {mp3_folder_path}")
        return

    # 读取 HTML 文件内容
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # 查找页面中所有的 <audio> 标签或 <source> 标签
    sources = soup.find_all('source')
    
    renamed_count = 0
    skipped_count = 0

    for source in sources:
        src_url = source.get('src', '')
        if not src_url.lower().endswith('.mp3'):
            continue

        # 从 URL 中提取原 MP3 文件名（如 10_02_AE.mp3）
        old_filename = os.path.basename(src_url)

        # 向上查找/前后查找对应的 <h2> (音素) 与 <p> (例词)
        # 1. 查找音素 <h2>
        h2_tag = source.find_previous('h2')
        # 2. 查找例词 <p>
        p_tag = source.find_next('p')

        if not h2_tag or not p_tag:
            print(f"⚠️ 无法匹配 HTML 中的元数据: {old_filename}")
            continue

        phoneme = h2_tag.get_text(strip=True)  # 例如 "Ä, ä"
        word = p_tag.get_text(strip=True)        # 例如 "Äpfel"

        # 拼接目标文件名："音素_例词.mp3" -> "Ä, ä_Äpfel.mp3"
        new_filename = f"{phoneme}_{word}.mp3"

        # 清理操作系统文件名禁止的特殊字符 (\ / : * ? " < > |)
        new_filename = re.sub(r'[\\/:*?"<>|]', '_', new_filename)

        # 拼装绝对路径
        old_filepath = os.path.join(mp3_folder_path, old_filename)
        new_filepath = os.path.join(mp3_folder_path, new_filename)

        # 执行重命名
        if os.path.exists(old_filepath):
            try:
                os.rename(old_filepath, new_filepath)
                print(f"✅ 重命名成功: [{old_filename}]  -->  [{new_filename}]")
                renamed_count += 1
            except Exception as e:
                print(f"❌ 重命名失败 [{old_filename}]: {e}")
        else:
            print(f"🔍 文件夹中未找到原文件: {old_filename}")
            skipped_count += 1

    print(f"\n处理完成！成功重命名 {renamed_count} 个文件，跳过 {skipped_count} 个文件。")


if __name__ == "__main__":
    # 填入你的 HTML 文件绝对或相对路径
    HTML_FILE = "C:\\Users\\jingy\\Desktop\\字母 _ Ü ü.html"
    
    # 填入存放 MP3 文件的文件夹路径
    MP3_FOLDER = "D:\\workspace\\study-notes\\small-tools\\german_alphabet_app\\dw_audio_files copy"

    batch_rename_mp3_from_html(HTML_FILE, MP3_FOLDER)