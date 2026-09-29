"""
    自动跟踪庄家 接单
    逻辑
    1。确定庄家跳价点
    2. 指定下单 锚点
    3. 分段处理  买入段，休息段，卖出段  3段闭环
    4.锚点 ——买入——卖出——休息——锚点
    5. 买入-处理高档位，低档位订单，上一档位 卖出，及挂单，当前档位无订单无订单买入，（当前档位处理）
    6。卖出-处理高档位所有买单 判定目标档位改单 ，有撤单 。当前档位卖出，及挂单（变动前档位处理）
"""
from futu import *

import logging
from trading_src.PyQt5_Trading_Demo.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口
TRADING_MARKET = TrdMarket.HK  # 交易市场权限，用于筛选对应交易市场权限的账户

TRADING_ENVIRONMENT = TrdEnv.REAL  # 交易环境：真实 / 模拟
IMMOBILIZATION_SET = {}          # 全局集合
PRESENT = 0                      # 记录器
FORECAST_LIST = []               # 显示调用列表
WRT_TYPE = ''                    # 涡轮方向
WRT_CONVERSION_RATIO = 0         # 涡轮理论波动率（换股比例 * 最低价格0.001）
WRT_RATIO = 0                    # 涡轮实际波动率
JUMP_MINIMUM_UNIT = 0.001        # 最小跳价点
TRADING_PWD = '536386'           # 交易密码，用于解锁交易

ORDER_BTN = '0'
MARKET_SECURITY = 'HK.00700'    # 标的参考代码
TRADING_SECURITY = 'HK.68662'    # 交易标的
TRADING_NUM = '9704'             # 交易目标经纪号
ORDER_SIZE = 10                  # 仓位 单位手默认1手
MARKET_PRICE = 0                # 参考价格
PERCENT = 0                     # 百分比
PRICE = 0                       # 价格

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT, security_firm=SecurityFirm.FUTUSECURITIES)  # 交易对象，根据交易品种修改交易对象类型

# 判断交易标的类型 相关信息
def get_market_snapshot():
    global WRT_TYPE
    global WRT_CONVERSION_RATIO
    global WRT_RATIO
    ret, data = quote_context.get_market_snapshot([TRADING_SECURITY])
    if ret == RET_OK:
        wrt_valid = data['wrt_valid'][0]    #bool是否是涡轮
        if wrt_valid:
            WRT_TYPE = data['wrt_type'][0]
            WRT_CONVERSION_RATIO = round(data['wrt_conversion_ratio'][0] * 0.001, 3)
            WRT_RATIO = WRT_CONVERSION_RATIO
            logger.info('正股代码：' + MARKET_SECURITY)
            logger.info('涡轮代码：' + TRADING_SECURITY + ' | 涡轮方向：' + WRT_TYPE + \
                        ' | 目标经纪号：' + TRADING_NUM + ' | 换股比例：' + str(data['wrt_conversion_ratio'][0]))
            logger.info('理论灵敏度 = 换股比率 * 0.001 ' + str(WRT_CONVERSION_RATIO))
            logger.info('实际波动率 ： 默认等于理论灵敏度' + str(WRT_RATIO))
    else:
        logger.error('error:', data)


# 初始化字典 备用列表
def initialization_immobilization_set():
    logger.info("初始化记录值字典默认[-1, -1, -1, '-1', '-1']")
    num = 0
    while num <= 250:
        # [价格，记录值，百分比，订单号，买卖方向]
        IMMOBILIZATION_SET[round((num * 0.001), 3)] = [-1, -1, -1, '-1', '-1']
        num = num + 1


# 预测值 并显示相关信息
def modify_immobilization_set(push_set_price, call_or_put):
    pushPriceList = []
    if push_set_price[0] <= 0.250:
        num = -3  # 计数器
        while num <= 3:
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][0] = round(push_set_price[0] + (num * 0.001), 3)
            if call_or_put == 'BULL' or call_or_put == 'CALL':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1], 3)
            elif call_or_put == 'BEAR' or call_or_put == 'PUT':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1], 3)
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][2] = push_set_price[2]
            num = num + 1
        num = -3
        while num <= 3:
            pushPriceList.append(round((push_set_price[0] + num * 0.001), 3))
            num = num + 1
    # 打印相关信息
    pull_print_list(pushPriceList)


