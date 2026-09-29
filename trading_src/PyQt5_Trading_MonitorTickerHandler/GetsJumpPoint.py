"""
    记录及预测跳价点
"""

from futu import *
import logging
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口

IMMOBILIZATION_SET = {}    # 全局集合
LIST_OF_ELEMENTS = [-1, -1, -1, -1, -1]   # 临时数据列表
PUSH_PRICE_LIST = []    # 临时价格列表列表
FORECAST_LIST = []  # 预测列表
PRESENT = 0         # 当前价格记录器
WRT_TYPE = ''       # 交易方向

MARKET_SECURITY = 'HK.HSImain'  # 标的参考代码
TRADING_SECURITY = 'HK.57067'  # 交易标的
TRADING_NUM = '9692'    # 交易目标经纪号


quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象


############################ 填充以下函数来完成您的策略 ############################

#   获取快照
def get_market_snapshot(trading_security):
    global WRT_TYPE
    ret, data = quote_context.get_market_snapshot([trading_security])
    if ret == RET_OK:
        wrt_valid = data['wrt_valid'][0]    # bool是否是涡轮
        if wrt_valid:
            WRT_TYPE = data['wrt_type'][0]  # 涡轮方向
    else:
        logger.error('error:', data)

# 初始化字典 备用列表
def initialization_immobilization_set():
    get_market_snapshot(TRADING_SECURITY)
    global LIST_OF_ELEMENTS
    num = 0
    while num <= 250:
        IMMOBILIZATION_SET[round((num * 0.001), 3)] = [-1, -1, -1]
        num = num + 1

# 预测值 并显示相关信息
def modify_immobilization_set(push_set_price, call_or_put):
    PUSH_PRICE_LIST.clear()
    if push_set_price[0] <= 0.250:
        num = -2  # 计数器
        while num <= 2:
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][0] = round(push_set_price[0] + (num * 0.001), 3)
            if call_or_put == 'BULL' or call_or_put == 'CALL':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1] + (num * 10), 3)
            elif call_or_put == 'BEAR' or call_or_put == 'PUT':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1] - (num * 10), 3)
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][2] = push_set_price[2]
            PUSH_PRICE_LIST.append(round((push_set_price[0] + num * 0.001), 3))
            num = num + 1
    # 打印相关信息
    pull_print_list(PUSH_PRICE_LIST, push_set_price)

# 打印列表
def pull_print_list(push_price_list, push_set_price):
    # 清除列表数据
    FORECAST_LIST.clear()
    # #   遍历所有相关价格
    for key in push_price_list:
    #     # 集合中没有相关价格 添加相关价格
        if IMMOBILIZATION_SET.get(key) == None:
            # FORECAST_LIST.append('<p>' + str(key) + "</p>\n")
            FORECAST_LIST.append(str(key))
            # FORECAST_LIST.append('Hello PyQt5!\n单击按钮')

    #     # # 集合中有相关价格 添加相关记录值
        else:
            # FORECAST_LIST.append('<p>' + str(IMMOBILIZATION_SET.get(key)) + '</p>')
            FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key))))  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
    print("增加的代码:\033[1;30;41m" + str(push_set_price) + "\033[0m")
    print(FORECAST_LIST)


# 拉取一次行情
def pull_the_market_security(market_security, call_or_put):
    ret, data = quote_context.get_order_book(market_security, num=1)  # 获取一次 1 档实时摆盘数据
    if ret == RET_OK:
        bid_list = []
        if call_or_put == 'BULL' or call_or_put == 'CALL':
            bid_price = data['Bid'][0][0]
            price_percent = int(round(data['Bid'][0][1] / (data['Bid'][0][1] + data['Ask'][0][1]), 2) * 100)
        elif call_or_put == 'BEAR' or call_or_put == 'PUT':
            bid_price = data['Ask'][0][0]
            price_percent = int(round(data['Ask'][0][1] / (data['Ask'][0][1] + data['Bid'][0][1]), 2) * 100)
        bid_list.append(bid_price)
        bid_list.append(price_percent)
    else:
        logger.error('error:', data)
    return bid_list


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
    global PRESENT      # 当前价格记录器
    global IMMOBILIZATION_SET  # 全局字典
    push_code = data['code']  # 推送的代码
    # 找到行情标的
    if push_code == MARKET_SECURITY:
        # if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
        # 记录数据以备分析
        logger.info(data['code'] + '--' + str(data['Bid'][0][0]) + '--' + str(data['Ask'][0][0]) + '--' + data['svr_recv_time_bid'] + '--' + data['svr_recv_time_ask'])
    # 找到交易标的
    if push_code == TRADING_SECURITY:
        # 找到目标经纪号所在的价格（代码，经纪号，所有买盘数据）
        push_price = find_order_price(push_code, TRADING_NUM, data['Bid'])
        # 推送价格大于价格记录器（庄家买入）
        if push_price > PRESENT:
            # 记录数据以备分析
            logger.info(push_code + '--' + str(push_price))
            PRESENT = push_price  # 更新价格记录器
        # 推送价格小于价格记录器（庄家买入）
        elif push_price < PRESENT:
            # 记录数据以备分析
            logger.info(push_code + '--' + str(push_price))
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 全局集合中有相关元素， 修改相关元素
            LIST_OF_ELEMENTS[0] = PRESENT  # 庄家吃入价格
            LIST_OF_ELEMENTS[1] = pull_the_market[0]  # 庄家吃入时 行情的价格
            LIST_OF_ELEMENTS[2] = pull_the_market[1]  # 庄家吃入时 行情的百分比
            # 修改字典相关数据
            modify_immobilization_set(LIST_OF_ELEMENTS, WRT_TYPE)
            PRESENT = push_price  # 更新价格记录器
        # 推送价格等于0（庄家不在的时候）
        elif push_price == 0:
            pass
        # 推送价格等于价格记录器（庄家在原地没动的时候）
        elif push_price == PRESENT:
            pass



################################ 框架实现部分，可忽略不看 ###############################
class OrderBookClass(OrderBookHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookClass, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error("OrderBookTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open(data)
        return RET_OK, data


################################ 外部调用 ###############################
def submit_run(market_security, trading_security_le, trading_num):
    global MARKET_SECURITY
    global TRADING_SECURITY
    global TRADING_NUM
    MARKET_SECURITY = market_security       # 标的参考代码
    TRADING_SECURITY = trading_security_le  # 交易标的
    TRADING_NUM = trading_num               # 交易目标经纪号
    # 初始化字典和列表
    initialization_immobilization_set()
    # 设置回调
    quote_context.set_handler(OrderBookClass())   # 摆盘回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])

def quote_context_stop():
    quote_context.unsubscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])

def quote_context_close():
    quote_context.unsubscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
    quote_context.close()


# 主函数
if __name__ == '__main__':
    # 初始化字典和列表
    initialization_immobilization_set()
    # 设置回调
    quote_context.set_handler(OrderBookClass())   # 摆盘回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
