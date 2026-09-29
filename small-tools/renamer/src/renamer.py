import argparse
import os


def normalize_ext(ext: str) -> str:
    """确保后缀名以点号 . 开头，且为小写"""
    ext = ext.strip()
    if not ext.startswith("."):
        ext = "." + ext
    return ext.lower()


def batch_change_extension(
    dir_path: str, old_ext: str, new_ext: str, dry_run: bool = False
) -> int:
    """批量修改指定目录下文件的后缀名"""
    if not os.path.isdir(dir_path):
        raise ValueError(f"指定路径不存在或不是目录: {dir_path}")

    old_ext = normalize_ext(old_ext)
    new_ext = normalize_ext(new_ext)

    changed_count = 0

    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)

        # 只处理文件，忽略文件夹
        if not os.path.isfile(file_path):
            continue

        name, ext = os.path.splitext(filename)

        if ext.lower() == old_ext:
            new_filename = name + new_ext
            new_file_path = os.path.join(dir_path, new_filename)

            if not dry_run:
                os.rename(file_path, new_file_path)

            changed_count += 1

    return changed_count

# 在 renamer.py 末尾追加 CLI 交互逻辑

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量修改文件后缀名小工具")
    # 这里保持 "path"，不要改写成具体的 Windows 路径
    parser.add_argument("path", help="目标文件夹路径")
    parser.add_argument("old_ext", help="原后缀名 (例如: txt)")
    parser.add_argument("new_ext", help="新后缀名 (例如: md)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览将要修改的文件，不执行真正改名",
    )

    args = parser.parse_args()
    # ...后续代码保持不变

    args = parser.parse_args()

    mode_str = "[预览模式]" if args.dry_run else "[实际执行]"
    print(f"--> 开始运行 {mode_str}")

    try:
        count = batch_change_extension(
            dir_path=args.path,
            old_ext=args.old_ext,
            new_ext=args.new_ext,
            dry_run=args.dry_run,
        )
        print(f"成功处理 {count} 个文件！")
    except Exception as e:
        print(f"出现错误: {e}")