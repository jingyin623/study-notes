"""
    记录及预测跳价点
"""
import queue
import time

from futu import *
import logging
from trading_src.PyQt5_Trading_GetsJumpPoint.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口

TRADING_SECURITY_THREAD_DICT = {}       # 线程的相关新参数信息
TRADING_SECURITY_THREAD_DICT_RUN = {}   # 正在运行的线程字典
FORECAST_LIST_ALL_DICT = {}             # 展示用的原始数据

SUBSCRIBE_DICT_LIST = []                # 订阅信息 的展示列表
FORECAST_LIST_ALL = []                  # 数据展示列表

# 线程方法
def framework_thread(market_security, market_small, trading_security, trading_num, trading_sensitivity, method_queue, exit_flag, add_forecast_list):
    """
    :param market_security:     行情代码
    :param market_small:        市场的最小变动价格
    :param trading_security:    交易代码
    :param trading_num:         交易经济好
    :param trading_sensitivity: 交易代码的敏感度
    :param method_queue:        线程队列
    :param exit_flag:           线程退出标志
    :param add_forecast_list:   外部调用线程
    :return:
    """
    MARKET_SMALL = float(market_small)                  # 最小波动值
    TRADING_SENSITIVITY = 1/float(trading_sensitivity)  # 波动率
    IMMOBILIZATION_SET = {}                             # 全局集合
    PUSH_PRICE_LIST = []                                # 临时价格列表列表
    FORECAST_LIST = []                                  # 预测列表
    PRESENT = 0                                         # 所有监控目标的临时价格
    WRT_TYPE = ''                                       # 交易方向
    quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象

    ############################ 填充以下函数来完成您的策略 ############################
    #   获取快照
    def get_market_snapshot(trading_security):
        nonlocal WRT_TYPE
        ret, data = quote_context.get_market_snapshot([trading_security])
        if ret == RET_OK:
            wrt_valid = data['wrt_valid'][0]    # bool是否是涡轮
            if wrt_valid:
                WRT_TYPE = data['wrt_type'][0]  # 涡轮方向
        else:
            logger.error('error:', data)

    # 初始化字典 备用列表
    def initialization_immobilization_set():
        get_market_snapshot(trading_security)
        num = 0
        while num <= 250:
            IMMOBILIZATION_SET[round((num * 0.001), 3)] = [-1, -1, -1, -1, -1]
            num = num + 1

    def modify_trading_sensitivity(trading_sensitivity, num, pull_percentage, market_small):
        """

        :param trading_sensitivity:     波动率
        :param num:                     增加或者减少价格
        :param pull_percentage:         行情百分比
        :param market_small:            行情的最小变动
        :return: 得到增加后者减少的 整数位和百分比
        """
        integer_part = int(trading_sensitivity * num)               # 相关价格变动的整数部分
        fractional_part = round((abs(trading_sensitivity * num) - abs(integer_part)), 2)  # 相关变动的分数部分
        # 说明不够减 integer_part - 1
        if pull_percentage + fractional_part >= 1:
            # 付价格
            if integer_part < 0:
                integer_part = integer_part - 1
            if integer_part > 0:
                integer_part = integer_part + 1
            fractional_part = (pull_percentage + fractional_part) - 1
        # 在0到1 百分比改变
        elif pull_percentage + fractional_part < 1:
            fractional_part = pull_percentage + fractional_part
        return round(integer_part * market_small, 3), round(fractional_part, 2)

    def modify_immobilization_set(price, pull_mark_price, pull_percentage, wrt_type, up_or_down):
        """
        :param price:               涡轮的推送价格
        :param pull_mark_price:     成交实时行情的价格
        :param pull_percentage:     成交实时行情的百分比
        :param wrt_type:            涡轮的类型
        :param up_or_down:          成交的方向
        :return: 无
        """
        PUSH_PRICE_LIST.clear()
        if price <= 0.250:
            # 判断是买入还是卖出
            if up_or_down == 'up':
                num = -1  # 计数器
                while num <= 1:
                    # 得到需要增加或者减少的整数，和分数部分
                    integer_part, fractional_part = modify_trading_sensitivity(TRADING_SENSITIVITY, num, pull_percentage, MARKET_SMALL)

                    # 涡轮价格
                    IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][0] = round(
                        price + (num * 0.001), 3)
                    if wrt_type == 'BULL' or wrt_type == 'CALL':
                        IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][1] = round(
                            (pull_mark_price + integer_part), 3)
                    elif wrt_type == 'BEAR' or wrt_type == 'PUT':
                        IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][1] = round(
                            (pull_mark_price - integer_part), 3)
                    IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][2] = fractional_part
                    PUSH_PRICE_LIST.append(round((price + num * 0.001), 3))
                    num = num + 1
            if up_or_down == 'down':
                num = -1  # 计数器
                while num <= 1:
                    # 得到增加或者减少的整数部分和百分比integer_part,百分比fractional_part
                    integer_part, fractional_part = modify_trading_sensitivity(TRADING_SENSITIVITY, num, pull_percentage, MARKET_SMALL)
                    # 涡轮价格
                    IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][0] = round(
                        price + (num * 0.001), 3)
                    if wrt_type == 'BULL' or wrt_type == 'CALL':
                        IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][3] = round(
                            (pull_mark_price + integer_part), 3)
                    elif wrt_type == 'BEAR' or wrt_type == 'PUT':
                        IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][3] = round(
                            (pull_mark_price - integer_part), 3)
                    IMMOBILIZATION_SET[round(price + (num * 0.001), 3)][4] = fractional_part
                    PUSH_PRICE_LIST.append(round((price + num * 0.001), 3))
                    num = num + 1
        # 打印相关信息
        pull_print_list(PUSH_PRICE_LIST)

    # 打印列表
    def pull_print_list(push_price_list):
        # 清除列表数据
        FORECAST_LIST.clear()
        FORECAST_LIST.append(trading_security)
        # 遍历所有相关价格
        for key in push_price_list:
            # 集合中没有相关价格 添加相关价格
            if IMMOBILIZATION_SET.get(key) is None:
                FORECAST_LIST.append(str(key))
            # 集合中有相关价格 添加相关记录值
            else:
                FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key))))  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
        # 调用外部方法 并吧数据送出
        add_forecast_list(FORECAST_LIST)

    def pull_the_market_security(market_security, warrants_call_put):
        """
        根据涡轮类型获得正股价格和计算买卖价格的百分比
        :param market_security: 正股代码
        :param warrants_call_put:   涡轮的类型
        :return: pull_price, pull_percentage
                如果涡轮是牛返回的是[买盘价格，和买盘占比]
                如果涡轮是熊返回的是[卖盘价格，和卖占比]
                如果没有数据返回 0,0
        """
        ret, data = quote_context.get_order_book(market_security, num=1)  # 获取一次 1 档实时摆盘数据
        pull_price = 0
        pull_percentage = 0
        if ret == RET_OK:
            if len(data['Bid']) != 0:
                if warrants_call_put == 'BULL' or warrants_call_put == 'CALL':
                    pull_price = data['Bid'][0][0]
                    pull_percentage = round(data['Bid'][0][1] / (data['Bid'][0][1] + data['Ask'][0][1]), 2)
                elif warrants_call_put == 'BEAR' or warrants_call_put == 'PUT':
                    pull_price = data['Ask'][0][0]
                    pull_percentage = round(data['Ask'][0][1] / (data['Ask'][0][1] + data['Bid'][0][1]), 2)
        else:
            logger.error('获得正股价格和百分比失败error:{}'.format(data))
        return pull_price, pull_percentage

    # 返回目标经纪号所在的价格
    def find_order_price(push_code, trading_num, bid):
        ret, bid_frame_table, ask_frame_table = quote_context.get_broker_queue(push_code)  # 获取一次经纪队列数据
        if ret == RET_OK:
            pos = 0
            for indexs in bid_frame_table.index:
                bid_broker_id = bid_frame_table.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
                bid_broker_pos = bid_frame_table.at[indexs, 'bid_broker_pos']  # 经纪档位
                if bid_broker_id == int(trading_num):
                    pos = bid_broker_pos  # 经纪号所在得档位
                    break
            # 返回目标经济号所在价格
            if pos != 0:
                bid_price = bid[pos - 1][0]
            # 没有找到相关经纪号信息
            else:
                bid_price = 0
            return bid_price
        else:
            logger.error('error:', bid_frame_table)

    # 每次产生数据变化运行一次，返回买卖信号可将策略的主要逻辑写在此处
    def on_bar_open(data):
        nonlocal PRESENT  # 当前价格记录器
        nonlocal IMMOBILIZATION_SET  # 全局字典
        push_code = data['code']  # 推送的代码
        # 找到交易标的
        if push_code == trading_security:
            # 找到目标经纪号所在的价格（代码，经纪号，所有买盘数据）
            push_price = find_order_price(push_code, trading_num, data['Bid'])
            # 推送价格大于价格记录器（庄家买入）
            if push_price > PRESENT:
                time.sleep(1.5)
                ret, testdata = quote_context.get_order_book(push_code, num=10)  # 获取一次 10 档实时摆盘数据
                testpush_price = find_order_price(push_code, trading_num, testdata['Bid'])
                # print(f'testpush_price{testpush_price}, push_price{push_price}')
                if testpush_price == push_price:
                    # 拉取一次行情数据，行情第一档得价格和百分比类型list
                    pull_mark_price, pull_percentage = pull_the_market_security(market_security, WRT_TYPE)
                    if pull_mark_price != 0:
                        # 全局集合中有相关元素， 修改相关元素
                        # 修改字典相关数据
                        modify_immobilization_set(push_price, pull_mark_price, pull_percentage, WRT_TYPE, 'up')
                    PRESENT = push_price  # 更新价格记录器
            # 推送价格小于价格记录器（庄家买入）
            elif push_price < PRESENT:
                # 延迟1秒时间后判断庄家最新状态和价格
                time.sleep(1.5)
                ret, testdata = quote_context.get_order_book(push_code, num=10)  # 获取一次 10 档实时摆盘数据
                testpush_price = find_order_price(push_code, trading_num, testdata['Bid'])
                # print(f'testpush_price{testpush_price}, push_price{push_price}')
                if testpush_price == push_price:
                    # 拉取一次行情数据，行情第一档得价格和百分比类型list
                    pull_mark_price, pull_percentage = pull_the_market_security(market_security, WRT_TYPE)
                    if pull_mark_price != 0:
                        # 全局集合中有相关元素， 修改相关元素
                        # 修改字典相关数据
                        modify_immobilization_set(PRESENT, pull_mark_price, pull_percentage, WRT_TYPE, 'up')
                        modify_immobilization_set(PRESENT, pull_mark_price, pull_percentage, WRT_TYPE, 'down')
                    PRESENT = push_price  # 更新价格记录器
                # 推送价格等于价格记录器（庄家在原地没动的时候）
            elif push_price == PRESENT:
                pass
    ################################ 框架实现部分，可忽略不看 ###############################
    # 摆盘回调
    class OrderBookTest(OrderBookHandlerBase):
        def on_recv_rsp(self, rsp_pb):
            ret_code, data = super(OrderBookTest,self).on_recv_rsp(rsp_pb)
            if ret_code != RET_OK:
                print("OrderBookTest: error, msg: %s" % data)
                return RET_ERROR, data
            on_bar_open(data)
            return RET_OK, data

    # 经纪队列回调
    class BrokerTest(BrokerHandlerBase):
        def on_recv_rsp(self, rsp_pb):
            ret_code, err_or_stock_code, data = super(BrokerTest, self).on_recv_rsp(rsp_pb)
            if ret_code != RET_OK:
                print("BrokerTest: error, msg: {}".format(err_or_stock_code))
                return RET_ERROR, data
            pass
            return RET_OK, data

    ################################ 外部调用 ###############################
    def quote_context_close():
        quote_context.close()

    # 初始化字典和列表
    initialization_immobilization_set()
    # 设置回调
    quote_context.set_handler(OrderBookTest())  # 摆盘回调
    quote_context.set_handler(BrokerTest())     # 经纪队列回调
    # 订阅标的合约的 摆盘，以便获取数据
    ret_sub, err_message = quote_context.subscribe([market_security, trading_security], [SubType.ORDER_BOOK, SubType.BROKER])
    # 先订阅了 QUOTE 和 TICKER 两个类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        logger.info('subscribe successfully！current subscription status :{}'.format(quote_context.query_subscription())) # 订阅成功后查询订阅状态
    else:
        logger.error('subscription failed'.format(err_message))

    # 在线程内部执行方法
    while not exit_flag.is_set():
        try:
            method_name = method_queue.get(timeout=1)
            if method_name == 'quote_context_close':
                quote_context_close()
        except queue.Empty:
            pass

