import os
import json
import random
import shutil
import threading
import pygame

# 初始化 pygame 音频引擎
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "phonetics_data.json")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

DEFAULT_PHONETICS = [
    ("A a", "Tag", "audio/元音/a.mp3", "元音"),
    ("E e", "Tee", "audio/元音/e.mp3", "元音"),
    ("I i", "wie", "audio/元音/i.mp3", "元音"),
]

THEMES = {
    "light": {
        "bg_main": "#f5f6fa",
        "bg_top": "#ebedf0",
        "bg_card": "#ffffff",
        "bg_header": "#e2e8f0",
        "fg_header_text": "#2c3e50",
        "fg_label": "#34495e",
        "sound_fg": "#2c3e50",
        "example_fg": "#7f8c8d",
        "card_border": "#dcdde1",
        "entry_bg": "#ffffff",
        "entry_fg": "#2c3e50",
        "btn_theme_bg": "#34495e",
        "btn_theme_fg": "#ffffff",
        "btn_theme_text": "🌙 夜间模式"
    },
    "dark": {
        "bg_main": "#1e1e2e",
        "bg_top": "#181825",
        "bg_card": "#313244",
        "bg_header": "#45475a",
        "fg_header_text": "#cdd6f4",
        "fg_label": "#cdd6f4",
        "sound_fg": "#89b4fa",
        "example_fg": "#bac2de",
        "card_border": "#585b70",
        "entry_bg": "#313244",
        "entry_fg": "#cdd6f4",
        "btn_theme_bg": "#f9e2af",
        "btn_theme_fg": "#11111b",
        "btn_theme_text": "☀️ 日间模式"
    }
}