# 打印列表
def pull_print_list(push_price_list):
    # 清除列表数据
    FORECAST_LIST.clear()
    # #   遍历所有相关价格
    for key in push_price_list:
          # 集合中没有相关价格 添加相关价格
        if IMMOBILIZATION_SET.get(key) == None:
            FORECAST_LIST.append(str(key))
        # 集合中有相关价格 添加相关记录值
        else:
            FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key))))  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
    logger.debug(FORECAST_LIST)

# 拉取一次行情
def pull_the_market_security(market_security, warrants_call_put):
    ret, data = quote_context.get_order_book(market_security, num=1)  # 获取一次 1 档实时摆盘数据
    bid_list = []
    if ret == RET_OK:
        if warrants_call_put == 'BULL' or warrants_call_put == 'CALL':
            bid_price = data['Bid'][0][0]
            price_percent = round(data['Bid'][0][1] / (data['Bid'][0][1] + data['Ask'][0][1]), 2)
            bid_list.append(bid_price)
            bid_list.append(price_percent)
        elif warrants_call_put == 'BEAR' or warrants_call_put == 'PUT':
            bid_price = data['Ask'][0][0]
            price_percent = round(data['Ask'][0][1] / (data['Ask'][0][1] + data['Bid'][0][1]), 2)
            bid_list.append(bid_price)
            bid_list.append(price_percent)
        bid_list.append(data['Bid'][0][1])
        bid_list.append(data['Ask'][0][1])
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


# 计算最小下单数量
def small_calculate_quantity(code):
    price_quantity = 0
    # 使用最小交易量
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        logger.error('获取快照失败：', data)
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity


# 判断购买力是否足够
def is_valid_quantity(code, quantity, price):
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        logger.error('获取最大可买可卖失败：', data)
        return False
    max_can_buy = data['max_cash_buy'][0]
    max_can_sell = data['max_sell_short'][0]
    if quantity > 0:
        return quantity < max_can_buy
    elif quantity < 0:
        return abs(quantity) < max_can_sell
    else:
        return False


# 开仓函数
def open_position(code, price, order_size, trd_side):
    # 计算下单量
    open_quantity = small_calculate_quantity(code) * order_size
    # 判断购买力是否足够
    if is_valid_quantity(code, open_quantity, price):
        # 下单
        ret, data = trade_context.place_order(price=price, qty=open_quantity, code=code, trd_side=trd_side,
                                              order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
                                              remark='moving_average_strategy')
        if ret != RET_OK:
            logger.error('开仓失败：', data)
        order_id = data['order_id'][0]   # 成功后返回订单的ID
        return order_id
    else:
        logger.error('下单数量超出最大可买数量。')


# 开仓函数(交易代码，价格，仓位(手)，买卖方向(0买1卖))
def up_open_position(trading_security, bid_share_price, order_size, buy_or_sell):
    global ORDER_BTN
    #   更改订单状态为已下单 ，订单无回调(不为'-1')
    ORDER_BTN = '0'
    IMMOBILIZATION_SET[bid_share_price][3] = '0'
    order_id = open_position(trading_security, bid_share_price, order_size, buy_or_sell)
    #   更改订单状态为已下单 ，订单无回调
    IMMOBILIZATION_SET[bid_share_price][3] = order_id
    IMMOBILIZATION_SET[bid_share_price][4] = buy_or_sell
    time.sleep(0.04)