################################ 外部调用 ###############################
def add_code(market_security, market_small, trading_security, trading_num, trading_sensitivity):
    trading_security_list = [market_security, market_small, trading_security, trading_num, trading_sensitivity]
    # 如果线程信息在 字典中 说明启动了字典,
    if trading_security in TRADING_SECURITY_THREAD_DICT_RUN:
        # 线程参数是否修改,没有在说明修改
        if trading_security_list not in TRADING_SECURITY_THREAD_DICT[trading_security]:
            # 删除线程或停止线程
            TRADING_SECURITY_THREAD_DICT_RUN[trading_security][0].put('quote_context_close')
            TRADING_SECURITY_THREAD_DICT_RUN[trading_security][1].set()
            # del TRADING_SECURITY_THREAD_DICT_RUN[trading_security]
            remove_code(trading_security)
            # 启动新线程
            trading_security_queue = queue.Queue()
            # 创建一个标志位用于通知线程退出
            exit_flag = threading.Event()
            trading_security_run = threading.Thread(target=framework_thread, args=(
            market_security, market_small, trading_security, trading_num, trading_sensitivity, trading_security_queue, exit_flag, add_forecast_list))
            trading_security_run.start()
            # 添加新的线程系信息和保存进程
            TRADING_SECURITY_THREAD_DICT[trading_security] = trading_security_list
            TRADING_SECURITY_THREAD_DICT_RUN[trading_security] = [trading_security_queue, exit_flag]
    else:
        # 启动新线程
        trading_security_queue = queue.Queue()
        # 创建一个标志位用于通知线程退出
        exit_flag = threading.Event()
        trading_security_run = threading.Thread(target=framework_thread, args=(
            market_security, market_small, trading_security, trading_num, trading_sensitivity, trading_security_queue,
            exit_flag, add_forecast_list))
        trading_security_run.start()
        # 添加新的线程系信息和保存进程
        TRADING_SECURITY_THREAD_DICT[trading_security] = trading_security_list
        TRADING_SECURITY_THREAD_DICT_RUN[trading_security] = [trading_security_queue, exit_flag]
    update_subscribe_dict_list()

