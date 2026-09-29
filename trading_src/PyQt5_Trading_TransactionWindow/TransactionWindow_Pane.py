from PyQt5.Qt import *
from trading_src.PyQt5_Trading_TransactionWindow.resource.TransactionWindow_ui import Ui_Form
from trading_src.PyQt5_Trading_TransactionWindow.TransactionWindow import FORECAST_LIST, submit_run, quote_context_close, quote_context_stop
import time


# 创建一个子线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)

    def run(self):
        # 无限循环，每秒钟传递一次时间给UI
        while True:
            self.update_data.emit(FORECAST_LIST)
            time.sleep(0.1)


class TransactionWindowPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

    # 被子线程的信号触发，更新一次数据
    def timeUpdate(self, data):
        # self.textEdit.setPlainText(data)
        # self.textEdit.setText(data)
        # self.listView.listView(data)
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView.setModel(listModel)
        # self.textEdit.setHtml(data)

    def subimit(self):  # type: ignore
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY_LE = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        # 启动后台业务逻辑
        submit_run(MARKET_SECURITY, TRADING_SECURITY_LE, TRADING_NUM)
        # 创建子线程 持续接收并显示后台逻辑结果
        self.subThread = UpdateThread()
        # 将子线程中的信号与timeUpdate槽函数绑定
        self.subThread.update_data.connect(self.timeUpdate)
        # 启动子线程（开始更新时间）
        self.subThread.start()

    def enable_register_btn(self):
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY_LE = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()         # 交易目标经纪号
        PRICE = self.PRICE_LE.text()                     # 买入价格
        VOLUME = self.VOLUME_LE.text()                   # 订单数价格
        MARKET_PRICE = self.MARKET_SECURITY_LE.text()    # 市场点位
        PERCENT = self.PERCENT_LE.text()                 # 市场百分比
        if len(MARKET_SECURITY) > 0 and len(TRADING_SECURITY_LE) > 0 and \
                len(TRADING_NUM) > 0 and len(CALL_OR_PUT) > 0:
            self.Submit_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)
        if len(PRICE) > 0 and len(VOLUME) > 0 and \
                len(MARKET_PRICE) > 0 and len(PERCENT) > 0:
            self.Buy_btn.setEnabled(True)
            self.Sell_btn.setEnabled(True)
        else:
            self.Buy_btn.setEnabled(False)
            self.Sell_btn.setEnabled(True)

    def exit_pane(self):
        quote_context_close()
        self.close()

    def stop_pane(self):
        quote_context_stop()

    def call_btn(self):
        print('call')

    def sell_btn(self):
        print('sell')


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = TransactionWindowPane()
    window.show()
    sys.exit(app.exec_())

