# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'GetsJumpPoint_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListView, QPushButton, QSizePolicy,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(312, 591)
        self.horizontalLayout_3 = QHBoxLayout(Form)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.Submit_btn = QPushButton(Form)
        self.Submit_btn.setObjectName(u"Submit_btn")
        self.Submit_btn.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Submit_btn.sizePolicy().hasHeightForWidth())
        self.Submit_btn.setSizePolicy(sizePolicy)
        self.Submit_btn.setMaximumSize(QSize(156, 16777215))
        self.Submit_btn.setStyleSheet(u"")

        self.gridLayout.addWidget(self.Submit_btn, 6, 0, 1, 4)

        self.MARKET_SMALL_LE = QLineEdit(Form)
        self.MARKET_SMALL_LE.setObjectName(u"MARKET_SMALL_LE")
        self.MARKET_SMALL_LE.setMaximumSize(QSize(102, 16777215))
        self.MARKET_SMALL_LE.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.MARKET_SMALL_LE, 2, 2, 1, 2)

        self.label_6 = QLabel(Form)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMaximumSize(QSize(48, 16777215))

        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 2)

        self.listView = QListView(Form)
        self.listView.setObjectName(u"listView")
        self.listView.setMaximumSize(QSize(156, 16777215))

        self.gridLayout.addWidget(self.listView, 0, 0, 1, 4)

        self.Stop_btn = QPushButton(Form)
        self.Stop_btn.setObjectName(u"Stop_btn")
        sizePolicy.setHeightForWidth(self.Stop_btn.sizePolicy().hasHeightForWidth())
        self.Stop_btn.setSizePolicy(sizePolicy)
        self.Stop_btn.setMaximumSize(QSize(75, 16777215))
        self.Stop_btn.setStyleSheet(u"")

        self.gridLayout.addWidget(self.Stop_btn, 7, 0, 1, 3)

        self.TRADING_NUM_LE = QLineEdit(Form)
        self.TRADING_NUM_LE.setObjectName(u"TRADING_NUM_LE")
        self.TRADING_NUM_LE.setMaximumSize(QSize(102, 16777215))
        self.TRADING_NUM_LE.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.TRADING_NUM_LE, 4, 2, 1, 2)

        self.label_8 = QLabel(Form)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMaximumSize(QSize(48, 16777215))

        self.gridLayout.addWidget(self.label_8, 2, 0, 1, 2)

        self.label_7 = QLabel(Form)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMaximumSize(QSize(48, 16777215))

        self.gridLayout.addWidget(self.label_7, 5, 0, 1, 2)

        self.TRADING_SECURITY_LE = QLineEdit(Form)
        self.TRADING_SECURITY_LE.setObjectName(u"TRADING_SECURITY_LE")
        self.TRADING_SECURITY_LE.setMaximumSize(QSize(102, 16777215))
        self.TRADING_SECURITY_LE.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.TRADING_SECURITY_LE, 3, 2, 1, 2)

        self.Exit_btn = QPushButton(Form)
        self.Exit_btn.setObjectName(u"Exit_btn")
        sizePolicy.setHeightForWidth(self.Exit_btn.sizePolicy().hasHeightForWidth())
        self.Exit_btn.setSizePolicy(sizePolicy)
        self.Exit_btn.setMaximumSize(QSize(75, 16777215))
        self.Exit_btn.setStyleSheet(u"")

        self.gridLayout.addWidget(self.Exit_btn, 7, 3, 1, 1)

        self.MARKET_SECURITY_LE = QLineEdit(Form)
        self.MARKET_SECURITY_LE.setObjectName(u"MARKET_SECURITY_LE")
        self.MARKET_SECURITY_LE.setMaximumSize(QSize(102, 16777215))
        self.MARKET_SECURITY_LE.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.MARKET_SECURITY_LE, 1, 2, 1, 2)

        self.label_5 = QLabel(Form)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(48, 16777215))

        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 2)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setMaximumSize(QSize(48, 16777215))

        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 2)

        self.TRADING_SENSITIVITY_LE = QLineEdit(Form)
        self.TRADING_SENSITIVITY_LE.setObjectName(u"TRADING_SENSITIVITY_LE")
        self.TRADING_SENSITIVITY_LE.setMaximumSize(QSize(102, 16777215))
        self.TRADING_SENSITIVITY_LE.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.TRADING_SENSITIVITY_LE, 5, 2, 1, 2)


        self.horizontalLayout_2.addLayout(self.gridLayout)

        self.listView_2 = QListView(Form)
        self.listView_2.setObjectName(u"listView_2")
        self.listView_2.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.listView_2)


        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Form)
        self.TRADING_NUM_LE.textChanged.connect(Form.enable_register_btn)
        self.TRADING_SECURITY_LE.textChanged.connect(Form.enable_register_btn)
        self.MARKET_SECURITY_LE.textChanged.connect(Form.enable_register_btn)
        self.Exit_btn.clicked.connect(Form.exit_pane)
        self.Submit_btn.clicked.connect(Form.subimit)
        self.Stop_btn.clicked.connect(Form.stop_pane)
        self.MARKET_SMALL_LE.textChanged.connect(Form.enable_register_btn)
        self.TRADING_SENSITIVITY_LE.textChanged.connect(Form.enable_register_btn)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.Submit_btn.setText(QCoreApplication.translate("Form", u"\u63d0\u4ea4", None))
        self.MARKET_SMALL_LE.setText(QCoreApplication.translate("Form", u"0.05", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"\u884c\u60c5\u4ee3\u7801", None))
        self.Stop_btn.setText(QCoreApplication.translate("Form", u"\u6e05\u9664", None))
        self.TRADING_NUM_LE.setText(QCoreApplication.translate("Form", u"9696", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"\u6700\u5c0f\u53d8\u52a8", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"\u654f\u611f\u5ea6", None))
        self.TRADING_SECURITY_LE.setText(QCoreApplication.translate("Form", u"65101", None))
        self.Exit_btn.setText(QCoreApplication.translate("Form", u"\u9000\u51fa", None))
        self.MARKET_SECURITY_LE.setText(QCoreApplication.translate("Form", u"HSImain", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"\u7ecf\u7eaa\u53f7", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"\u4ea4\u6613\u4ee3\u7801", None))
        self.TRADING_SENSITIVITY_LE.setText(QCoreApplication.translate("Form", u"9696", None))
    # retranslateUi

