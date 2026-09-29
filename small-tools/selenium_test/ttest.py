def bubble_sort(arr):
    # 冒泡法的实现
    n = len(arr)
    print(f"原始数组: {arr}")
    swapped = True

    # 外层循环，保证效率，如果一趟中没有元素交换，则退出
    while swapped:
        swapped = False
        # 内层循环，进行相邻元素的比较和交换
        for i in range(0, len(arr) - 1):
            # 比较 i 和 i+1
            if arr[i] > arr[i+1]:
                # 交换 arr[i] 和 arr[i+1]
                arr[i], arr[i+1] = arr[i+1], arr[i]
                swapped = True
        # 可选：在某些情况下，每完成一趟可以打印一次状态
        # print(f"经过一趟后数组状态: {arr}")

    print(f"排序完成的数组: {arr}")
    return arr

# 添加测试方法
def add_test_methods():
    print("\n==================================================")
    print("          添加测试方法执行区开始 (Add Test Methods) ")
    print("==================================================")
    
    # 测试用例 1: 随机顺序
    test_case_1 = [9, 3, 7, 1]
    print("\n--- 测试用例 1: 随机顺序 [9, 3, 7, 1] ---")
    test_arr_1 = list(test_case_1) # 复制列表以保持原测试用例的完整性
    bubble_sort(test_arr_1)

    # 测试用例 2: 已排序顺序 (性能测试)
    test_case_2 = [1, 2, 3, 4]
    print("\n--- 测试用例 2: 已排序顺序 [1, 2, 3, 4] ---")
    test_arr_2 = list(test_case_2)
    bubble_sort(test_arr_2)

    # 测试用例 3: 完全逆序 (最耗时测试)
    test_case_3 = [5, 4, 3, 2, 1]
    print("\n--- 测试用例 3: 完全逆序 [5, 4, 3, 2, 1] ---")
    test_arr_3 = list(test_case_3)
    bubble_sort(test_arr_3)

    # 测试用例 4: 包含重复元素
    test_case_4 = [5, 3, 5, 1]
    print("\n--- 测试用例 4: 包含重复元素 [5, 3, 5, 1] ---")
    test_arr_4 = list(test_case_4)
    bubble_sort(test_arr_4)

    print("\n==================================================")
    print("          添加测试方法执行区结束 (Add Test Methods) ")
    print("==================================================")

if __name__ == "__main__":
    add_test_methods()
