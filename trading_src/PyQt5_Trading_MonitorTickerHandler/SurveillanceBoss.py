# -*- coding: utf-8 -*-

import time

import winsound
import pyttsx3
from futu import *
import logging
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口

SUBSCRIBE_DICT = {}         # 订阅信息
TRIGGER_LIST = []           # 触发列表
SUBSCRIBE_DICT_LIST = []    # 订阅信息 的展示列表


CODE = ''
POSITION = 0
DIRECTION = '0'

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象
################################ 内部调用 ###############################
# 朗读线程
def text_to_speech(text):
    words = text.split()  # 将字符串按空格分割成单词列表
    split_numbers = [digit for digit in words[0]]
    joined_numbers = ' '.join(split_numbers) + ' ' + words[1][:-3] + ' K ' + words[2]

    # 初始化 pyttsx3 引擎，并设置使用 Microsoft-SAPI 音色
    engine = pyttsx3.init('sapi5')
    # 获取系统中可用的所有音色列表，可以通过修改引号内的值来切换不同的语音
    # voices = engine.getProperty('voices')
    # engine.setProperty('voice', voices[0].id) # voices[1] 代表 Microsoft-SAPI 音色

    engine.setProperty('rate', 150)  # 设置语速
    engine.say(joined_numbers)
    engine.runAndWait()
# 提示音与朗读
def error_beep(freq, duration, text):
    for i in range(1): winsound.Beep(freq, duration)
    # 创建朗读线程并启动
    text_to_speech_thread = threading.Thread(target=text_to_speech, args=(text,))
    text_to_speech_thread.start()

def trigger_list_add(text):
    TRIGGER_LIST.append(text)
    time.sleep(10)
    TRIGGER_LIST.remove(text)

# 提示方法
def trigger(data):
    logger.info(data)
    data = (' '.join(map(str, data)))[3:]
    # 创建线程并启动 TRIGGER_LIST添加数据
    beep_thread = threading.Thread(target=trigger_list_add, args=(data,))
    beep_thread.start()
    # 创建线程并启动 声音提示线程
    beep_thread = threading.Thread(target=error_beep, args=(1000, 500, data))
    beep_thread.start()

# 删除并重新遍历SUBSCRIBE_DICT的所有元素
def update_subscribe_dict_list():
    SUBSCRIBE_DICT_LIST.clear()
    for values_list in SUBSCRIBE_DICT.values():
        for value in values_list:
            add_value = (' '.join(map(str, value)))[3:]
            SUBSCRIBE_DICT_LIST.append(add_value)

def add_code_list(codeList):
    # 查询代码是否在字典中
    code = codeList[0]
    # 1 字典中没有相关键
    if code not in SUBSCRIBE_DICT:
        SUBSCRIBE_DICT[code] = [codeList]
        logger.info('字典中没有相关代码,增加相关数据:{}'.format(codeList))
    # 2 字典中有相关键 但是没有相关值
    elif codeList not in SUBSCRIBE_DICT[code]:
        SUBSCRIBE_DICT[code].append(codeList)
        logger.info('字典有相关代码,但是没有相关数据增加数据:{}'.format(codeList))
    update_subscribe_dict_list()
################################ 内部逻辑 ###############################

def on_bar_open(data):
    push_code = data['code'][0]    # 涡轮代码
    volume = data['volume'][0]     # 单笔成交量
    ticker_direction = data['ticker_direction'][0]
    if push_code in SUBSCRIBE_DICT:
        push_data = [push_code, volume, ticker_direction]
        if push_data in SUBSCRIBE_DICT[push_code]:
            trigger(push_data)

################################ 实现框架 ###############################
class TickerTest(TickerHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(TickerTest, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error("TickerTest: error, msg: {}".format(data))
            return RET_ERROR, data
        on_bar_open(data)
        return RET_OK, data

################################ 外部调用 ###############################
def add_code(market_security, trading_security, trading_num):
    global CODE
    global POSITION
    global DIRECTION
    CODE = market_security       # 涡轮代码
    POSITION = float(trading_security)  # 仓位
    # 订阅标的合约的 摆盘，以便获取数据
    ret_sub, err_message = quote_context.subscribe([CODE], [SubType.TICKER])
    # 先订阅了 QUOTE 和 TICKER 两个类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        logger.info('subscribe successfully！current subscription status :{}'.format(quote_context.query_subscription())) # 订阅成功后查询订阅状态
        add_list1 = [CODE, POSITION, 'BUY']
        add_list2 = [CODE, POSITION, 'SELL']

        if trading_num == '-1':
            # 字典增加方法
            add_code_list(add_list1)
            add_code_list(add_list2)
        elif trading_num == '0':
            add_code_list(add_list1)
        elif trading_num == '1':
            add_code_list(add_list2)
    else:
        logger.error('subscription failed'.format(err_message))

def remove_code(remove_list):
    if remove_list[0] in SUBSCRIBE_DICT:
        if remove_list in SUBSCRIBE_DICT[remove_list[0]]:
            SUBSCRIBE_DICT[remove_list[0]].remove(remove_list)
            logger.info('删除相关数据:{}'.format(remove_list))
            # 删除后如果该键下面没有元素 删除该键,并取消订阅
            if remove_list[0] in SUBSCRIBE_DICT and not SUBSCRIBE_DICT[remove_list[0]]:
                del SUBSCRIBE_DICT[remove_list[0]]
                logger.info('删除相关数据,相关数据清空,清楚代码:{}'.format(remove_list))
                # 反订阅
                ret_unsub, err_message_unsub = quote_context.unsubscribe([remove_list[0]], [SubType.QUOTE])
                if ret_unsub == RET_OK:
                    logger.info('unsubscribe successfully！current subscription status:'.format(quote_context.query_subscription()))  # 取消订阅后查询订阅状态
                else:
                    logger.error('unsubscription failed！'.format(err_message_unsub))
            update_subscribe_dict_list()


def save_code():
    filename = 'data.json'
    # 将字典保存为文件
    with open(filename, 'w') as file:
        json.dump(SUBSCRIBE_DICT, file)

def load_code():
    global SUBSCRIBE_DICT
    filename = 'data.json'
    if not os.path.exists(filename):
        # 文件不存在，创建文件
        with open(filename, 'w') as file:
            json.dump({}, file)

    # 读取文件内容
    with open(filename, 'r') as file:
        SUBSCRIBE_DICT = json.load(file)
    # 拿到所有的订阅目标
    keys = list(SUBSCRIBE_DICT.keys())
    quote_context.set_handler(TickerTest())   # 摆盘回调
    # 订阅标的合约的 摆盘，以便获取数据
    ret_sub, err_message = quote_context.subscribe(keys, [SubType.TICKER])
    # 先订阅了 QUOTE 和 TICKER 两个类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        logger.info('subscribe successfully！current subscription status :{}'.format(quote_context.query_subscription())) # 订阅成功后查询订阅状态
    else:
        logger.error('subscription failed'.format(err_message))

    update_subscribe_dict_list()


def quote_context_close():
    # 反订阅
    ret_unsub, err_message_unsub = quote_context.unsubscribe_all()  # 取消所有订阅
    if ret_unsub == RET_OK:
        logger.info('unsubscribe all successfully！current subscription status:{}'.format(quote_context.query_subscription()))  # 取消订阅后查询订阅状态
    else:
        logger.error('Failed to cancel all subscriptions！{}'.format(err_message_unsub))
    # 关闭连接
    quote_context.close()

