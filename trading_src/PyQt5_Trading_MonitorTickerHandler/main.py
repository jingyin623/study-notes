from trading_src.PyQt5_Trading_MonitorTickerHandler.main_Pane import mainPane
from trading_src.PyQt5_Trading_MonitorTickerHandler.GetsJumpPoint_Pane import GetsJumpPointPane
from trading_src.PyQt5_Trading_MonitorTickerHandler.MonitorTickerHandler_Pane import MonitorTickerHandlerPane
from trading_src.PyQt5_Trading_MonitorTickerHandler.AutoTrade_Pane import AutoTradePane

from PyQt5.Qt import *

import logging
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    # 创建面板主面板
    mian_pane = mainPane()

    #  槽函数
    def show_MonitorTickerHandler_Pane():
        print('展示MonitorTickerHandlerPane界面')
        monitorTickerHandlerPane = MonitorTickerHandlerPane(mian_pane)
        monitorTickerHandlerPane.move(10, 30 + 350)
        monitorTickerHandlerPane.show()
    def show_GetsJumpPoint_Pane():
        print('展示GetsJumpPoint界面')
        getsJumpPoint_Pane = GetsJumpPointPane(mian_pane)
        getsJumpPoint_Pane.move(10 + 280, 30)
        getsJumpPoint_Pane.show()
    def show_AutoTrade_Pane():
        logger.info('展示AutoTrade界面')
        autoTrade_Pane = AutoTradePane(mian_pane)
        autoTrade_Pane.move(10, 30)
        autoTrade_Pane.show()
    #
    # # 信号的链接
    mian_pane.MonitorTickerHandler_signal.connect(show_MonitorTickerHandler_Pane)
    mian_pane.GetsJumpPoint_signal.connect(show_GetsJumpPoint_Pane)
    mian_pane.AutoTradePane_signal.connect(show_AutoTrade_Pane)

    mian_pane.show()
    sys.exit(app.exec_())

