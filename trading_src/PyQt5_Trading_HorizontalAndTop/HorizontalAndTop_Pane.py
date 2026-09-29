from PyQt5.Qt import *
from trading_src.PyQt5_Trading_HorizontalAndTop.resource.HorizontalAndTop import Ui_Form
from trading_src.PyQt5_Trading_HorizontalAndTop.HorizontalAndTop import FORECAST_LIST_ALL, add_code, quote_context_close, SUBSCRIBE_DICT_LIST, remove_code, load_code, get_trading_security_thread
import time


# 创建一个子线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)
    def run(self):
        # 无限循环，每秒钟传递一次时间给UI
        while True:
            self.update_data.emit(FORECAST_LIST_ALL)
            time.sleep(0.1)

class GetsJumpPointPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle('GetsJumpPoint')  # 修改窗口标题
        self.LE_set = {'MARKET_SECURITY', 'MARKET_SMALL', 'TRADING_SECURITY', 'TRADING_NUM', 'TRADING_SENSITIVITY'}
        self.init_login_info()              # 填充数据
        self.clicked_already = False        # 类变量,用于控制解绑信号
        self.UpdateThread_thread()
        load_code()
        self.update_subscribe_dict_list()

        # 创建模型
        self.item_model = QStandardItemModel()
        # 设置模型
        self.listView_2.setModel(self.item_model)

    # 被子线程的信号触发，更新一次数据
    def timeUpdate(self, data):
        # 清空item_model
        self.item_model.clear()
        # 遍历数据并创建QStandardItem
        for i, item in enumerate(data):
            q_item = QStandardItem(item)
            if i % 2 == 0:
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

    # 点击删除相关信息
    def on_list_item_clicked(self, index):
        text = (index.data(Qt.DisplayRole))[0:8]          # 获取被单击项的前5个字符 (交易代码)
        data_list = get_trading_security_thread(text)
        self.MARKET_SECURITY_LE.setText(data_list[0][3:])   # 标的参考代码
        self.MARKET_SMALL_LE.setText(data_list[1])  # 最小跳价点
        self.TRADING_SECURITY_LE.setText(data_list[2][3:])     # 交易标的
        self.TRADING_NUM_LE.setText(data_list[3])     # 交易目标经纪号
        self.TRADING_SENSITIVITY_LE.setText(data_list[4])  # 敏感度
        remove_code(text)
        print(text)
        self.update_subscribe_dict_list()

    def update_subscribe_dict_list(self):
        model = QStringListModel()
        model.setStringList(SUBSCRIBE_DICT_LIST)
        self.listView.setModel(model)
        # # 信号绑定状态
        if self.clicked_already:
            # 解绑信号
            self.listView.clicked.disconnect(self.on_list_item_clicked)
            # 绑定信号与槽 用于单击填充
            self.listView.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
        else:
            # 给listView_2每个元素连接(带参数)绑定函数
            self.listView.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
            self.clicked_already = True

    def UpdateThread_thread(self):
        # 提示信息子线程
        self.triggerListThread = UpdateThread()
        # 将子线程中的信号连接(绑定)给timeUpdate函数
        self.triggerListThread.update_data.connect(self.timeUpdate)
        # 启动子线程（开始更新时间）
        self.triggerListThread.start()

    def subimit(self):  # type: ignore
        MARKET_SECURITY = 'HK.' + self.MARKET_SECURITY_LE.text()   # 标的参考代码
        MARKET_SMALL = self.MARKET_SMALL_LE.text()  # 最小跳价点
        TRADING_SECURITY = 'HK.' + self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        TRADING_SENSITIVITY = self.TRADING_SENSITIVITY_LE.text()  # 敏感度
        # 启动后台业务逻辑
        add_code(MARKET_SECURITY, MARKET_SMALL, TRADING_SECURITY, TRADING_NUM, TRADING_SENSITIVITY)
        self.update_subscribe_dict_list()

    def enable_register_btn(self):
        MARKET_SECURITY = 'HK.' + self.MARKET_SECURITY_LE.text()   # 标的参考代码
        MARKET_SMALL = self.MARKET_SMALL_LE.text()  # 最小跳价点
        TRADING_SECURITY = 'HK.' + self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        TRADING_SENSITIVITY = self.TRADING_SENSITIVITY_LE.text()  # 敏感度
        if len(MARKET_SECURITY) > 0 and len(TRADING_SECURITY) > 0 \
                and len(TRADING_NUM) > 0 and len(MARKET_SMALL) > 0 \
                and len(TRADING_SENSITIVITY) > 0:
            self.Submit_btn.setEnabled(True)
            self.Stop_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)
            self.Stop_btn.setEnabled(False)

    def stop_pane(self):
        self.TRADING_SECURITY_LE.clear()     # 交易标的
        self.MARKET_SMALL_LE.clear()     # 最小跳价点
        self.TRADING_SECURITY_LE.clear()     # 交易标的
        self.TRADING_NUM_LE.clear()     # 交易目标经纪号
        self.TRADING_SENSITIVITY_LE.clear()     # 敏感度

    def exit_pane(self):
        self.save_login_info()
        quote_context_close()
        self.close()

    # 保存lineEdit中内容
    def save_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            settings.setValue(Issuer, getattr(self, '{}_LE'.format(Issuer)).text())

    # 提取文件之并填充对应的lineEdit
    def init_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        # # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            getattr(self, '{}_LE'.format(Issuer)).setText(settings.value(Issuer))


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = GetsJumpPointPane()
    window.show()
    sys.exit(app.exec_())