#  撤单
def cancel_position(order_id):
    #  撤单
    ret, data = trade_context.modify_order(modify_order_op=ModifyOrderOp.CANCEL, order_id=order_id, price=0,
                                           qty=0, trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        pass
    else:
        logger.error('modify_order error: ', data)

#  撤单(当前价格， 订单ID)
def up_cancel_position(bid_share_price, order_id):
    #   更改订单状态为已下单 ，订单无回调
    IMMOBILIZATION_SET[bid_share_price][3] = '0'
    cancel_position(order_id)
    #   当前价格改为无订单状态
    IMMOBILIZATION_SET[bid_share_price][3] = '-1'
    IMMOBILIZATION_SET[bid_share_price][4] = '-1'
    time.sleep(0.04)

# 解锁交易
def unlock_trade():
    if TRADING_ENVIRONMENT == TrdEnv.REAL:
        ret, data = trade_context.unlock_trade(TRADING_PWD)
        if ret != RET_OK:
            logger.error('解锁交易失败：', data)
            return False
        logger.info('解锁交易成功！')
    return True


# 策略启动时运行一次，用于初始化策略
def on_init():
    # 解锁交易（如果是模拟交易则不需要解锁）
    if not unlock_trade():
        return False
    logger.info('************    初始化    ***********')
    get_market_snapshot()
    initialization_immobilization_set()
    logger.info('************  策略开始运行 ***********')
    return True



############################ 填充以下函数来完成您的策略 ############################
# 每次产生数据变化运行一次，返回买卖信号可将策略的主要逻辑写在此处
def on_bar_open(data):
    global ORDER_QUANTITY
    global PRESENT
    global MARKET_SMALL_WRT_RATIO
    global PRICE
    global ORDER_BTN

    push_code = data['code']  # 推送的代码
    # 找到交易标的 记录数据
    if push_code == TRADING_SECURITY:
        # 找到目标经纪号所在的价格（代码，经纪号，所有买盘数据）
        push_price = find_order_price(push_code, TRADING_NUM, data['Bid'])
        # 推送价格大于价格记录器（庄家买入）
        if push_price > PRESENT:
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 修改字典相关数据[list, WRT_TYPE]
            modify_immobilization_set([push_price, pull_the_market[0], pull_the_market[1]], WRT_TYPE)
            PRESENT = push_price          # 更新价格记录器
        # 推送价格小于价格记录器（庄家买入）
        elif push_price < PRESENT:
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 修改字典相关数据[list, WRT_TYPE]
            modify_immobilization_set([PRESENT, pull_the_market[0], pull_the_market[1]], WRT_TYPE)
            PRESENT = push_price          # 更新价格记录器
        # 推送价格等于0（庄家不在的时候）
        elif push_price == 0:
            pass
        # 推送价格等于价格记录器（庄家在原地没动的时候）
        elif push_price == PRESENT:
            pass

    # 找到推送行情数据的代码
    if push_code == MARKET_SECURITY:
        # 拉取一次行情数据，行情第一档得价格和百分比类型list
        pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
        # 判断下单方向
        if ORDER_BTN == 'BUY':
            # 拉取一次交易数据，行情第一档得价格和百分比类型list 买入单量 卖出单量
            pull_the_trading = pull_the_market_security(TRADING_SECURITY, WRT_TYPE)
            # 1.牛证
            if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
                # 判断行情价格， 判断交易价格
                # 行情 大于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                if pull_the_market[0] > MARKET_PRICE and pull_the_trading[0] <= PRICE and pull_the_trading[3] >= ORDER_SIZE:
                    # 下单买入
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                # 行情 等于 输入监测 and 行情百分比 小于等于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                elif pull_the_market[0] == MARKET_PRICE and pull_the_market[1] >= PERCENT and pull_the_trading[0] <= PRICE and pull_the_trading[3] >= ORDER_SIZE:
                    # 下单买入
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
            # 2.熊
            if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
                # 判断行情价格， 判断交易价格
                # 行情 大于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                if pull_the_market[0] < MARKET_PRICE and pull_the_trading[0] <= PRICE and pull_the_trading[3] >= ORDER_SIZE:
                    # 下单买入
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                # 行情 等于 输入监测 and 行情百分比 小于等于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                elif pull_the_market[0] == MARKET_PRICE and pull_the_market[1] >= PERCENT and pull_the_trading[0] <= PRICE and pull_the_trading[3] >= ORDER_SIZE:
                    # 下单买入
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
        # 判断下单方向
        if ORDER_BTN == 'SELL':
            # 拉取一次交易数据，行情第一档得价格和百分比类型list 买入单量 卖出单量
            pull_the_trading = pull_the_market_security(TRADING_SECURITY, WRT_TYPE)
            # 1.牛证
            if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
                # 判断行情价格， 判断交易价格
                # 行情 大于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                if pull_the_market[0] < MARKET_PRICE and pull_the_trading[0] >= PRICE and pull_the_trading[2] >= ORDER_SIZE:
                    # 下单卖出
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                    ORDER_BTN = '0'
                # 行情 等于 输入监测 and 行情百分比 小于等于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                elif pull_the_market[0] == MARKET_PRICE and pull_the_market[1] <= PERCENT and pull_the_trading[0] >= PRICE and pull_the_trading[2] >= ORDER_SIZE:
                    # 下单卖出
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                    ORDER_BTN = '0'
            # 2.熊
            if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
                # 判断行情价格， 判断交易价格
                # 行情 大于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                if pull_the_market[0] > MARKET_PRICE and pull_the_trading[0] >= PRICE and pull_the_trading[2] >= ORDER_SIZE:
                    # 下单卖出
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                    ORDER_BTN = '0'
                # 行情 等于 输入监测 and 行情百分比 小于等于 输入监测 and 交易价格小等于 输入价格 and 订单仓位 大于等于 输入仓位
                elif pull_the_market[0] == MARKET_PRICE and pull_the_market[1] <= PERCENT and pull_the_trading[0] >= PRICE and pull_the_trading[2] >= ORDER_SIZE:
                    # 下单卖出
                    up_open_position(TRADING_SECURITY, PRICE, ORDER_SIZE, ORDER_BTN)
                    ORDER_BTN = '0'

# 订单状态有变化时运行一次
def on_order_status(data):                          # 推送数据代码
    push_code = data['code'][0]
    if push_code == TRADING_SECURITY:
        push_price = data['price'][0]               # 推送价格
        push_id = int(data['order_id'][0])          # 推送订单ID
        order_status = data['order_status'][0]      # 推送订单的状态
        dealt_qty = data['dealt_qty'][0]            # 成交数量
        trd_side = data['trd_side'][0]

        # 已提交，等待成交
        if order_status == 'SUBMITTED':
            logger.info('【等待成交】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))
        # 撤单
        elif order_status == 'CANCELLED_ALL':
            logger.info('【撤单信息】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))
        # 全部成交
        elif order_status == 'FILLED_ALL':
            logger.info('【全部成交】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))
        # 部分成交
        elif order_status == 'FILLED_PART':
            logger.info('【部分成交】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))


################################ 框架实现部分，可忽略不看 ###############################
class OrderBookClass(OrderBookHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookClass, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error("OrderBookTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open(data)
        return RET_OK, data
#   交易回调


class OnOrderClass(TradeOrderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OnOrderClass, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            on_order_status(data)


################################ 外部调用 ###############################
    # 预测值外部调用
def submit_run(market_security, trading_security, trading_num):
    global MARKET_SECURITY
    global TRADING_SECURITY
    global TRADING_NUM
    MARKET_SECURITY = 'HK.' + market_security       # 标的参考代码
    TRADING_SECURITY = 'HK.' + trading_security  # 交易标的
    TRADING_NUM = trading_num                       # 交易目标经纪号

    # 初始化策略
    if not on_init():
        logger.error('策略初始化失败，脚本退出！')
        quote_context.close()
        trade_context.close()
    else:

        quote_context.set_handler(OrderBookClass())   # 摆盘回调
        trade_context.set_handler(OnOrderClass())    # 订单回调
        # 订阅标的合约的 逐笔，K 线和摆盘，以便获取数据
        quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
    # 更新数据行情价格和百分比 当前价格的
def updata():
    list = []
    # 拉取一次行情数据，行情第一档得价格和百分比类型list
    pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
    list.append(pull_the_market[0])
    list.append(pull_the_market[1])
    list.append(PRESENT)
    logger.info(list)
    return list

def buy(order_size, market_price, percent, price, buyOrSell):
    global ORDER_SIZE
    global MARKET_PRICE
    global PERCENT
    global PRICE
    global ORDER_BTN
    ORDER_SIZE = int(order_size)  # 仓位 单位手默认1手
    MARKET_PRICE = round(float(market_price), 3)  # 参考价格
    PERCENT = float(percent)  # 百分比
    PRICE = float(price)  # 价格
    ORDER_BTN = buyOrSell
    logger.info(ORDER_BTN)

def sell(order_size, market_price, percent, price, buyOrSell):
    global ORDER_SIZE
    global MARKET_PRICE
    global PERCENT
    global PRICE
    global ORDER_BTN
    ORDER_SIZE = float(order_size)  # 仓位 单位手默认1手
    MARKET_PRICE = float(market_price)  # 参考价格
    PERCENT = int(percent)/100  # 百分比
    PRICE = float(price)  # 价格
    ORDER_BTN = buyOrSell
    logger.info(ORDER_BTN)


def setOrderBtn(buyOrSell):
    global ORDER_BTN
    ORDER_BTN = buyOrSell
    logger.info(ORDER_BTN)


def quote_context_close(code_list):
    # 取消相关订阅
    quote_context.subscribe(code_list=code_list, subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
    logger.info(code_list)
