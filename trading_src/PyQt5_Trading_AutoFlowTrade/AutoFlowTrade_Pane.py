

from PyQt5.Qt import *

from trading_src.PyQt5_Trading_AutoFlowTrade.GetWarrant import get_warrant
from trading_src.PyQt5_Trading_AutoFlowTrade.GetBrokerId import get_broker, set_broker
from trading_src.PyQt5_Trading_AutoFlowTrade.resource.AutoFlowTrade_ui import Ui_Form
from trading_src.PyQt5_Trading_AutoFlowTrade.AutoFlowTrade import FORECAST_LIST, submit_run, quote_context_close, quote_context_reset
import time
import logging
from trading_src.PyQt5_Trading_AutoFlowTrade.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')
UPDAT_TIME = 120

# 定义一个可观察列表类
class ObservableList:
    def __init__(self, initial_list):
        self._list = initial_list.copy()
        self._callbacks = []

    def set_list(self, new_list):
        if self._list != new_list:
            self._list = new_list.copy()
            for callback in self._callbacks:
                callback(self._list)

    def get_list(self):
        return self._list.copy()

    def add_callback(self, callback):
        self._callbacks.append(callback)

# 初始化可观察的 FORECAST_LIST
observable_forecast_list = ObservableList(FORECAST_LIST)

# 价格信息展示线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        # 注册回调函数，当可观察列表变化时触发
        observable_forecast_list.add_callback(self.on_list_changed)

    def on_list_changed(self, new_list):
        # 发射信号，传递更新后的数据
        self.update_data.emit(new_list)

    def run(self):
        # 保持线程运行
        pass
        # while True:
        #     time.sleep(0.1)

class AutoTradePane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)                  # 初始化面板框架
        self.setWindowFlags(Qt.WindowStaysOnTopHint)    # 使窗口永远保持最前端
        self.setWindowTitle('AutoFlowTrade')  # 修改窗口标题
        self.LE_set = {'MARKET_SECURITY', 'TRADING_SECURITY', 'TRADING_NUM', 'CALL_PARAGRAPH', 'PUT_PARAGRAPH',
                       'ORDER_QUANTITY', 'ORDER_SIZE', 'MARKET_SMALL_WRT_RATIO', 'PASS_WORD', 'OR_CANCEL_ALL',
                       'TRIM_PARAGRAPH'}   # 需要保存的变量
        self.init_login_info()              # 填充数据
        self.clicked_already = False        # 类变量,用于控制解绑信号
        self.datalist = []                  # 用于存放当前运行的交易代码和经济号

        # 创建模型
        self.item_model = QStandardItemModel()
        # 设置模型
        self.listView.setModel(self.item_model)

        # 价格信息子线程
        self.subThread = UpdateThread()
        # 将子线程中的信号连接(绑定)给timeUpdate函数
        self.subThread.update_data.connect(self.listViewUpdate)
        # 启动子线程（开始更新时间）
        self.subThread.start()

    # 被子线程的信号触发，更新一次数据
    def listViewUpdate(self, data):
        # 清空item_model
        self.item_model.clear()
        # 遍历数据并创建QStandardItem
        for i, item in enumerate(data):
            q_item = QStandardItem(item)
            if i % 3 == 0:
                if i % 4 == 0:
                    # 每隔4行，设置颜色为红色
                    q_item.setForeground(QColor('red'))
                    font = QFont()
                    font.setBold(True)  # 设置字体加粗
                    font.setPointSize(font.pointSize() + 2)
                    q_item.setFont(font)
                else:
                    # 每隔4行，设置颜色为红色
                    q_item.setForeground(QColor('blue'))
                    font = QFont()
                    font.setBold(True)  # 设置字体加粗
                    font.setPointSize(font.pointSize() + 1)
                    q_item.setFont(font)
            self.item_model.appendRow(q_item)


    # 提交按钮
    def subimit(self):  # type: ignore
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        PUT_PARAGRAPH = self.PUT_PARAGRAPH_LE.text()
        CALL_PARAGRAPH = self.CALL_PARAGRAPH_LE.text()
        ORDER_QUANTITY = self.ORDER_QUANTITY_LE.text()
        ORDER_SIZE = self.ORDER_SIZE_LE.text()
        MARKET_SMALL_WRT_RATIO = self.MARKET_SMALL_WRT_RATIO_LE.text()
        PASS_WORD = self.PASS_WORD_LE.text()
        OR_CANCEL_ALL = self.OR_CANCEL_ALL_LE.text()
        TRIM_PARAGRAPH = self.TRIM_PARAGRAPH_LE.text()
        # 启动后台业务逻辑
        submit_run(MARKET_SECURITY, TRADING_SECURITY, TRADING_NUM, CALL_PARAGRAPH, PUT_PARAGRAPH, ORDER_QUANTITY,
                   ORDER_SIZE, MARKET_SMALL_WRT_RATIO, PASS_WORD, OR_CANCEL_ALL, TRIM_PARAGRAPH)

    # 更改按钮状态(每次输入后判断一次)
    def enable_register_btn(self):
        # 获取所有 QLineEdit 的文本
        texts = [edit.text().strip() for edit in self.findChildren(QLineEdit)]
        # 检查是否所有文本都不为空
        submit_enabled = all(texts)
        # 设置按钮的启用状态
        self.Submit_btn.setEnabled(submit_enabled)

    def exit_pane(self):
        self.save_login_info()
        quote_context_close()
        self.close()

    def reset_pane(self, datalist):
        # 防止多次点击同一个涡轮造成卡死
        if self.datalist != datalist:
            quote_context_reset()
            self.datalist = datalist
            self.TRADING_SECURITY_LE.clear()     # 清空交易lineEdit
            self.TRADING_NUM_LE.clear()             # 清空经济号lineEdit

    # 保存lineEdit中内容
    def save_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            settings.setValue(Issuer, getattr(self, '{}_LE'.format(Issuer)).text())

    # 提取文件之并填充对应的lineEdit
    def init_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        for Issuer in self.LE_set:
            getattr(self, '{}_LE'.format(Issuer)).setText(settings.value(Issuer))


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = AutoTradePane()
    window.show()
    sys.exit(app.exec_())