# 有参数删除相关代码 没有参数关闭所有进程
def quote_context_close(code=None):
    if code is not None:
        TRADING_SECURITY_THREAD_DICT_RUN[code][0].put('quote_context_close')
        TRADING_SECURITY_THREAD_DICT_RUN[code][1].set()
    else:
        save_code()
        for stop in TRADING_SECURITY_THREAD_DICT_RUN.values():
            stop[0].put('quote_context_close')
            stop[1].set()

    # 遍历所有key 得展示列表
def update_subscribe_dict_list():
    FORECAST_LIST_ALL.clear()
    SUBSCRIBE_DICT_LIST.clear()
    key_list = []   # 顺序列表
    for value in TRADING_SECURITY_THREAD_DICT.values():
        add_value = ' '.join(map(str, [value[2], value[4]]))
        SUBSCRIBE_DICT_LIST.append(add_value)
        key_list.append(value[2])
    for key in key_list:
        if key in FORECAST_LIST_ALL_DICT:
            value = FORECAST_LIST_ALL_DICT[key]
            for x in value:
                FORECAST_LIST_ALL.append(str(x))

    # 删除相关代码原始数据 并停止相关的进程
def remove_code(code):
    if code in TRADING_SECURITY_THREAD_DICT:
        TRADING_SECURITY_THREAD_DICT_RUN[code][0].put('quote_context_close')
        TRADING_SECURITY_THREAD_DICT_RUN[code][1].set()
        del TRADING_SECURITY_THREAD_DICT[code]
        del TRADING_SECURITY_THREAD_DICT_RUN[code]
    if code in FORECAST_LIST_ALL_DICT.keys():
        del FORECAST_LIST_ALL_DICT[code]
    update_subscribe_dict_list()

    # 线程内部 需要调用的方法 原始数据,并转换成先用列表
def add_forecast_list(data):
    global FORECAST_LIST_ALL
    FORECAST_LIST_ALL.clear()
    if data[0] in FORECAST_LIST_ALL_DICT:
        if data not in FORECAST_LIST_ALL_DICT[data[0]]:
            FORECAST_LIST_ALL_DICT[data[0]] = data
    else:
        FORECAST_LIST_ALL_DICT[data[0]] = data
    update_subscribe_dict_list()

def get_trading_security_thread(data):
    data_list = TRADING_SECURITY_THREAD_DICT[data]
    return data_list

def save_code():
    filename = 'data.json'
    # 将字典保存为文件
    with open(filename, 'w') as file:
        json.dump(TRADING_SECURITY_THREAD_DICT, file)

def load_code():
    global TRADING_SECURITY_THREAD_DICT
    filename = 'data.json'
    if not os.path.exists(filename):
        # 文件不存在，创建文件
        with open(filename, 'w') as file:
            json.dump({}, file)
    # 读取文件内容
    with open(filename, 'r') as file:
        TRADING_SECURITY_THREAD_DICT = json.load(file)
    for key, value in TRADING_SECURITY_THREAD_DICT.items():
        add_code(value[0], value[1], value[2], value[3], value[4])


