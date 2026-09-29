# -*- coding: utf-8 -*-
import time
from PyQt5.Qt import *
from trading_src.PyQt5_Trading_TransactionWindow.resource.SurveillanceBoss_ui import Ui_Form
from trading_src.PyQt5_Trading_TransactionWindow.SurveillanceBoss import add_code, quote_context_close, SUBSCRIBE_DICT_LIST, TRIGGER_LIST, remove_code, save_code, load_code


# 提示信息
class triggerListThread(QThread):
    # 创建一个信号，触发时传递当前时间给槽函数
    update_data = pyqtSignal(list)

    def run(self):
        while True:
            self.update_data.emit(TRIGGER_LIST)    # 释放一次信号,有参数
            time.sleep(0.1)


class SurveillanceBossPane(QWidget, Ui_Form):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.LE_set = {'MARKET_SECURITY', 'TRADING_SECURITY', 'TRADING_NUM'}   # 需要保存的变量
        self.init_login_info()              # 填充数据
        self.clicked_already = False        # 类变量,用于控制解绑信号
        self.trigger_list_thread()
        load_code()                         # 调用加载方法
        self.update_subscribe_dict_list()
        # self.subimit()                      # 调用一次提交方法,启动进程



    # 更新listView数据(提示信息)
    def listViewUpdate(self, data):
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView.setModel(listModel)

    # 更新listView_2数据(监控列表)
    def listView_2Update(self, data):
        listModel = QStringListModel()
        listModel.setStringList(data)
        self.listView_2.setModel(listModel)

    def enable_register_btn(self):
        MARKET_SECURITY = self.MARKET_SECURITY_LE.text()    # 代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()    # 仓位
        TRADING_NUM = self.TRADING_NUM_LE.text()    # 方向
        if len(MARKET_SECURITY) > 0 and len(TRADING_SECURITY) > 0 and len(TRADING_NUM) > 0:
            self.Submit_btn.setEnabled(True)
            self.Stop_btn.setEnabled(True)
        else:
            self.Submit_btn.setEnabled(False)
            self.Stop_btn.setEnabled(False)

    # 点击删除相关信息
    def on_list_item_clicked(self, index):
        text = index.data(Qt.DisplayRole)          # 获取被单击项的前5个字符 (交易代码)
        # 分割输入字符串并转换为对应的数据类型
        tokens = text.split()  # 使用空格分割
        code = 'HK.' + tokens[0]  # 构建股票代码
        price = float(tokens[1])  # 将价格转换为浮点数
        action = tokens[2]  # 获取交易动作
        # 构建新的列表
        new_list = [code, price, action]
        remove_code(new_list)
        self.update_subscribe_dict_list()

    def update_subscribe_dict_list(self):
        model = QStringListModel()
        model.setStringList(SUBSCRIBE_DICT_LIST)
        self.listView_2.setModel(model)
        # # 信号绑定状态
        if self.clicked_already:
            # 解绑信号
            self.listView_2.clicked.disconnect(self.on_list_item_clicked)
            # 绑定信号与槽 用于单击填充
            self.listView_2.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
        else:
            # 给listView_2每个元素连接(带参数)绑定函数
            self.listView_2.clicked.connect(self.on_list_item_clicked)  # doubleClicked双击 clicked
            self.clicked_already = True

    def trigger_list_thread(self):
        # 提示信息子线程
        self.triggerListThread = triggerListThread()
        # 将子线程中的信号连接(绑定)给timeUpdate函数
        self.triggerListThread.update_data.connect(self.listViewUpdate)
        # 启动子线程（开始更新时间）
        self.triggerListThread.start()

    def subimit(self):  # type: ignore
        MARKET_SECURITY = 'HK.' + self.MARKET_SECURITY_LE.text()  # 代码
        TRADING_SECURITY = self.TRADING_SECURITY_LE.text()  # 仓位
        TRADING_NUM = self.TRADING_NUM_LE.text()  # 方向
        add_code(MARKET_SECURITY, TRADING_SECURITY, TRADING_NUM)
        self.update_subscribe_dict_list()




    def stop_pane(self):
        self.MARKET_SECURITY_LE.clear()     # 交易标的
        self.TRADING_SECURITY_LE.clear()     # 交易目标经纪号
        self.TRADING_NUM_LE.clear()     # 交易目标经纪号

    def exit_pane(self):
        self.save_login_info()
        quote_context_close()
        save_code()
        self.close()

    # 保存lineEdit中内容
    def save_login_info(self):
        settings = QSettings("config1.ini", QSettings.IniFormat)

        # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            # getattr(object, attribute[, default])
            # 其中，object 是要获取属性的对象，attribute 是属性名，default 是默认值（可选参数）
            # value = getattr(self, Issuer + '_LE').text()
            # settings.setValue("PREMIUMMAX", self.PREMIUMMAX_LE.text()) # 模板
            settings.setValue(Issuer, getattr(self, '{}_LE'.format(Issuer)).text())


    # 提取文件之并填充对应的lineEdit
    def init_login_info(self):
        settings = QSettings("config1.ini", QSettings.IniFormat)
        # # 根据属性名动态访问对象属性(LE)
        for Issuer in self.LE_set:
            # object是要设置属性的对象，attribute是待设置的属性名，value是要设置的属性值
            # setattr(object, attribute, value)
            # setattr(self, Issuer, settings.value(Issuer))

            # self.MARKET_SECURITY_LE.setText(settings.value("MARKET_SECURITY")) # 模板
            getattr(self, '{}_LE'.format(Issuer)).setText(settings.value(Issuer))

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = SurveillanceBossPane()
    window.show()
    sys.exit(app.exec_())
