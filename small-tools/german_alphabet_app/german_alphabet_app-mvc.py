import tkinter as tk
from tkinter import messagebox
from model import PhoneticsModel
from view import PhoneticsView

class PhoneticsController:
    def __init__(self, root):
        self.root = root
        self.model = PhoneticsModel()
        self.view = PhoneticsView(root, self)
        
        # 恢复上次保存的窗口尺寸
        self.root.geometry(f"{max(self.model.win_size[0], 1050)}x{max(self.model.win_size[1], 420)}")
        self.view.card_w_var.set(self.model.card_w)
        self.view.card_h_var.set(self.model.card_h)

        # 绑定 UI 事件处理函数
        self.view.bind_events()

        # 首次加载 UI 视图
        self.refresh_ui()

    def refresh_ui(self):
        groups = self.model.get_all_groups()
        self.view.update_groups_combobox(groups, self.model.selected_group)
        self.view.update_theme(self.model.theme, self.model.is_dark_mode)
        self.view.update_mode_buttons(
            self.model.move_mode, 
            self.model.delete_mode, 
            self.model.is_topmost, 
            len(self.model.selected_indices)
        )
        self.view.render_all_cards()

    def toggle_theme(self):
        self.model.is_dark_mode = not self.model.is_dark_mode
        self.refresh_ui()

    def toggle_topmost(self):
        self.model.is_topmost = not self.model.is_topmost
        self.root.attributes("-topmost", self.model.is_topmost)
        self.view.update_mode_buttons(
            self.model.move_mode, 
            self.model.delete_mode, 
            self.model.is_topmost, 
            len(self.model.selected_indices)
        )

    def toggle_delete_mode(self):
        if self.model.move_mode:
            self.model.move_mode = False
        self.model.delete_mode = not self.model.delete_mode
        self.model.selected_indices.clear()
        self.refresh_ui()

    def toggle_move_mode(self):
        if self.model.delete_mode:
            self.model.delete_mode = False
        self.model.move_mode = not self.model.move_mode
        self.model.selected_indices.clear()
        self.refresh_ui()

    def on_group_filter_changed(self, group_name):
        self.model.selected_group = group_name
        self.view.render_all_cards()

    def on_sort_changed(self, sort_mode):
        self.model.sort_mode = sort_mode
        self.view.render_all_cards()

    def on_size_changed(self, width, height):
        self.model.card_w = width
        self.model.card_h = height
        self.view.render_all_cards()

    def on_card_clicked(self, orig_idx, mp3_path):
        if self.model.delete_mode or self.model.move_mode:
            if orig_idx in self.model.selected_indices:
                self.model.selected_indices.remove(orig_idx)
            else:
                self.model.selected_indices.add(orig_idx)
            self.view.update_mode_buttons(
                self.model.move_mode, 
                self.model.delete_mode, 
                self.model.is_topmost, 
                len(self.model.selected_indices)
            )
            self.view.render_all_cards()
        else:
            self.model.play_audio_async(mp3_path)

    def add_card(self, label, word, group, src_file_path):
        try:
            self.model.add_card(label, word, group, src_file_path)
            self.model.save_data()
            self.refresh_ui()
        except Exception as e:
            messagebox.showerror("错误", f"添加发音卡片失败: {e}", parent=self.root)

    def batch_import_files(self, group, selected_paths):
        count = self.model.batch_import_files(group, selected_paths)
        self.model.save_data()
        self.refresh_ui()
        return count

    def move_selected(self, target_group):
        count = self.model.move_selected_cards(target_group)
        self.model.save_data()
        self.model.move_mode = False
        self.model.selected_indices.clear()
        self.refresh_ui()
        return count

    def confirm_delete(self):
        if not self.model.selected_indices:
            messagebox.showinfo("提示", "未选中任何卡片！", parent=self.root)
            return

        if messagebox.askyesno("确认删除", f"确定要永久删除选中的 {len(self.model.selected_indices)} 个发音卡片吗？", parent=self.root):
            self.model.delete_selected_cards()
            self.model.save_data()
            self.model.delete_mode = False
            self.refresh_ui()

    def rename_group(self, old_name, new_name):
        self.model.rename_group(old_name, new_name)
        self.model.save_data()
        self.refresh_ui()

    def delete_group(self, group_name, action):
        self.model.delete_group(group_name, action)
        self.model.save_data()
        self.refresh_ui()

    def on_closing(self):
        self.model.save_data(self.root.winfo_width(), self.root.winfo_height())
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneticsController(root)
    root.mainloop()