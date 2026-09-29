#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票振幅监控程序
基于富途API实现，监控指定股票的振幅，当一小时振幅小于2%时发出声音提示
"""

import json
import time
import threading
import winsound
import requests
from futu import *
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class StockAmplitudeMonitor:
    def __init__(self):
        self.stock_codes = []
        self.price_history = {}
        self.monitoring = False
        self.amplitude_threshold = 0.02  # 2%
        self.time_interval = 60  # 检查间隔(秒)

        # 富途API配置 (需要根据实际情况修改)
        self.futu_host = "https://openapi.futunn.com"
        self.api_key = "YOUR_API_KEY"  # 需要替换为实际的API密钥
        self.access_token = "YOUR_ACCESS_TOKEN"  # 需要替换为实际的访问令牌

    def get_stock_price(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票实时价格
        使用富途API获取股票价格信息
        """
        try:
            # 构建API请求URL
            url = f"{self.futu_host}/openapi/quote/v1/realtime"

            # 请求参数
            params = {
                "symbol": stock_code,
                "fields": "last_price,open_price,high_price,low_price,volume,timestamp"
            }

            # 请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "X-Api-Key": self.api_key
            }

            # 发送请求
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return data.get("data")
                else:
                    print(f"API错误: {data.get('msg')}")
            else:
                print(f"HTTP错误: {response.status_code}")

        except Exception as e:
            print(f"获取股票价格失败: {e}")

        return None

    def calculate_amplitude(self, stock_code: str) -> Optional[float]:
        """
        计算股票一小时的振幅
        振幅 = (最高价 - 最低价) / 开盘价 * 100%
        """
        if stock_code not in self.price_history:
            return None

        history = self.price_history[stock_code]
        if len(history) < 2:
            return None

        # 获取一小时内的数据
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_data = [p for p in history if p['time'] >= one_hour_ago]

        if len(recent_data) < 2:
            return None

        high_price = max(p['high'] for p in recent_data)
        low_price = min(p['low'] for p in recent_data)
        open_price = recent_data[0]['open']

        if open_price == 0:
            return None

        amplitude = (high_price - low_price) / open_price
        return amplitude

    def play_alert_sound(self):
        """播放提醒声音"""
        try:
            # Windows系统播放声音
            for _ in range(3):  # 连续播放3次
                winsound.Beep(1000, 500)  # 1000Hz, 500ms
                time.sleep(0.5)
        except:
            print("声音提醒失败，请检查系统声音设置")

    def monitor_stock(self, stock_code: str):
        """监控单个股票"""
        print(f"开始监控股票: {stock_code}")

        while self.monitoring:
            try:
                # 获取股票价格
                price_data = self.get_stock_price(stock_code)

                if price_data:
                    # 更新价格历史
                    current_time = datetime.now()
                    price_record = {
                        'time': current_time,
                        'open': price_data.get('open_price', 0),
                        'high': price_data.get('high_price', 0),
                        'low': price_data.get('low_price', 0),
                        'last': price_data.get('last_price', 0)
                    }

                    if stock_code not in self.price_history:
                        self.price_history[stock_code] = []

                    self.price_history[stock_code].append(price_record)

                    # 保留最近2小时的数据
                    two_hours_ago = current_time - timedelta(hours=2)
                    self.price_history[stock_code] = [
                        p for p in self.price_history[stock_code]
                        if p['time'] >= two_hours_ago
                    ]

                    # 计算振幅
                    amplitude = self.calculate_amplitude(stock_code)

                    if amplitude is not None:
                        amplitude_percent = amplitude * 100
                        current_price = price_data.get('last_price', 0)

                        print(f"[{current_time.strftime('%H:%M:%S')}] {stock_code}: "
                              f"当前价 {current_price:.3f}, 一小时振幅 {amplitude_percent:.2f}%")

                        # 检查是否低于阈值
                        if amplitude < self.amplitude_threshold:
                            alert_msg = f"⚠️ {stock_code} 振幅过低! 一小时振幅: {amplitude_percent:.2f}%"
                            print(alert_msg)
                            self.play_alert_sound()

                time.sleep(self.time_interval)

            except KeyboardInterrupt:
                print(f"停止监控股票: {stock_code}")
                break
            except Exception as e:
                print(f"监控 {stock_code} 时发生错误: {e}")
                time.sleep(5)  # 出错后等待5秒再继续

    def input_stock_codes(self):
        """用户输入股票代码"""
        print("=== 股票振幅监控程序 ===")
        print("请输入要监控的股票代码 (用逗号分隔，如: 00700,00941,000001)")
        print("输入 'quit' 退出程序")

        while True:
            user_input = input("\n请输入股票代码: ").strip()

            if user_input.lower() == 'quit':
                return False

            if not user_input:
                print("请输入有效的股票代码")
                continue

            # 分割股票代码
            codes = [code.strip() for code in user_input.split(',')]
            codes = [code for code in codes if code]  # 过滤空字符串

            if codes:
                self.stock_codes = codes
                print(f"已设置监控股票: {', '.join(codes)}")
                return True
            else:
                print("请输入有效的股票代码")

    def start_monitoring(self):
        """开始监控"""
        print(f"\n开始监控 {len(self.stock_codes)} 只股票...")
        print(f"振幅阈值: {self.amplitude_threshold * 100:.1f}%")
        print(f"检查间隔: {self.time_interval} 秒")
        print("按 Ctrl+C 停止监控\n")

        self.monitoring = True

        # 为每个股票创建监控线程
        threads = []
        for stock_code in self.stock_codes:
            thread = threading.Thread(target=self.monitor_stock, args=(stock_code,))
            thread.daemon = True
            threads.append(thread)
            thread.start()

        try:
            # 等待所有线程完成
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            self.monitoring = False
            print("监控已停止")

    def run(self):
        """运行程序"""
        print("股票振幅监控程序启动...")
        print("注意: 请确保已正确配置富途API密钥和访问令牌")

        while True:
            if not self.input_stock_codes():
                break

            self.start_monitoring()

            # 询问是否继续
            continue_input = input("\n是否继续监控其他股票? (y/n): ").strip().lower()
            if continue_input != 'y':
                break

        print("程序结束")

def main():
    """主函数"""
    monitor = StockAmplitudeMonitor()
    monitor.run()

if __name__ == "__main__":
    main()