import time
import re
import json
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from http.cookiejar import LWPCookieJar


def get_sales_number(url):
    # 发送 GET 请求
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
        return int(sales_number)
    else:
        return int(0)


class AutoBuyer:
    def __init__(self):
        # 初始化浏览器
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """登录流程"""
        try:
            # 打开登录页面
            self.driver.get('https://reg.lenovo.com.cn/user_auth/toc/#/login')

            # 等待用户手动登录
            input("请手动登录后按回车继续...")
            print("登录成功！")
            return True

        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def send_notification(self):
        """发送推送通知"""
        try:
            push_url = "https://www.pushplus.plus/send?token=7ddbd38f6ccf418da067034e7e950054&title=%E8%81%94%E6%83%B3%E6%8A%A2%E8%B4%AD%E6%88%90%E5%8A%9F&content=%E8%B5%B6%E7%B4%A7%E5%8E%BB%E4%BB%98%E9%92%B1&template=html"
            response = requests.get(push_url)
            if response.status_code == 200:
                print("推送通知发送成功！")
            else:
                print("推送通知发送失败！")
        except Exception as e:
            print(f"推送通知发送失败: {e}")

    def buy_product(self, product_url):
        """执行购买流程"""
        try:
            # 打开商品页面
            self.driver.get(product_url)

            # 等待购买按钮出现并点击
            buy_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#ljgm"))
            )
            buy_button.click()

            # 等待订单页面加载
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".fr.submitBtn"))
            )
            submit_button.click()

            print("抢购成功！")
            # 发送推送通知
            self.send_notification()

        except Exception as e:
            print(f"抢购失败: {e}")

    def run(self, product_url, stock_url):
        """运行抢购程序"""
        try:
            # 每次运行都需要登录
            login_success = self.login()
            if not login_success:
                print("登录失败，程序退出")
                return

            # 持续检查库存
            while True:
                stock = get_sales_number(stock_url)
                print(stock)
                if stock > 0:
                    print(f"检测到库存，开始抢购！当前库存: {stock}")
                    self.buy_product(product_url)
                    break
                time.sleep(0.2)  # 避免请求过于频繁

        finally:
            self.driver.quit()


if __name__ == "__main__":
    # 配置参数
    product_id = "1039473"
    product_url = f"https://item.lenovo.com.cn/product/{product_id}.html"
    stock_url = f"https://papi.lenovo.com.cn/stock/getStockInfo.jhtm?ss=737&callback=jQueryJSONP_stock_getStockInfo&proInfos=%5B%7BactivityType%3A0%2C+productCode%3A{product_id}%7D%5D&_=1719453464174"
    print(product_url, stock_url)
    # 创建抢购实例并运行
    buyer = AutoBuyer()
    buyer.run(product_url, stock_url)

