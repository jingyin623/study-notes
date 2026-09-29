

from PyQt5.Qt import *
from trading_src.PyQt5_Trading_MonitorTickerHandler.resource.ElectronicBill_ui import Ui_Form
from trading_src.PyQt5_Trading_MonitorTickerHandler.ElectronicBill import FORECAST_LIST, submit_run, quote_context_close, updata, buy, sell, setOrderBtn, ORDER_BTN
import time

import logging
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')


# 创建一个子线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)
    update_order_btn = pyqtSignal(str)

    def run(self):
        # 无限循环，每秒钟传递一次时间给UI
        while True:
            self.update_data.emit(FORECAST_LIST)
            self.update_order_btn.emit(ORDER_BTN)
            time.sleep(0.05)


class ElectronicBillPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

    # 被子线程的信号触发，更新一次数据
    def timeUpdate(self, data):
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView.setModel(listModel)

    # 被子线程的信号触发，更新一次数据
    def timeUpdateOrder_btn(self, data):
        if data == '0':
            self.Status_btn.setText("状态:取消")
        elif data == 'BUY':
            self.Status_btn.setText("状态:正在买入监听")
        elif data == 'SELL':
            self.Status_btn.setText("状态:正在卖出监听")

    def subimit(self):  # type: ignore
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()

        # 启动后台业务逻辑
        submit_run(MARKET_SECURITY, TRADING_SECURITY, TRADING_NUM)
        # 创建子线程 持续接收并显示后台逻辑结果
        self.subThread = UpdateThread()
        # 将子线程中的信号与timeUpdate槽函数绑定
        self.subThread.update_data.connect(self.timeUpdate)
        self.subThread.update_order_btn.connect(self.timeUpdateOrder_btn)
        # 启动子线程（开始更新时间）
        self.subThread.start()

    def updata_pane(self):
        # 调用方法 获取 行情， 百分比， 价格并更新
        list = updata()
        self.MARKET_PRICE_LE.setText(str(list[0]))
        self.PERCENT_LE.setText(str(list[1]))
        self.PRICE_LE.setText(str(list[2]))

    def buy_pane(self):
        ORDER_SIZE = self.ORDER_SIZE_LE.text()
        MARKET_PRICE = self.MARKET_PRICE_LE.text()
        PERCENT = self.PERCENT_LE.text()
        PRICE = self.PRICE_LE.text()
        buy(ORDER_SIZE, MARKET_PRICE, PERCENT, PRICE, 'BUY')

    def sell_pane(self):
        ORDER_SIZE = self.ORDER_SIZE_LE.text()
        MARKET_PRICE = self.MARKET_PRICE_LE.text()
        PERCENT = self.PERCENT_LE.text()
        PRICE = self.PRICE_LE.text()
        sell(ORDER_SIZE, MARKET_PRICE, PERCENT, PRICE, 'SELL')

    def cancel_pane(self):
        setOrderBtn('0')


    def exit_pane(self):
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()     # 交易标的
        quote_context_close(['HK.' + TRADING_SECURITY, 'HK.' + MARKET_SECURITY])
        self.close()


    def enable_register_btn(self):
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY_LE = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        ORDER_SIZE = self.ORDER_SIZE_LE.text()
        MARKET_PRICE = self.MARKET_PRICE_LE.text()
        PERCENT = self.PERCENT_LE.text()
        PRICE = self.PRICE_LE.text()
        if len(MARKET_SECURITY) \
                > 0 and len(TRADING_SECURITY_LE) \
                > 0 and len(TRADING_NUM):
            self.Submit_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)
        if len(MARKET_SECURITY) \
                > 0 and len(TRADING_SECURITY_LE) \
                > 0 and len(TRADING_NUM) \
                > 0 and len(ORDER_SIZE) \
                > 0 and len(MARKET_PRICE) \
                > 0 and len(PERCENT) \
                > 0 and len(PRICE):
            self.Buy_btn.setEnabled(True)
            self.Sell_btn.setEnabled(True)

        else:
            self.Buy_btn.setEnabled(False)
            self.Sell_btn.setEnabled(False)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = ElectronicBillPane()
    window.show()
    sys.exit(app.exec_())

