

from PyQt5.Qt import *

from trading_src.PyQt5_Trading_Demo.GetWarrant import get_warrant
from trading_src.PyQt5_Trading_Demo.GetBrokerId import get_broker, set_broker
from trading_src.PyQt5_Trading_Demo.resource.AutoTrade_ui import Ui_Form
from trading_src.PyQt5_Trading_Demo.AutoTrade import FORECAST_LIST, submit_run, quote_context_close, quote_context_reset
import time
import logging
from trading_src.PyQt5_Trading_Demo.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')
UPDAT_TIME = 120


# 价格信息展示线程
class UpdateThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)

    def run(self):
        while True:
            self.update_data.emit(FORECAST_LIST)    # 释放一次信号,有参数
            time.sleep(0.1)

# 创建一个涡轮选股子线程
class SwarrantThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal()
    def run(self):
        while True:
            self.update_data.emit()     # 释放一次信号,无参数
            time.sleep(UPDAT_TIME)
            logger.info('线程启动更新时间:{}'.format(UPDAT_TIME))


class AutoTradePane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)                  # 初始化面板框架
        self.btn_set = {'UB', 'JP', 'BP', 'HS', 'MB', 'MS', 'CT', 'SG'}          # 保存和填充数据集合
        self.LE_set = {'MARKET_SECURITY', 'TRADING_SECURITY', 'TRADING_NUM', 'CALL_PARAGRAPH', 'PUT_PARAGRAPH',
                       'ORDER_QUANTITY', 'ORDER_SIZE', 'MARKET_SMALL_WRT_RATIO', 'PASS_WORD', 'OR_CANCEL_ALL',
                       'TRIM_PARAGRAPH', 'STOCK_OWNER', 'CURPRICEMAX', 'STREETMIN', 'PREMIUMMAX', 'UPDATA_TIME'}   # 需要保存的变量
        self.Issuer_set_list = set()        # 初始化查询的做市商
        self.init_login_info()              # 填充数据
        self.clicked_already = False        # 类变量,用于控制解绑信号
        self.is_seek_swarrant = False       # 类变量，用于控制seek_swarrant线程调用

    # 更新listView数据
    def listViewUpdate(self, data):
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView.setModel(listModel)

    # 提交按钮
    def subimit(self):  # type: ignore
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()   # 标的参考代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()     # 交易标的
        TRADING_NUM = self.TRADING_NUM_LE.text()     # 交易目标经纪号
        PUT_PARAGRAPH = self.PUT_PARAGRAPH_LE.text()
        CALL_PARAGRAPH = int(self.CALL_PARAGRAPH_LE.text()) + int(PUT_PARAGRAPH)
        ORDER_QUANTITY = self.ORDER_QUANTITY_LE.text()
        ORDER_SIZE = self.ORDER_SIZE_LE.text()
        MARKET_SMALL_WRT_RATIO = self.MARKET_SMALL_WRT_RATIO_LE.text()
        PASS_WORD = self.PASS_WORD_LE.text()
        OR_CANCEL_ALL = self.OR_CANCEL_ALL_LE.text()
        TRIM_PARAGRAPH = self.TRIM_PARAGRAPH_LE.text()
        set_broker('HK.' + TRADING_SECURITY, TRADING_NUM)   # 做市商代码对应的经纪号 写入
        # 只有当is_seek_swarrant未开启时执行一次
        if not self.is_seek_swarrant:
            logger.debug('涡轮子线程开始执行')
            self.is_seek_swarrant = True  # 更新线程状态为开启状态
            # 选股子线程(无数据)
            self.swarrantThread = SwarrantThread()
            # 将子线程中的信号连接(绑定)给swarrant_sub函数
            self.swarrantThread.update_data.connect(self.swarrant_sub)
            # 启动子线程
            self.swarrantThread.start()
        # 启动后台业务逻辑
        submit_run(MARKET_SECURITY, TRADING_SECURITY, TRADING_NUM, CALL_PARAGRAPH, PUT_PARAGRAPH, ORDER_QUANTITY,
                   ORDER_SIZE, MARKET_SMALL_WRT_RATIO, PASS_WORD, OR_CANCEL_ALL, TRIM_PARAGRAPH)
        # 价格信息子线程
        self.subThread = UpdateThread()
        # 将子线程中的信号连接(绑定)给timeUpdate函数
        self.subThread.update_data.connect(self.listViewUpdate)
        # 启动子线程（开始更新时间）
        self.subThread.start()

    # 更改按钮状态(每次输入后判断一次)
    def enable_register_btn(self):
        # 获取所有 QLineEdit 的文本
        texts = [edit.text().strip() for edit in self.findChildren(QLineEdit)]
        # 检查是否所有文本都不为空
        submit_enabled = all(texts)
        warrant_enabled = bool(
            self.STOCK_OWNER_LE.text() and self.CURPRICEMAX_LE.text() and self.PREMIUMMAX_LE.text() and self.STREETMIN_LE.text())
        # 设置按钮的启用状态
        self.Submit_btn.setEnabled(submit_enabled)
        self.Warrant_btn.setEnabled(warrant_enabled)

    # 点击填充数据(交易代码和经纪号)
    def on_list_item_clicked(self, index):
        if self.is_seek_swarrant: self.reset_pane()     # seek_swarrant线程启动状态,执行重置方法
        text = index.data(Qt.DisplayRole)[:5]           # 获取被单击项的前5个字符 (交易代码)
        self.TRADING_SECURITY_LE.setText(text)          # 填充代码
        broker_id = str(get_broker('HK.' + text))       # 获取代码对应的做市商的经纪号
        self.TRADING_NUM_LE.setText(broker_id)          # 填充经纪号
        logger.info('填充涡轮代码-->{} 经纪号{}'.format(text, broker_id))

    # 选股函数
    def swarrant_sub(self):
        global UPDAT_TIME
        STOCK_OWNER = self.STOCK_OWNER_LE.text()
        CURPRICEMAX = self.CURPRICEMAX_LE.text()
        STREETMIN = self.STREETMIN_LE.text()
        PREMIUMMAX = self.PREMIUMMAX_LE.text()
        self.UPDATA_TIME_LE.setText('60') if int(self.UPDATA_TIME_LE.text()) < 60 else None
        UPDAT_TIME = int(self.UPDATA_TIME_LE.text())     # 更新 涡轮自动刷新时间
        good_value = get_warrant(STOCK_OWNER, CURPRICEMAX, STREETMIN, PREMIUMMAX, list(self.Issuer_set_list))   # 得到筛选后股票信息
        model = QStringListModel()
        model.setStringList(good_value)
        self.listView_2.setModel(model)
        # 信号绑定状态
        if self.clicked_already:
            # 解绑信号
            self.listView_2.clicked.disconnect(self.on_list_item_clicked)
            # 绑定信号与槽 用于单击填充
            self.listView_2.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
        else:
            # 给listView_2每个元素连接(带参数)绑定函数
            self.listView_2.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
            self.clicked_already = True
        # 自动选轮按钮状态(开启)
        if self.Autotrading_btn.isChecked():
            logger.info('提示:自动选轮状态开启,自动填充开启,自动提交开启大于等于80分涡轮')
            # 列表第一个元素得分
            if 100 >= int(good_value[0]) >= 80:
                try:
                    code = good_value[1][:5]    # 交易涡轮
                    num = str(get_broker('HK.' + code))    # 涡轮相关经纪号
                    logger.info('重置涡轮符合自动填充要求填充代码{} 经纪号{}'.format(code, num))
                # 查询出错就重置撤单
                except Exception as e:
                    self.reset_pane()        # 重置数据
                # 不是同一个涡轮,经纪号也有的时候
                if self.TRADING_SECURITY_LE.text() != code and num != '0':
                    self.reset_pane()        # 重置数据
                    self.TRADING_SECURITY_LE.setText(code)  # 自动填充代码(第二个元素)
                    self.TRADING_NUM_LE.setText(num)  # 自动填充代码做市商的经纪号
                    time.sleep(1)
                if UPDAT_TIME < 300:  # 自动刷新时间小于5分钟设置为5分钟
                    UPDAT_TIME = 300
                    self.UPDATA_TIME_LE.setText('300')
                self.subimit()



    # 自动选轮按钮状态样式
    def autotrading(self):
        if self.Autotrading_btn.isChecked():  # 检查按钮状态
            self.Autotrading_btn.setText('True')
            self.Autotrading_btn.setStyleSheet("background-color: #7CFC00;")  # 设置绿色背景
        else:
            self.Autotrading_btn.setText('False')
            self.Autotrading_btn.setStyleSheet("background-color: #FF0000;")  # 设置红色背景
        logger.debug('自动涡轮状态-->{}'.format(self.Autotrading_btn.isChecked()))

    # 点击做市商按钮
    def Issuer_btn(self):
        button = window.sender()            # sender()方法获取发送信号的对象（即被点击的按钮）
        if button.isChecked():
            # 如果按钮被选中
            self.Issuer_set_list.add(button.text()) if button.text() not in self.Issuer_set_list else None    # 判断添加元素
            button.setStyleSheet("background-color: #7CFC00;")  # 设置绿色背景
        else:
            # 如果按钮被取消选中
            self.Issuer_set_list.discard(button.text()) if button.text() in self.Issuer_set_list else None    # 判断删除元素
            button.setStyleSheet("background-color: #FF0000;")  # 设置红色背景
        logger.debug('{}是否选中-->{}||集合中{}'.format(button.text(), button.isChecked(), self.Issuer_set_list))

    def exit_pane(self):
        self.save_login_info()
        quote_context_close()
        self.close()

    def reset_pane(self):
        quote_context_reset()
        self.TRADING_SECURITY_LE.clear()     # 清空交易lineEdit

    # 保存lineEdit中内容
    def save_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)

        # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            # getattr(object, attribute[, default])
            # 其中，object 是要获取属性的对象，attribute 是属性名，default 是默认值（可选参数）
            # value = getattr(self, Issuer + '_LE').text()
            # settings.setValue("PREMIUMMAX", self.PREMIUMMAX_LE.text()) # 模板
            settings.setValue(Issuer, getattr(self, '{}_LE'.format(Issuer)).text())

        # # 根据属性名动态访问对象属性(_btn)
        for Issuer in self.btn_set:
            # settings.setValue("button_state", self.button.isChecked())    # 模板
            settings.setValue(Issuer, getattr(self, '{}_btn'.format(Issuer)).isChecked())

    # 提取文件之并填充对应的lineEdit
    def init_login_info(self):
        settings = QSettings("config.ini", QSettings.IniFormat)
        # # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            # object是要设置属性的对象，attribute是待设置的属性名，value是要设置的属性值
            # setattr(object, attribute, value)
            # setattr(self, Issuer, settings.value(Issuer))

            # self.MARKET_SECURITY_LE.setText(settings.value("MARKET_SECURITY")) # 模板
            getattr(self, '{}_LE'.format(Issuer)).setText(settings.value(Issuer))

        # # 根据属性名动态访问对象属性(LE)
        for Issuer in self.btn_set:
            value = settings.value(Issuer, False, type=bool)
            self.Issuer_set_list.add(Issuer) if value else None     # 加入到查询数据集合中
            getattr(self, '{}_btn'.format(Issuer)).setChecked(value) # 模板
            # getattr(self, Issuer + '_btn').setText(settings.value(Issuer))


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = AutoTradePane()
    window.show()
    sys.exit(app.exec_())

