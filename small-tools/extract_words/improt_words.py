from pathlib import Path

# 获取当前文件的绝对路径 (包含文件名)
current_file_path = Path(__file__).resolve()

# 获取当前文件所在的文件夹路径 (不含文件名)
CURRENT_DIR = current_file_path.parent


# 读取一个文件,把每行部为空的内容写进列表中
def process_file(file_path):
    """


    读取指定文件，并返回一个包含所有非空行的列表。

    Args:
        file_path (Path): 要读取的文件的路径。

    Returns:
        list[str]: 包含所有非空行的字符串列表。如果文件不存在，则返回空列表。
    """

    non_empty_lines_list = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                # 检查是否为空的内容
                if line.strip() != "":
                    non_empty_lines_list.append(line)
        return non_empty_lines_list
    except FileNotFoundError:
        print(f"错误: 文件未找到在路径: {file_path}")
        return []


def extract_data_from_list(data_list):
    """
    根据传入的列表数据，分别提取基数元素（索引为0, 2, 4...）和偶数元素（索引为1, 3, 5...），
    并将它们分别写入到当前目录下的指定文件中。

    Args:
        data_list (list[str]): 包含待处理数据的列表。

    Returns:
        tuple: 包含四个列表的元组：[first_data], [second_data], base_elements, even_elements。
    """
    if not data_list:
        return [], [], [], []
    # 剩下的数据
    remaining_data = data_list
    # 基数元素 (从剩下的数据中取基数，即索引为0, 2, 4...的元素)
    base_elements = [remaining_data[i] for i in range(0, len(remaining_data), 2)]
    # 吧这个列表内容写入一个txt文件
    with open(CURRENT_DIR / "base_elements_output.txt", "w", encoding="utf-8") as f:
        for item in base_elements:
            f.write(str(item) + "\n")

    # 偶数元素 (从剩下的数据中取偶数，即索引为1, 3, 5...的元素)
    even_elements = [remaining_data[i] for i in range(1, len(remaining_data), 2)]
    with open(CURRENT_DIR / "even_elements_output.txt", "w", encoding="utf-8") as f:
        for item in even_elements:
            f.write(str(item) + "\n")
    # 返回四个列表变量

    return (
        [data_list[0]],
        [data_list[1]] if len(data_list) > 1 else [],
        base_elements,
        even_elements,
    )


if __name__ == "__main__":
    """
    主执行入口。
    1. 读取 "produce_worlds.txt" 文件，获取所有非空行数据。
    2. 调用 extract_data_from_list 函数，提取基数元素和偶数元素，并写入文件。
    3. 打印提取的结果。
    """
    file_to_process = CURRENT_DIR / "produce_worlds.txt"
    # 由于 process_file 是同步函数，必须使用 asyncio.to_thread 来调用它
    data_list = process_file(file_to_process)
    first_data, second_data, base_elements, even_elements = extract_data_from_list(
        data_list
    )
    print(first_data, second_data, base_elements, even_elements)
