from PyQt5.Qt import *
from trading_src.PyQt5_Trading_TransactionWindow.resource.main_ui import Ui_Form

import logging
import os
from trading_src.PyQt5_Trading_TransactionWindow.my_logger import initLogConf
initLogConf(os.getcwd())
logger = logging.getLogger('my_logger')

class mainPane(QWidget, Ui_Form):
    # 自定义信号，外部调用
    MonitorTickerHandler_signal = pyqtSignal()          # 自定义信号
    GetsJumpPoint_signal = pyqtSignal()       # 自定义信号
    AutoTradePane_signal = pyqtSignal()       # 自定义信号

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    # 槽函数
    def show_MonitorTickerHandler_Pane(self):  # type: ignore
        print('MonitorTickerHandler_signal')
        self.MonitorTickerHandler_signal.emit()

    def show_GetsJumpPoint_Pane(self):
        print('GetsJumpPoint_signal')
        self.GetsJumpPoint_signal.emit()

    def show_AutoTrade_Pane(self):
        logger.info('AutoTrade_signal')
        self.AutoTradePane_signal.emit()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = mainPane()
    window.show()
    sys.exit(app.exec_())