class PhoneticsModel:
    def __init__(self):
        self.is_dark_mode = False
        self.delete_mode = False
        self.move_mode = False
        self.is_topmost = False
        self.selected_indices = set()
        
        self.selected_group = "全部分组"
        self.sort_mode = "默认顺序"

        self.win_size, self.card_size, self.phonetics_list = self.load_data()
        self.card_w = self.card_size[0]
        self.card_h = self.card_size[1]

    @property
    def theme(self):
        return THEMES["dark"] if self.is_dark_mode else THEMES["light"]

    def load_data(self):
        default_win_size = [1200, 750]
        default_card_size = [160, 90]
        default_phonetics = list(DEFAULT_PHONETICS)

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        win_size = data.get("window_size", default_win_size)
                        card_size = data.get("card_size", default_card_size)
                        raw_phonetics = data.get("phonetics", default_phonetics)
                        phonetics = []
                        for item in raw_phonetics:
                            if len(item) == 3:
                                phonetics.append((item[0], item[1], item[2], "未分类"))
                            else:
                                phonetics.append(tuple(item))
                        return win_size, card_size, phonetics
            except Exception as e:
                print(f"读取配置失败，使用默认配置: {e}")
        return default_win_size, default_card_size, default_phonetics

    def save_data(self, win_width=None, win_height=None):
        win_size = [win_width, win_height] if win_width and win_height and win_width > 100 and win_height > 100 else self.win_size
        config_data = {
            "window_size": win_size,
            "card_size": [self.card_w, self.card_h],
            "phonetics": self.phonetics_list
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")

    def get_all_groups(self):
        groups = []
        for item in self.phonetics_list:
            grp = item[3] if len(item) > 3 else "未分类"
            if grp not in groups:
                groups.append(grp)
        if "未分类" not in groups:
            groups.append("未分类")
        return groups

    def get_grouped_items(self):
        """按分组和排序规则返回过滤/排序后的数据"""
        all_groups = self.get_all_groups()
        groups_to_show = [self.selected_group] if (self.selected_group != "全部分组" and self.selected_group in all_groups) else all_groups
        
        result = {}
        for group_name in groups_to_show:
            group_items = [(idx, item) for idx, item in enumerate(self.phonetics_list)
                           if (item[3] if len(item) > 3 else "未分类") == group_name]
            if not group_items:
                continue

            if self.sort_mode == "音素 (A-Z)":
                group_items.sort(key=lambda x: x[1][0].lower())
            elif self.sort_mode == "例词 (A-Z)":
                group_items.sort(key=lambda x: x[1][1].lower())
            elif self.sort_mode == "🔀 随机打乱":
                random.shuffle(group_items)

            result[group_name] = group_items
        return result

    def add_card(self, label, word, group, src_file_path):
        group_audio_dir = os.path.join(AUDIO_DIR, group)
        os.makedirs(group_audio_dir, exist_ok=True)

        file_name = os.path.basename(src_file_path)
        dest_file_path = os.path.join(group_audio_dir, file_name)

        if os.path.abspath(src_file_path) != os.path.abspath(dest_file_path):
            shutil.copy2(src_file_path, dest_file_path)

        relative_path = f"audio/{group}/{file_name}"
        self.phonetics_list.append((label, word, relative_path, group))

    def batch_import_files(self, group, selected_paths):
        group_audio_dir = os.path.join(AUDIO_DIR, group)
        os.makedirs(group_audio_dir, exist_ok=True)

        imported_count = 0
        for src_path in selected_paths:
            filename = os.path.basename(src_path)
            stem, ext = os.path.splitext(filename)

            if "_" in stem:
                parts = stem.split("_", 1)
                label = parts[0].strip() or stem
                word = parts[1].strip() or stem
            else:
                label = stem
                word = stem

            dest_filename = filename
            dest_path = os.path.join(group_audio_dir, dest_filename)

            if os.path.abspath(src_path) != os.path.abspath(dest_path):
                counter = 1
                while os.path.exists(dest_path):
                    dest_filename = f"{stem}_{counter}{ext}"
                    dest_path = os.path.join(group_audio_dir, dest_filename)
                    counter += 1

                try:
                    shutil.copy2(src_path, dest_path)
                except Exception as e:
                    print(f"拷贝文件失败 [{src_path}]: {e}")
                    continue

            relative_path = f"audio/{group}/{dest_filename}"
            self.phonetics_list.append((label, word, relative_path, group))
            imported_count += 1
        return imported_count

    def move_selected_cards(self, target_group):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass

        target_audio_dir = os.path.join(AUDIO_DIR, target_group)
        os.makedirs(target_audio_dir, exist_ok=True)

        moved_count = 0
        for idx in self.selected_indices:
            item = self.phonetics_list[idx]
            label, word, old_rel_path, old_group = item[0], item[1], item[2], item[3] if len(item) > 3 else "未分类"

            if old_group == target_group:
                continue

            filename = os.path.basename(old_rel_path)
            old_abs_path = old_rel_path if os.path.isabs(old_rel_path) else os.path.join(BASE_DIR, old_rel_path)

            dest_filename = filename
            target_abs_path = os.path.join(target_audio_dir, dest_filename)

            if os.path.exists(old_abs_path) and os.path.abspath(old_abs_path) != os.path.abspath(target_abs_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(target_abs_path):
                    dest_filename = f"{base}_{counter}{ext}"
                    target_abs_path = os.path.join(target_audio_dir, dest_filename)
                    counter += 1

                try:
                    shutil.move(old_abs_path, target_abs_path)
                except Exception as e:
                    print(f"移动文件失败 [{filename}]: {e}")

            new_rel_path = f"audio/{target_group}/{dest_filename}"
            self.phonetics_list[idx] = (label, word, new_rel_path, target_group)
            moved_count += 1
        return moved_count

    def delete_selected_cards(self):
        for idx in sorted(self.selected_indices, reverse=True):
            del self.phonetics_list[idx]
        self.selected_indices.clear()

    def rename_group(self, old_group_name, new_group_name):
        old_audio_dir = os.path.join(AUDIO_DIR, old_group_name)
        new_audio_dir = os.path.join(AUDIO_DIR, new_group_name)

        if os.path.exists(old_audio_dir):
            try:
                os.makedirs(AUDIO_DIR, exist_ok=True)
                if not os.path.exists(new_audio_dir):
                    os.rename(old_audio_dir, new_audio_dir)
            except Exception as e:
                print(f"重命名音频目录失败: {e}")

        updated_list = []
        for item in self.phonetics_list:
            grp = item[3] if len(item) > 3 else "未分类"
            if grp == old_group_name:
                filename = os.path.basename(item[2])
                new_rel_path = f"audio/{new_group_name}/{filename}"
                updated_list.append((item[0], item[1], new_rel_path, new_group_name))
            else:
                updated_list.append(item)

        self.phonetics_list = updated_list
        if self.selected_group == old_group_name:
            self.selected_group = new_group_name

    def delete_group(self, group_name, action):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass

        src_group_dir = os.path.join(AUDIO_DIR, group_name)

        if action == 'move':
            uncategorized_dir = os.path.join(AUDIO_DIR, "未分类")
            os.makedirs(uncategorized_dir, exist_ok=True)

            updated_list = []
            for item in self.phonetics_list:
                grp = item[3] if len(item) > 3 else "未分类"
                if grp == group_name:
                    old_rel_path = item[2]
                    filename = os.path.basename(old_rel_path)
                    old_abs_path = old_rel_path if os.path.isabs(old_rel_path) else os.path.join(BASE_DIR, old_rel_path)
                    
                    dest_filename = filename
                    if os.path.exists(old_abs_path):
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(uncategorized_dir, dest_filename)):
                            dest_filename = f"{base}_{counter}{ext}"
                            counter += 1
                        
                        target_path = os.path.join(uncategorized_dir, dest_filename)
                        try:
                            shutil.move(old_abs_path, target_path)
                        except Exception as e:
                            print(f"移动音频文件失败 [{filename}]: {e}")

                    new_rel_path = f"audio/未分类/{dest_filename}"
                    updated_list.append((item[0], item[1], new_rel_path, "未分类"))
                else:
                    updated_list.append(item)

            self.phonetics_list = updated_list
            if os.path.exists(src_group_dir):
                shutil.rmtree(src_group_dir, ignore_errors=True)

        elif action == 'delete':
            self.phonetics_list = [
                item for item in self.phonetics_list
                if (item[3] if len(item) > 3 else "未分类") != group_name
            ]
            if os.path.exists(src_group_dir):
                shutil.rmtree(src_group_dir, ignore_errors=True)

        if self.selected_group == group_name:
            self.selected_group = "未分类"

    def play_audio_async(self, mp3_path):
        threading.Thread(target=self._play_mp3, args=(mp3_path,), daemon=True).start()

    def _play_mp3(self, mp3_path):
        full_path = mp3_path if os.path.isabs(mp3_path) else os.path.join(BASE_DIR, mp3_path)
        if os.path.exists(full_path):
            try:
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"播放失败 [{full_path}]: {e}")
        else:
            print(f"未找到音频文件: {full_path}")