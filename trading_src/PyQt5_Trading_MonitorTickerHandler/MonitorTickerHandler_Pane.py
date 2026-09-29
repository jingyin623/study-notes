
import time

from PyQt5.Qt import *
from trading_src.PyQt5_Trading_MonitorTickerHandler.resource.MonitorTickerHandler_ui import Ui_Form
from trading_src.PyQt5_Trading_MonitorTickerHandler.MonitorTickerHandler import submit_run, RECORD_SET, quote_context_close, quote_context_stop


# 创建一个子线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)

    def run(self):
        # 无限循环，每秒钟传递一次时间给UI
        while True:
            self.update_data.emit(list(RECORD_SET))
            time.sleep(0.5)


class MonitorTickerHandlerPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

        # 被子线程的信号触发，更新一次数据
    def timeUpdate(self, data):
            # self.textEdit.setText(data)
            listModel = QStringListModel()
            listModel.setStringList(data)
            self.listView.setModel(listModel)

    def subimit(self):  # type: ignore
        DEFAULTAMPLITUDE = self.DEFAULTAMPLITUDE_LE.text()   # 预设振幅
        DEFAULTTURNOVER = self.DEFAULTTURNOVER_LE.text()     # 预设成交额
        DEFAULTMULTIPLE = self.DEFAULTMULTIPLE_LE.text()     # 预设倍数
        LIFECYCLE = self.LIFECYCLE_LE.text()                 # 生命周期
        SUMTURNOVER = self.SUMTURNOVER_LE.text()             # 同向成交量倍数
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()     # 监测列表文件地址

        # 启动后台业务逻辑
        submit_run(MARKET_SECURITY, DEFAULTAMPLITUDE, DEFAULTTURNOVER, DEFAULTMULTIPLE, LIFECYCLE, SUMTURNOVER)
        # 创建子线程 持续接收并显示后台逻辑结果
        self.subThread = UpdateThread()
        # 将子线程中的信号与timeUpdate槽函数绑定
        self.subThread.update_data.connect(self.timeUpdate)
        # 启动子线程（开始更新时间）
        self.subThread.start()

    def enable_register_btn(self):
        print('每次输入框变化都执行一次判定')
        DEFAULTAMPLITUDE = self.DEFAULTAMPLITUDE_LE.text()  # 预设振幅
        DEFAULTTURNOVER = self.DEFAULTTURNOVER_LE.text()  # 预设成交额
        DEFAULTMULTIPLE = self.DEFAULTMULTIPLE_LE.text()  # 预设倍数
        LIFECYCLE = self.LIFECYCLE_LE.text()  # 生命周期
        SUMTURNOVER = self.SUMTURNOVER_LE.text()  # 同向成交量倍数
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()  # 监测列表文件地址
        if len(DEFAULTAMPLITUDE) > 0 and len(DEFAULTTURNOVER) > 0 and \
                len(DEFAULTMULTIPLE) > 0 and len(LIFECYCLE) > 0 and \
                len(SUMTURNOVER) > 0 and len(MARKET_SECURITY) > 0:
            self.Submit_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)

    def exit_pane(self):
        quote_context_close()
        self.close()

    def stop_btn(self):
        quote_context_stop()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MonitorTickerHandlerPane()
    window.show()
    sys.exit(app.exec_())

