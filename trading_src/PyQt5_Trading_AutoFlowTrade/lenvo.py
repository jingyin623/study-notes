import threading
import time

import requests
import json
import re

import winsound


def get_sales_number(url):
    # 发送 GET 请求400


    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功

    # 提取 JSONP 中的 JSON 数据
    jsonp_text = response.text
    json_data = re.search(r'jQueryJSONP_stock_getStockInfo\((.*)\)', jsonp_text).group(1)

    # 解析 JSON 数据
    data = json.loads(json_data)

    # 提取 salesNumber 的数值
    if data and isinstance(data, list) and 'salesNumber' in data[0]:
        sales_number = data[0]['salesNumber']
        return sales_number
    else:
        return "无法获取 salesNumber"

def error_beep_one(freq, duration):
    winsound.Beep(freq, duration)
    # for i in range(1) : winsound.Beep(freq, duration)
def error_beep():
    # 创建线程并启动 声音提示线程
    beep_thread = threading.Thread(target=error_beep_one, args=(1000, 2000))
    beep_thread.start()

# if __name__ == '__main__':
#
#     # 示例用法
#     url = 'https://papi.lenovo.com.cn/stock/getStockInfo.jhtm?ss=737&callback=jQueryJSONP_stock_getStockInfo&proInfos=%5B%7BactivityType%3A0%2C+productCode%3A1037657%7D%5D&_=1719453464174'
#     sales_number = get_sales_number(url)
#     print(f"salesNumber: {sales_number}")

if __name__ == '__main__':
    # 示例用法
    while True:
        yesorno = True
        url = input(
            '121')
        if url == '1':
            print('退出程序')
            break
        while yesorno:
            time.sleep(1)
            try:
                sales_number = get_sales_number(url)
                if sales_number != '0':
                    yesorno = False
                    error_beep()
                    print(f"有货salesNumber: {sales_number}")
                print(f"salesNumber: {sales_number}")
            except Exception as e:
                print('网址输入错误')