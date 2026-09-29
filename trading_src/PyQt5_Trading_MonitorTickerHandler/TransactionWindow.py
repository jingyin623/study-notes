"""
    记录及预测跳价点
"""

from futu import *

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口
IMMOBILIZATION_SET = {}    # 全局集合
FORECAST_LIST = []  # 预测列表
FORECAST_VALUE = 0     # 预测值
SHARE_PRICE = 0     # 当前价格记录器

MARKET_SECURITY = 'HK.HSImain'  # 标的参考代码
TRADING_SECURITY = 'HK.65101'  # 交易标的
CALL_OR_PUT = 0  # 交易标的
TRADING_NUM = '9696'    # 交易目标经纪号


quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象


############################ 填充以下函数来完成您的策略 ############################
# 打印列表
def pull_print_list(push_price, push_set_price):
    # 清除列表数据
    FORECAST_LIST.clear()
    # #   遍历所有相关价格
    for key in push_price:
    #     # 集合中没有相关价格 添加相关价格
        if IMMOBILIZATION_SET.get(key) == None:
            # FORECAST_LIST.append('<p>' + str(key) + "</p>\n")
            FORECAST_LIST.append(str(key))
            # FORECAST_LIST.append('Hello PyQt5!\n单击按钮')

    #     # # 集合中有相关价格 添加相关记录值
        else:
            # FORECAST_LIST.append('<p>' + str(IMMOBILIZATION_SET.get(key)) + '</p>')
            FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key)))) # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
    print("增加的代码:\033[1;30;41m" + str(push_set_price) + "\033[0m")
    print(FORECAST_LIST)
    # print(IMMOBILIZATION_SET)


# 拉取一次行情
def pull_the_market_security(market_security):
    global CALL_OR_PUT  # 涡轮方向
    ret, data = quote_context.get_order_book(market_security, num=1)  # 获取一次 1 档实时摆盘数据
    if ret == RET_OK:
        bid_list = []
        if CALL_OR_PUT == 0:
            bid_price = data['Bid'][0][0]
            price_percent = int(round(data['Bid'][0][1] / (data['Bid'][0][1] + data['Ask'][0][1]), 2) * 100)
        elif CALL_OR_PUT == 1:
            bid_price = data['Ask'][0][0]
            price_percent = int(round(data['Ask'][0][1] / (data['Ask'][0][1] + data['Bid'][0][1]), 2) * 100)
        bid_list.append(bid_price)
        bid_list.append(price_percent)
    else:
        print('error:', data)
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
        print('error:', bid_frame_table)


# 每次产生数据变化运行一次，返回买卖信号可将策略的主要逻辑写在此处
def on_bar_open(data):
    global SHARE_PRICE  # 当前价格记录器
    global IMMOBILIZATION_SET  # 全局列表
    push_code = data['code']  # 推送的代码
    # 找到交易标的
    if push_code == TRADING_SECURITY:
        # 认购轮准备显示列表数据 买盘3和卖盘2数据
        push_price_list = []
        push_price_list.append(data['Bid'][2][0])
        push_price_list.append(data['Bid'][1][0])
        push_price_list.append(data['Bid'][0][0])
        push_price_list.append(data['Ask'][0][0])
        push_price_list.append(data['Ask'][1][0])
        push_price = find_order_price(push_code, TRADING_NUM, data['Bid'])  # 找到目标经纪号所在的价格（代码，经纪号，所有买盘数据）
        # 推送价格大于价格记录器
        if push_price > BID_GET_SHARE_PRICE:
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY)
            # 全局中没有相关价格元素 ，新增相关价格元素
            if IMMOBILIZATION_SET.get(push_price) == None:
                list_of_elements = []  # 元素列表,只有5个值
                list_of_elements.append(push_price)
                list_of_elements.extend(pull_the_market)    # 庄家吃入时 行情的价格和百分比
                list_of_elements.extend(pull_the_market)    # 庄家撤退时 行情的价格和百分比
                IMMOBILIZATION_SET[push_price] = list_of_elements
                pull_print_list(push_price_list, IMMOBILIZATION_SET[push_price])     # 显示相关信息
            # 全局集合中有相关元素， 修改相关元素
            else:
                IMMOBILIZATION_SET[push_price][1] = pull_the_market[0]     # 庄家吃入时 行情的价格
                IMMOBILIZATION_SET[push_price][2] = pull_the_market[1]     # 庄家吃入时 行情的百分比
                pull_print_list(push_price_list, IMMOBILIZATION_SET[push_price])     # 显示相关信息
            BID_GET_SHARE_PRICE = push_price    # 更新价格记录器

        # 推送价格小于价格记录器 庄家撤退时的操作
        elif 0 < push_price < BID_GET_SHARE_PRICE:
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY)
            # 全局中没有相关价格元素 ，新增相关价格元素
            if IMMOBILIZATION_SET.get(push_price) == None:
                list_of_elements = []  # 元素列表,只有5个值
                list_of_elements.append(push_price)
                list_of_elements.extend(pull_the_market)  # 庄家吃入时 行情的价格和百分比
                list_of_elements.extend(pull_the_market)  # 庄家撤退时 行情的价格和百分比
                IMMOBILIZATION_SET[push_price] = list_of_elements
                pull_print_list(push_price_list, IMMOBILIZATION_SET[push_price])     # 显示相关信息

            # 全局集合中有相关元素， 修改相关元素
            else:
                IMMOBILIZATION_SET[BID_GET_SHARE_PRICE][3] = pull_the_market[0]  # 庄家撤退时 行情的价格
                IMMOBILIZATION_SET[BID_GET_SHARE_PRICE][4] = pull_the_market[1]  # 庄家撤退时 行情的百分比
                pull_print_list(push_price_list, IMMOBILIZATION_SET[push_price])     # 显示相关信息
            BID_GET_SHARE_PRICE = push_price  # 更新价格记录器

        # 庄家不在的时候
        elif push_price == 0:
            pass
        # 庄家在原地没动的时候
        elif push_price == BID_GET_SHARE_PRICE:
            pass


################################ 框架实现部分，可忽略不看 ###############################
class OrderBookClass(OrderBookHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookClass, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("OrderBookTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open(data)
        return RET_OK, data


################################ 外部调用 ###############################
def quote_context_close():
    quote_context.close()

def quote_context_stop():
    quote_context.stop()


def submit_run(market_security, trading_security_le, trading_num, call_or_put):
    global MARKET_SECURITY
    global TRADING_SECURITY
    global TRADING_NUM
    MARKET_SECURITY = 'HK.' + market_security       # 标的参考代码
    TRADING_SECURITY = 'HK.' + trading_security_le  # 交易标的
    TRADING_NUM = trading_num               # 交易目标经纪号
    # 设置回调
    quote_context.set_handler(OrderBookClass())   # 摆盘回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
    quote_context.start()

# 主函数
if __name__ == '__main__':
    # 设置回调
    quote_context.set_handler(OrderBookClass())   # 摆盘回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
