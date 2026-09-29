from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("左边最大尺寸，右边最小尺寸，动态隐藏示例")
        self.setGeometry(100, 100, 800, 400)

        # 左侧部分
        self.left_widget = QLabel("左边部分")
        self.left_widget.setStyleSheet("background-color: lightblue;")
        self.left_widget.setMaximumWidth(300)  # 设置左边最大宽度

        # 右侧部分
        self.right_widget = QLabel("右边部分（保持最小宽度）")
        self.right_widget.setStyleSheet("background-color: lightgreen;")
        self.right_widget.setMinimumWidth(200)  # 设置右边最小宽度

        # 使用 QSplitter 创建可调节布局
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setStretchFactor(0, 1)  # 左边部分初始可拉伸
        self.splitter.setStretchFactor(1, 1)  # 右边部分初始可拉伸

        # 主窗口布局
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        """
        监听窗口大小变化，动态调整布局。
        - 如果右边部分的宽度小于最小宽度，则隐藏左边部分。
        """
        total_width = self.width()  # 窗口总宽度
        right_width = self.splitter.sizes()[1]  # 获取右边部分的宽度

        # 当右边部分的宽度小于等于最小时，隐藏左边
        if right_width <= self.right_widget.minimumWidth():
            self.left_widget.hide()
            self.splitter.setSizes([0, total_width])  # 将全部宽度分配给右边部分
        else:
            self.left_widget.show()

        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
