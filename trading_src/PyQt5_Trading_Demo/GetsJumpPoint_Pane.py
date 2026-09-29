from PyQt5.Qt import *
from trading_src.PyQt5_Trading_Demo.resource.GetsJumpPoint_ui import Ui_Form
from trading_src.PyQt5_Trading_Demo.GetsJumpPoint import FORECAST_LIST, submit_run, quote_context_close, quote_context_stop
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


class GetsJumpPointPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

    # 被子线程的信号触发，更新一次数据
    def timeUpdate(self, data):
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView.setModel(listModel)

    def subimit(self):  # type: ignore
        MARKET_SECURITY = 'HK.' + self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY_LE = 'HK.' + self.TRADING_SECURITY_LE.text()     # 交易标的
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
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        if len(MARKET_SECURITY) > 0 and len(TRADING_SECURITY_LE) > 0 and len(TRADING_NUM) > 0:
            self.Submit_btn.setEnabled(True)
            self.Stop_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)
            self.Stop_btn.setEnabled(False)

    def stop_pane(self):
        self.TRADING_SECURITY_LE.clear()     # 交易标的
        self.TRADING_NUM_LE.clear()     # 交易目标经纪号

    def exit_pane(self):
        self.close()



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = GetsJumpPointPane()
    window.show()
    sys.exit(app.exec_())

