"""
自动跟踪庄家 接单（适用非恒指涡轮）
逻辑
1。 获取各种参数
2. 预测庄家的灵敏度-->确定出交易标的的调价范围形成数轴
3. 分段处理  买入段，休息段，卖出段  3段闭环
4. 锚点 —1—>卖出—2—>不处理—3—>买入—4—>锚点——>卖出——>不处理——>买入——>锚点
5. 4段-处理高档位，低档位订单，上一档位 卖出，及挂单，当前档位无订单无订单买入，（当前档位处理）
6。1段-处理高档位所有买单 判定目标档位改单 ，有撤单 。当前档位卖出，及挂单（变动前档位处理）
"""
# coding=utf-8
import random
import time

import winsound
from futu import *
import logging
# 导入日志配置文件
from trading_src.PyQt5_Trading_AutoFlowTrade.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')
logger1 = logging.getLogger('my_logger1')

############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'         # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111                  # FutuOpenD 监听端口
TRADING_MARKET = TrdMarket.HK           # 交易市场权限，用于筛选对应交易市场权限的账户
TRADING_ENVIRONMENT = TrdEnv.REAL       # 交易环境：真实 / 模拟
IMMOBILIZATION_SET = {}                 # 全局行情数据集合
PRESENT = 0                             # 全局行情价格记录器-服务IMMOBILIZATION_SET
CAN_SELL_QTY = [0, {}, 0, 0]            # 全局仓位变量当前卖单数量和已经存在的卖单数量[增加的仓位,{订单的ID:已经成交的仓位},成交后变化后的仓位,变化前的仓位]
PRESENT_CACHE = 0                       # 恶意撤单时的价格记录器
FORECAST_LIST = []                      # QT5显示数据列表
WRT_TYPE = ''                           # 涡轮方向
STOCK_OWNER = ''                        # 正股代码
WRT_STRIKE_PRICE = 0                    # 涡轮行权价
THEORETICAL_PRICE = 0                   # 当前行情正股对应价格(实际)
PREMIUM = [0, 0, 0, 0]                  # 当前行情正股对应价格(实际)与(理论)[溢价点数,溢价百分比, 庄家所在的买盘,庄家所在卖盘]
TRADING_SESSION = False                 # 交易时段0表示在交易时段,其他表示非交易时段默认是非交易状态
CASH = 0                                # 现金购买力
CONTAINER = collections.deque()         # 买入计数器双端队列
SMALL_CALCULATE_QUANTITY = 100            # 确定最小下单量，一手的股数

MARKET_SMALL_WRT_RATIO = 0.1            # 用户参考系行情的最小波动价格
JUMP_MINIMUM_UNIT = 0.001               # 交易标的最小跳价点
OR_CANCEL_ALL = 1                       # 用户应对庄家撤单行为参数,(0撤单,1不撤单)
CALL_PARAGRAPH = 60 / 100               # 用户设置开始卖出挂单位置
PUT_PARAGRAPH = 30 / 100                # 用户设置开始撤单位置位置
ORDER_QUANTITY = 3                      # 用户挂单量参数
MARKET_SECURITY = 'HK.00000'            # 用户参考系行情代码
TRADING_SECURITY = 'HK.00000'           # 用户交易标的代码
TRADING_NUM = '9715'                    # 用户追踪经纪号
TRADING_PWD = '536386'                  # 用户交易密码,用于解锁交易
ORDER_SIZE = [1, 1, 1]                  # 用户仓位参数 单位手默认0手[当前使用仓位,用户输入仓位,最大风险仓位]
TRADING_SENSITIVITY = 0.1               # 交易代码的实际敏感度

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)   # 行情对象
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT,
                                    security_firm=SecurityFirm.FUTUSECURITIES)  # 交易对象，根据交易品种修改交易对象类型
############################ 全局变量设置 ############################

def small_calculate_quantity(code):
    """
    # 计算最小下单数量
    :param code: 交易代码
    :return:
    """
    price_quantity = 0
    # 使用最小交易量
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        logger.error('获取快照失败：{}'.format(data))
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity


# 判断交易标的类型 相关信息
def get_market_snapshot():
    global WRT_TYPE
    global WRT_CONVERSION_RATIO
    global WRT_RATIO
    global STOCK_OWNER
    global WRT_STRIKE_PRICE
    global CASH
    global SMALL_CALCULATE_QUANTITY
    global MARKET_SECURITY
    ret, data = trade_context.accinfo_query()
    if ret == RET_OK:
        CASH = data['cash'][0]      # 可用资金
    else:
        logger.error('accinfo_query error: ', data)
    ret, data = quote_context.get_market_snapshot([TRADING_SECURITY])
    if ret == RET_OK:
        # bool是否是涡轮
        if data['wrt_valid'][0]:
            WRT_TYPE = data['wrt_type'][0]                          # 涡轮类型
            WRT_CONVERSION_RATIO = data['wrt_conversion_ratio'][0]  # 换股比例
            WRT_RATIO = round(WRT_CONVERSION_RATIO * 0.001, 3)      # 波动率
            STOCK_OWNER = data['stock_owner'][0]                    # 正股代码
            WRT_STRIKE_PRICE = data['wrt_strike_price'][0]          # 行驶价格
            SMALL_CALCULATE_QUANTITY = small_calculate_quantity(TRADING_SECURITY)   # 确定最小下单量，一手的股数
            if MARKET_SECURITY == 'HK.0':
                MARKET_SECURITY = STOCK_OWNER


            logger.info('正股代码：{}--参考行情代码{}'.format(STOCK_OWNER, MARKET_SECURITY))
            logger.info('涡轮代码：{} | 涡轮方向：{} | 目标经纪号：{} | 换股比例：{} | 现金购买力：{} | 一手的股数：{}'
                        .format(TRADING_SECURITY, WRT_TYPE, TRADING_NUM, WRT_CONVERSION_RATIO, CASH, SMALL_CALCULATE_QUANTITY))
            logger.info('理论波动率 ： 默认等于理论灵敏度-->{}'.format(TRADING_SENSITIVITY))
            logger.info('买入开始：{} | 卖出开始：{} | 挂单量：{} | 仓位：{}  | 是否跟随撤单(0跟随其他不跟随)：{} '
                        .format(CALL_PARAGRAPH, PUT_PARAGRAPH, ORDER_QUANTITY, ORDER_SIZE, OR_CANCEL_ALL))
    else:
        logger.error('error:', data)

# 初始化字典 备用列表
def initialization_immobilization_set():
    IMMOBILIZATION_SET.clear()
    logger.debug("初始化记录值字典默认[-1, -1, -1, -1, -1, '-1', '-1']（0-0.250）")
    num = 0
    while num <= 250:
        # [价格，记录值，百分比，订单号，买卖方向]
        IMMOBILIZATION_SET[round((num * 0.001), 3)] = [-1, -1, -1, -1, -1, '-1', '-1']
        num = num + 1

def error_beep_one(freq, duration):
    logger.error("请注意: -->程序出错了，程序出错了")
    winsound.Beep(freq, duration)
    # for i in range(1) : winsound.Beep(freq, duration)

def error_beep():
    # 创建线程并启动 声音提示线程
    beep_thread = threading.Thread(target=error_beep_one, args=(1000, 500))
    beep_thread.start()


# 庄家撤单处理
def farmhouse_cancel_position(code, present, jump_minimum_unit):
    if present > 0:
        # 优先撤当前订单
        if IMMOBILIZATION_SET[present][5] != '-1':
            up_cancel_position(present, IMMOBILIZATION_SET[present][5], log=None,
                               message=f' 庄家撤单：撤相关订单--订单价格 |+{str(present)}')
        num = 2
        while num >= -10:
            # 目标价格是有订单-撤单(-1 没有订单)
            if IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][5] != '-1':
                up_cancel_position(round(present + num * jump_minimum_unit, 3),
                                   IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][5], log=None,
                                   message=f'庄家撤单：撤相关订单--订单价格 |{str(round(present + num * jump_minimum_unit, 3))}')
            num = num - 1
        ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=present)
        can_sell_qty = 0
        if ret == RET_OK:
            can_sell_qty = data['max_position_sell'][0]
            logger.debug(f'持仓最大可卖数量：{can_sell_qty}')  # 最大融资可买数量
        else:
            logger.error('acctradinginfo_query error: ', data)
        # 有持仓 卖出持仓（0 没有持仓）
        if can_sell_qty > 0:
            up_open_position(code, present, can_sell_qty, 'SELL', log=None,
                             message=f'庄家撤单 卖出价格{present},仓位{can_sell_qty}')


# 取消交易相关订阅
def quote_context_unsub(context, code_list=None, subtype_list=None, unsubscribe_all=True):
    """
    # 取消订阅 默认是取消链接的所有订阅
    :param context:             链接
    :param code_list:           代码列表
    :param subtype_list:        类型列表
    :param unsubscribe_all:     是否全部取消
    :return:    无
    """
    if unsubscribe_all is True:
        ret_unsub, err_message_unsub = context.unsubscribe_all()  # 取消所有订阅
        if ret_unsub == RET_OK:
            logger.info(f'unsubscribe all successfully！current subscription status:{context.query_subscription()}')  # 取消订阅后查询订阅状态
        else:
            logger.info(f'Failed to cancel all subscriptions！{err_message_unsub}')

    elif unsubscribe_all is not True and code_list is not None and subtype_list is not None:
        ret_unsub, err_message_unsub = quote_context.unsubscribe(code_list=code_list, subtype_list=subtype_list, unsubscribe_all=unsubscribe_all)
        if ret_unsub == RET_OK:
            logger.info(f'unsubscribe successfully！current subscription status:{quote_context.query_subscription()}')  # 取消订阅后查询订阅状态
        else:
            logger.error(f'unsubscription failed！{err_message_unsub}')

def quote_context_front(code, theoretical_price, jump_minimum_unit):
    """
    重置和关闭和错误执行取消前交易操作，卖出持仓
    :param code:                交易代码
    :param theoretical_price:   交易价格
    :param jump_minimum_unit:   最小变动点
    :return: 无
    """
    # 撤出所有订单
    if theoretical_price >= 0.010:
        num = -9
        while num <= 10:
            price = round(theoretical_price + num * jump_minimum_unit, 3)
            if IMMOBILIZATION_SET[price][5] != '-1':
                cancel_position(IMMOBILIZATION_SET[price][5])
            num = num + 1
    # 1.查询是否有可以卖的数量（必须撤单后才能查询出）
    can_sell_qty = is_valid_quantity(code, theoretical_price)[1]
    if can_sell_qty > 0:  # 有可卖仓位
        # 获取一次 1 档实时摆盘数据
        ret, data = quote_context.get_order_book(code, num=3)
        if ret == RET_OK:
            num = 0
            push_can_buy_qty = 0
            while num <= 3:
                bid_price = data['Bid'][num][0]
                push_can_buy_qty = push_can_buy_qty + data['Bid'][num][1]
                if can_sell_qty <= push_can_buy_qty:
                    up_open_position(code, bid_price, can_sell_qty, 'SELL', log=None, message=None)
                    break
                num = num + 1
        else:
            logger.error('error:{}'.format(data))
    else:
        logger.info('没有持仓 : ')

def modify_trading_sensitivity(trading_sensitivity, num, pull_percentage, market_small_wrt_ratio):
    """

    :param trading_sensitivity:     波动率
    :param num:                     增加或者减少价格（波动率倍数）
    :param pull_percentage:         成交实时行情的百分比
    :param market_small_wrt_ratio:  行情的最小变动
    :return: 得到增加后者减少的 整数位和百分比
    """
    integer_part = int(trading_sensitivity * num)  # 相关价格变动的整数部分
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
    return round(integer_part * market_small_wrt_ratio, 3), round(fractional_part, 2)

# 更新显示数据
def pull_print_list(price, jump_minimum_unit):
    """
    更新显示数据
    :param price: 中间价格
    :param jump_minimum_unit: 步长
    :return:
    """
    # 清除列表数据
    FORECAST_LIST.clear()
    FORECAST_LIST.append(TRADING_SECURITY)
    push_price_list = []
    for i in range(-2, 3):  # 生成 -2, -1, 0, 1, 2
        push_price_list.append(round(price + i * jump_minimum_unit, 3))
    # 遍历所有相关价格
    for key in push_price_list:
        # 集合中没有相关价格 添加相关价格
        if IMMOBILIZATION_SET.get(key) is None:
            FORECAST_LIST.append(str(key))
        # 集合中有相关价格 添加相关记录值
        else:
            # FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key))))  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
            # 获取集合内容并转为字符串列表
            items = list(map(str, IMMOBILIZATION_SET.get(key, [])))
            # 处理第6个元素（索引4）
            if len(items) > 5:  # 确保有第5个元素
                items[5] = items[5][:5]  # 取前5个字符
            # 拼接并加入列表
            FORECAST_LIST.append(' '.join(items))


def modify_immobilization_set(price, pull_mark_price, pull_percentage, wrt_type, up_or_down, jump_minimum_unit):
    """
    全局行情数据集合(预测值)并提供用户显示相关数据
    :param bid_price: 涡轮的买入价格
    :param pull_price: 行情数据价格
    :param pull_percentage: 行情数据的百分比
    :param wrt_type: 涡轮的类型
    :param jump_minimum_unit: 最小跳价点
    :return: 无
    """
    push_price_list = []
    if price <= 0.250:
        # 判断是买入还是卖出
        if up_or_down == 'up':
            num = -2  # 计数器
            while num <= 2:
                # 得到需要增加或者减少的整数，和分数部分
                integer_part, fractional_part = modify_trading_sensitivity(TRADING_SENSITIVITY, num, pull_percentage, MARKET_SMALL_WRT_RATIO)

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
                num = num + 1
        if up_or_down == 'down':
            num = -2  # 计数器
            while num <= 2:
                # 得到增加或者减少的整数部分和百分比integer_part,百分比fractional_part
                integer_part, fractional_part = modify_trading_sensitivity(TRADING_SENSITIVITY, num, pull_percentage, MARKET_SMALL_WRT_RATIO)
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
                num = num + 1
        pull_print_list(price, jump_minimum_unit)


def pull_the_market_security(market_security, warrants_call_put):
    """
    根据涡轮类型获得正股价格和计算买卖价格的百分比
    :param market_security: 正股代码
    :param warrants_call_put:   涡轮的类型
    :return: pull_price, pull_percentage
            如果涡轮是牛返回的是[买盘价格，和买盘占比]
            如果涡轮是熊返回的是[卖盘价格，和卖占比]
    """
    ret, data = quote_context.get_order_book(market_security, num=1)  # 获取一次 1 档实时摆盘数据
    pull_price = 0
    pull_percentage = 0
    if ret == RET_OK:
        if len(data['Bid'][0]) is not None:
            if warrants_call_put == 'BULL' or warrants_call_put == 'CALL':
                pull_price = data['Bid'][0][0]
                pull_percentage = round(data['Bid'][0][1] / (data['Bid'][0][1] + data['Ask'][0][1]), 2)
            elif warrants_call_put == 'BEAR' or warrants_call_put == 'PUT':
                pull_price = data['Ask'][0][0]
                pull_percentage = round(data['Ask'][0][1] / (data['Ask'][0][1] + data['Bid'][0][1]), 2)
    else:
        logger.error('获得正股价格和百分比失败error:{}'.format(data))
    return pull_price, pull_percentage


def find_order_price(push_code, trading_num, data):
    """
    查询目标经济号所在位置
    :param push_code:   涡轮的代码
    :param trading_num: 目标经经济号
    :param data:        所有的摆盘数据
    :return: bid_price, ask_price
            没有找到庄家返回0，0
    """
    ret, bid_frame_table, ask_frame_table = quote_context.get_broker_queue(push_code)  # 获取一次经纪队列数据
    bid_price = 0
    ask_price = 0
    if ret == RET_OK:
        for indexs in bid_frame_table.index:
            bid_broker_id = bid_frame_table.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
            bid_broker_pos = bid_frame_table.at[indexs, 'bid_broker_pos']  # 经纪档位
            if bid_broker_id == int(trading_num):
                pos = bid_broker_pos  # 经纪号所在得档位
                bid_price = data['Bid'][pos - 1][0]
                break
        for indexs in ask_frame_table.index:
            ask_broker_id = ask_frame_table.at[indexs, 'ask_broker_id']  # 经纪卖盘 ID
            ask_broker_pos = ask_frame_table.at[indexs, 'ask_broker_pos']  # 经纪档位
            if ask_broker_id == int(trading_num):
                pos_ask = ask_broker_pos  # 经纪号所在得档位
                ask_price = data['Ask'][pos_ask - 1][0]
                break
        return bid_price, ask_price
    else:
        logger.error('获取经纪号所在的价格数据失败error:{}'.format(bid_frame_table))
        return bid_price, ask_price


# 查询最大可买可卖
def is_valid_quantity(code, price):
    """
    现金可买, 持仓可卖
    :param code:
    :param price:
    :return: [现金可买, 持仓可卖]
    """
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=TRADING_ENVIRONMENT)
    if ret != RET_OK:
        logger.error('获取最大可买可卖失败：data{}|code{}|price{}'.format(data, code, price))
        return False
    max_can_buy = data['max_cash_buy'][0]
    max_can_sell = data['max_position_sell'][0]
    return [max_can_buy, max_can_sell]


def open_position(code, price, order_size, trd_side):
    """
    开仓函数
    :param code:
    :param price:
    :param order_size:
    :param trd_side:
    :return:
    """
    # 判断购买力是否足够
    ret, data = trade_context.place_order(price=price, qty=order_size, code=code, trd_side=trd_side,
                                          order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
                                          remark='moving_average_strategy')
    if ret != RET_OK:
        logger.error('开仓失败：data{}|code{}|price{}|order_size{}|trd_side{}'.format(data, code, price, order_size, trd_side))
    order_id = data['order_id'][0]   # 成功后返回订单的ID
    return order_id


def up_open_position(trading_security, bid_share_price, order_size, buy_or_sell, log, message):
    """
    开仓函数(交易代码，价格，仓位(手)，买卖方向(0买1卖))
    :param trading_security: 交易代码
    :param bid_share_price: 价格
    :param order_size: 仓位(手)
    :param buy_or_sell: 买卖方向(0买1卖)
    :param log:
    :param message:
    :return:
    """
    def up_open_position1(trading_security, bid_share_price, order_size, buy_or_sell, log, message):
        CounterContainer()  # 调用一次计数方法
        IMMOBILIZATION_SET[bid_share_price][5] = 0
        order_id = open_position(trading_security, bid_share_price, order_size, buy_or_sell)
        IMMOBILIZATION_SET[bid_share_price][5] = str(order_id)
        IMMOBILIZATION_SET[bid_share_price][6] = buy_or_sell
        if log is not None and message is not None:
            logger.debug(f'{message}-溢价{log[0]}-微调点位{log[1]}-订单号{order_id}')
        elif message is not None:
            logger.debug(f'{message}')
        # 防止下单太快 订单没来得及推送导致仓位错误
        time.sleep(0.02)
    if buy_or_sell == 'BUY':
        if len(CONTAINER) <= 13 and bid_share_price <= 0.250:
            up_open_position1(trading_security, bid_share_price, order_size, buy_or_sell, log, message)
        else:
            logger.debug(f'30秒内超过13次下单 ,本次不下单或者价格高于指定价格')
    elif buy_or_sell == 'SELL':
        up_open_position1(trading_security, bid_share_price, order_size, buy_or_sell, log, message)
    pull_print_list(bid_share_price, JUMP_MINIMUM_UNIT)

def cancel_position(order_id):
    """
    撤单
    :param order_id: 订单ID
    :return:
    """
    ret, data = trade_context.modify_order(ModifyOrderOp.CANCEL, order_id, 0,
                                           0, trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        # logger.debug('撤订单成功: {}'.format(order_id))
        pass
    else:
        logger.error('撤订单失败: {} error: {}'.format(order_id, data))


def up_cancel_position(bid_share_price, order_id, log=None, message=None):
    """
    撤单(当前价格， 订单ID)
    :param bid_share_price: 撤单价格
    :param order_id: 撤单的交易ID
    :param log: 撤单的日志[溢价，微调点位]
    :param message: 撤单的信息
    :return: 无
    """
    if log is not None and message is not None:
        logger.debug(f'{message}-溢价{log[0]}-微调点位{log[1]}')
    elif message is not None:
        logger.debug(f'{message}')
    cancel_position(order_id)
    IMMOBILIZATION_SET[bid_share_price][5] = '-1'
    IMMOBILIZATION_SET[bid_share_price][6] = '-1'
    # 判断订单是否已经成交过
    if CAN_SELL_QTY[1].get(order_id) != None:
        del CAN_SELL_QTY[1][order_id]
    pull_print_list(bid_share_price, JUMP_MINIMUM_UNIT)


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
    return True

def selected_price(pull_price, pull_percentage, wrt_type, present):
    """
    根据正股确定当前涡轮的理论价格在锚点价格附近5个价格内查询理论价值
    :param pull_price: 正股价格
    :param pull_percentage: 正股百分比
    :param wrt_type: 涡轮的类型
    :param present: 查询用得锚点
    :return: 无
    """
    global THEORETICAL_PRICE
    # 锚点不能为0 为零说明开始记录数据
    if present != 0:
        # 认购定价
        if wrt_type == 'BULL' or wrt_type == 'CALL':
            num = -1
            while num <= 5:
                # 记录值在记录值之间
                if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][3] \
                        <= round(pull_price + pull_percentage * JUMP_MINIMUM_UNIT, 5) < \
                        IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][3]:
                    THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]   # 确定交易价位
                num = num + 1
            num = -5
            while num <= -1:
                if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][3] \
                        <= round(pull_price + pull_percentage * JUMP_MINIMUM_UNIT, 5) < \
                        IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][3]:
                    THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]

                num = num + 1
        # 认沽定价
        if wrt_type == 'BEAR' or wrt_type == 'PUT':
            num = -1
            while num <= 5:
                if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][3] \
                        >= round(pull_price + pull_percentage * JUMP_MINIMUM_UNIT, 5) \
                        > IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][3]:
                    # 确定交易价位
                    THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]
                num = num + 1
            num = -5
            while num <= -1:
                if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][3] \
                        >= round(pull_price + pull_percentage * JUMP_MINIMUM_UNIT, 5) \
                        > IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][3]:
                    # 确定交易价位
                    THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]
                num = num + 1


def put_the_size(trading_security, push_price, order_quantity):
    """
    下单仓位
    :param trading_security: 交易代码
    :param push_price: 交易价格
    :param order_quantity: 最大订单数
    :return: 单位手
    """
    # 更新最大安全下单量int自动取整
    try:
        if SMALL_CALCULATE_QUANTITY * push_price != 0:
            ORDER_SIZE[2] = int(CASH / (SMALL_CALCULATE_QUANTITY * push_price) / (order_quantity + 1))
    except Exception as e:
        logger.debug('SMALL_CALCULATE_QUANTITY{} push_price{} order_quantity{}'.format(SMALL_CALCULATE_QUANTITY, push_price, order_quantity))
    # 用户输入值为0,自动调节仓位
    if ORDER_SIZE[1] == 0:
        ORDER_SIZE[0] = ORDER_SIZE[2]
    # 有用户输入值及不为0
    if ORDER_SIZE[1] != 0:
        ORDER_SIZE[0] = ORDER_SIZE[1]
        # 判断用户输入值是大于最大安全下单量
        if ORDER_SIZE[1] > ORDER_SIZE[2]:ORDER_SIZE[0] = ORDER_SIZE[2]


def _remove_element(element):
    """
    异步删除数据
    :param element:
    :return:
    """
    time.sleep(30)
    if element in CONTAINER:
        CONTAINER.remove(element)

#
def CounterContainer():
    """
    给双端队列添加时间元素
    :return:
    """
    element = time.time()
    CONTAINER.append(element)
    threading.Thread(target=_remove_element, args=(element,)).start()

def buy_paragraph(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log,):
    """
    买入段的处理处理顺序
    1. （格式化环境）处理高位的买入和低位buy多余的SELL单
    2.  买入当前价格
    :param tradingSecurity: 交易代码
    :param orderSize: 交易仓位[当前使用仓位,用户输入仓位,最大风险仓位]
    :param sharePrice: 当前理论价格
    :param orderQuantity: 最大订单数量
    :param jumpMinimumUnit: 最小跳加点
    :param log: 日志记录[溢价，微调百分比]
    :return: 无
    """
    # 处理高位位的多BUY 单和 多余SELL单sharePrice + (num + 1) * jumpMinimumUnit
    # 处理了当前价格以上的买单和当前价格+1以上的卖单

    if PRESENT != 0:
        num = 1
        while num <= 10:
            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            price = round(sharePrice + num * jumpMinimumUnit, 3)
            if IMMOBILIZATION_SET[price][5] != '-1':
                # 订单是买入订单
                if IMMOBILIZATION_SET[price][6] == 'BUY':
                    #  撤单(当前价格， 订单ID)
                    up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'买入段-BUY单-撤单|价格:{sharePrice}-高位多余订单:')
                price = round(sharePrice + (num + 1) * jumpMinimumUnit, 3)
                if IMMOBILIZATION_SET[price][6] == 'SELL':
                    #  撤单(当前价格， 订单ID)
                    up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'买入段-SELL单-撤单|价格:{sharePrice}-高位多余订单')
            num = num + 1

        # 处理当前价格低位的多余BUY单
        num = 0
        while num <= 5:
            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            price = round(sharePrice - orderQuantity * jumpMinimumUnit - num * jumpMinimumUnit, 3)
            if IMMOBILIZATION_SET[price][5] != '-1' and IMMOBILIZATION_SET[price][6] == 'BUY':
                #  撤单(当前价格， 订单ID)
                up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'买入段-BUY单 -撤单|价格:{sharePrice}-低位多余订单')

            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            price = round(sharePrice - num * jumpMinimumUnit, 3)
            if IMMOBILIZATION_SET[price][5] != '-1' and IMMOBILIZATION_SET[price][6] == 'SELL':
                #  撤单(当前价格， 订单ID)
                up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'买入段-SELL单-撤单|价格:{sharePrice}-低位多余订单')
            num = num + 1

        #   卖出订单如果是部分成交 修改订单
        price = round(sharePrice + jumpMinimumUnit, 3)
        if IMMOBILIZATION_SET[price][5] != '-1' and \
                IMMOBILIZATION_SET[price][6] == 'SELL' and CAN_SELL_QTY[2] != CAN_SELL_QTY[3]:
            up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'买入段-SELL单-撤单|价格{sharePrice}-仓位{CAN_SELL_QTY}-有订单 有持仓 （部分成交）')
            # 卖出订单
            up_open_position(tradingSecurity, price, CAN_SELL_QTY[2], 'SELL', log,
                             f'买入段-SELL单-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有订单 有持仓')
            CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
        #   卖出价格没有订单且有成交订单任务
        if IMMOBILIZATION_SET[price][5] == '-1' and CAN_SELL_QTY[2] != 0:
            if CAN_SELL_QTY[2] != CAN_SELL_QTY[3]:
                up_open_position(tradingSecurity, price, CAN_SELL_QTY[2], 'SELL', log,
                                 f'买入段-SELL单-卖出|价格{price}-仓位{CAN_SELL_QTY}-无订单 有持仓')
            CAN_SELL_QTY[3] = CAN_SELL_QTY[2]

        # 5，没有订单记录 订单价格大于等0.010 且已有仓位小于所有订单仓位的一般买入任务（不等于-1为真，其他取反）
        if IMMOBILIZATION_SET[sharePrice][5] == '-1' and CAN_SELL_QTY[2] < orderSize[0]:
            if round(sharePrice, 3) > 0.011 and len(CONTAINER) < 15:
                # 修改下单数量为随机数量
                orderSizemax = int(is_valid_quantity(tradingSecurity, sharePrice)[0] / SMALL_CALCULATE_QUANTITY)
                orderSize = orderSize[0] + random.randint(0, 4)
                if orderSize > orderSizemax:
                    orderSize = orderSizemax
                orderSize = orderSize * SMALL_CALCULATE_QUANTITY
                # 下单函数 (代码，价格，大小，方向)
                up_open_position(tradingSecurity, sharePrice, orderSize, 'BUY', log,
                                 f'买入段-BUY单 -买入|价格{sharePrice}-仓位{orderSize} 没有订单')
            # 价格接近0.011时溢价太大,禁止下单以免回收
            if round(sharePrice, 3) == 0.011 and len(CONTAINER) < 15:
                # 修改下单数量为随机数量
                orderSizemax = int(is_valid_quantity(tradingSecurity, sharePrice)[0] / SMALL_CALCULATE_QUANTITY)
                orderSize = orderSize[0] + random.randint(0, 4)
                if orderSize > orderSizemax:
                    orderSize = orderSizemax
                orderSize = orderSize * SMALL_CALCULATE_QUANTITY
                # 下单函数 (代码，价格，大小，方向)
                up_open_position(tradingSecurity, sharePrice, orderSize, 'BUY', log,
                                 f'买入段-BUY单 -买入|价格{sharePrice}-仓位{orderSize} 没有订单')


def newsell(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log):
    """
    卖出段 当前价格的操作
    :param tradingSecurity:
    :param orderSize:
    :param sharePrice:
    :param orderQuantity:
    :param jumpMinimumUnit:
    :param log:
    :return:
    """
    # 有订单（不等于-1为真，其他取反）
    if IMMOBILIZATION_SET[sharePrice][5] != '-1':
        if IMMOBILIZATION_SET[sharePrice][6] == 'BUY':
            # 撤单(当前价格)
            up_cancel_position(sharePrice, IMMOBILIZATION_SET[sharePrice][5], log,
                               f'撤退段-当前有订单-BUY单 -撤单|价格{sharePrice}')
            if CAN_SELL_QTY[2] != 0 and len(CONTAINER) <= 13:
                up_open_position(tradingSecurity, sharePrice, CAN_SELL_QTY[2], 'SELL', log,
                                 f'撤退段-当前有订单-SELL-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有持仓')
                CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
        # 订单类型是卖单类型。改单撤单处理
        elif IMMOBILIZATION_SET[sharePrice][6] == 'SELL' and CAN_SELL_QTY[2] != CAN_SELL_QTY[3] and len(
                CONTAINER) <= 13:
            up_cancel_position(sharePrice, IMMOBILIZATION_SET[sharePrice][5], log,
                               f'撤退段-当前有订单-SELL-撤单|价格{sharePrice}-成交前前仓位{CAN_SELL_QTY[2]}-且持仓改变')
            up_open_position(tradingSecurity, sharePrice, CAN_SELL_QTY[2], 'SELL', log,
                             f'撤退段-当前有订单-SELL-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有持仓')
            CAN_SELL_QTY[3] = CAN_SELL_QTY[2]

    # 5，无订单 卖出（不等于-1为真，其他取反）
    elif IMMOBILIZATION_SET[sharePrice][5] == '-1' and CAN_SELL_QTY[2] != 0:
        up_open_position(tradingSecurity, sharePrice, CAN_SELL_QTY[2], 'SELL', log,
                         f'撤退段-当前无订单-SELL-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有持仓')
        CAN_SELL_QTY[3] = CAN_SELL_QTY[2]

def sell_paragraph(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log):
    """
    撤退段 + 卖出段（撤单，在卖）
    :param tradingSecurity: 交易代码
    :param orderSize: 交易仓位[当前使用仓位,用户输入仓位,最大风险仓位]
    :param sharePrice: 当前理论价格
    :param orderQuantity: 最大订单数量
    :param jumpMinimumUnit: 最小跳加点
    :param log: 日志记录[溢价，微调百分比]
    :return: 无
    """

    #  清理高位所有订单（sharePrice + 1）
    num = 1
    while num <= 10:
        #  7. 目标价格是有订单(-1 没有订单,改单撤单)
        price = round(sharePrice + num * jumpMinimumUnit, 3)
        if IMMOBILIZATION_SET[price][5] != '-1':
            #  撤单(当前价格， 订单ID)
            up_cancel_position(price, IMMOBILIZATION_SET[price][5], log, f'撤退段-SELL AND BUY单-撤单|价格:{sharePrice}-高位多余订单')
        num = num + 1

    #  6. 目标价位没有订单(-1 没有订单,改单处理)
    if IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit, 3)][5] == '-1':
        # 7. 目标价格大于最低价格
        if round(sharePrice, 3) - round(orderQuantity * jumpMinimumUnit, 3) >= 0.011 and len(CONTAINER) <= 13:
            # 修改下单数量为随机数量
            orderSizemax = int(is_valid_quantity(tradingSecurity, sharePrice)[0] / SMALL_CALCULATE_QUANTITY)
            orderSize = orderSize[0] + random.randint(0, 4)
            if orderSize > orderSizemax:
                orderSize = orderSizemax
            orderSize = orderSize * SMALL_CALCULATE_QUANTITY
            up_open_position(tradingSecurity, round(sharePrice - orderQuantity * jumpMinimumUnit, 3), orderSize,
                             'BUY', log,
                             f'撤退段-BUY单 -当前|目标价格{sharePrice}-->{round(sharePrice - orderQuantity * jumpMinimumUnit, 3)}-有订单 目标没有订单且大于0.010')
        # 当前价位的操作
        newsell(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log)
    elif IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit, 3)][5] != '-1':
        # 当前价位的操作
        newsell(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log)


############################ 填充以下函数来完成您的策略 ############################
def on_bar_open(data):
    """
    实时摆盘推送，订阅列表每变动一次推送一次
    :param data: 推送的数据
    :return: NONE
    """
    global ORDER_QUANTITY
    global PRESENT
    global PRESENT_CACHE
    global MARKET_SMALL_WRT_RATIO
    global THEORETICAL_PRICE
    global TRADING_SESSION

    # 找到交易标的 确定交易时间
    if ('09:01:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '11:59:40' or
            '13:00:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '15:59:40'):
        push_code = data['code']  # 推送的代码
        # 找到交易标的
        if push_code == TRADING_SECURITY:
            # 找到目标经纪号所在的价格（代码，经纪号，所有买盘数据）
            bid_price, ask_price = find_order_price(push_code, TRADING_NUM, data)
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_mark_price, pull_percentage = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 推送价格大于价格记录器（庄家买入）
            if bid_price > PRESENT:
                # 记录庄家最后一次出现的价格（用于理论价格查询的定位器）
                PRESENT_CACHE = bid_price
                time.sleep(1.5)
                ret, testdata = quote_context.get_order_book(push_code, num=5)  # 获取一次 10 档实时摆盘数据
                cache_bid_price, cache_ask_price = find_order_price(push_code, TRADING_NUM, testdata)
                if cache_bid_price >= bid_price:
                    if pull_mark_price != 0:
                        # 下单仓位调节
                        put_the_size(TRADING_SECURITY, bid_price, ORDER_QUANTITY)
                        # 修改字典相关数据
                        modify_immobilization_set(bid_price, pull_mark_price, pull_percentage, WRT_TYPE, 'up', JUMP_MINIMUM_UNIT)
                    PRESENT = bid_price  # 更新价格记录器
            # 推送价格小于价格记录器（庄家买入）
            elif bid_price < PRESENT:
                # 记录庄家最后一次出现的价格（用于理论价格查询的定位器）
                PRESENT_CACHE = bid_price
                # 延迟1秒时间后判断庄家最新状态和价格
                time.sleep(1.5)
                ret, testdata = quote_context.get_order_book(push_code, num=5)  # 获取一次 10 档实时摆盘数据
                cache_bid_price, cache_ask_price = find_order_price(push_code, TRADING_NUM, testdata)
                if cache_bid_price == bid_price:
                    if pull_mark_price != 0:
                        # 下单仓位调节
                        put_the_size(TRADING_SECURITY, bid_price, ORDER_QUANTITY)
                        # 修改字典相关数据
                        modify_immobilization_set(PRESENT, pull_mark_price, pull_percentage, WRT_TYPE, 'up', JUMP_MINIMUM_UNIT)
                        modify_immobilization_set(PRESENT, pull_mark_price, pull_percentage, WRT_TYPE, 'down', JUMP_MINIMUM_UNIT)
                    PRESENT = bid_price  # 更新价格记录器
                # 推送价格等于价格记录器（庄家在原地没动的时候）
            elif bid_price == PRESENT:
                pass

        # 找到推送行情数据的代码
        if push_code == MARKET_SECURITY:
            if TRADING_SESSION is False:
                TRADING_SESSION = True
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_price, pull_percentage = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 2.确定当前市场对应理论价格
            selected_price(pull_price, pull_percentage, WRT_TYPE, PRESENT_CACHE)
            log = ['--', '--']
            # 能找到当前的理论价格
            if THEORETICAL_PRICE != None and THEORETICAL_PRICE > 0.009:
                num = 0
                num_num = 0
                # 1.牛证
                if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
                    # 1.行情大于 当前价格的理论点位 买入段
                    sum = round(CALL_PARAGRAPH * TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4],
                                5)  # 加减的总大小
                    num = int(sum)  # 加减的证书位
                    num_num = round(JUMP_MINIMUM_UNIT * (sum - num), 5)  # 加减的分数位置
                    if round(pull_price + pull_percentage * 0.001, 5) \
                            >= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num,
                                     5):
                        # logger.debug('买入跳价点:{}sun:{}--num:{}-numnum:{}--买入行情{}>>理论买入{}>>跳价点位{}'.format(round((TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4]), 5),
                        #     sum, num, num_num, round(pull_price + pull_percentage * 0.001, 5), round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num, 5),
                        #                                                                                IMMOBILIZATION_SET[THEORETICAL_PRICE]))

                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE, round(THEORETICAL_PRICE, 3), ORDER_QUANTITY,
                                      JUMP_MINIMUM_UNIT, log)

                    # 2.行情小于 当前价格的理论点位的 卖出段
                    sum = round(PUT_PARAGRAPH * TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4],5)  # 加减的总大小
                    num = int(sum)  # 加减的证书位
                    num_num = round(JUMP_MINIMUM_UNIT * (sum - num), 5)  # 加减的分数位置m - num)
                    if round(pull_price + pull_percentage * 0.001, 5) \
                            <= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num,
                                     5):
                        # logger.debug('卖出跳价点:{}sun:{}--num:{}-numnum:{}--买入行情{}>>理论买入{}>>跳价点位{}'.format(round((TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4]), 5),
                        #     sum, num, num_num, round(pull_price + pull_percentage * 0.001, 5), round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num, 5),
                        #                                                                                IMMOBILIZATION_SET[THEORETICAL_PRICE]))
                        sell_paragraph(TRADING_SECURITY, ORDER_SIZE, round(THEORETICAL_PRICE, 3), ORDER_QUANTITY,
                                       JUMP_MINIMUM_UNIT, log)
                # 2.熊
                if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
                    sum = round(CALL_PARAGRAPH * TRADING_SENSITIVITY - IMMOBILIZATION_SET[THEORETICAL_PRICE][4], 5)
                    num = int(sum)
                    num_num = round(JUMP_MINIMUM_UNIT * abs(sum - num), 5)
                    if round(pull_price + pull_percentage * 0.001, 5) \
                            <= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num,
                                     5):
                        # logger.debug('买入跳价点:{}sun:{}--num:{}-numnum:{}--买入行情{}>>理论买入{}>>跳价点位{}'.format(round((TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4]), 5),
                        #     sum, num, num_num, round(pull_price + pull_percentage * 0.001, 5), round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num, 5),
                        #                                                                                IMMOBILIZATION_SET[THEORETICAL_PRICE]))
                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE, round(THEORETICAL_PRICE, 3), ORDER_QUANTITY,
                                      JUMP_MINIMUM_UNIT, log)
                    # 2.行情大于 当前价格的理论点位的 卖出段
                    sum = round(PUT_PARAGRAPH * TRADING_SENSITIVITY - IMMOBILIZATION_SET[THEORETICAL_PRICE][4], 5)
                    num = int(sum)
                    num_num = round(JUMP_MINIMUM_UNIT * abs(sum - num),5)
                    if round(pull_price + pull_percentage * 0.001, 5) \
                            >= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num,
                                     5):
                        # logger.debug('卖出跳价点:{}sun:{}--num:{}-numnum:{}--买入行情{}>>理论买入{}>>跳价点位{}'.format(round((TRADING_SENSITIVITY + IMMOBILIZATION_SET[THEORETICAL_PRICE][4]), 5),
                        #     sum, num, num_num, round(pull_price + pull_percentage * 0.001, 5), round(IMMOBILIZATION_SET[THEORETICAL_PRICE][3] + num * MARKET_SMALL_WRT_RATIO + num_num, 5),
                        #                                                                                IMMOBILIZATION_SET[THEORETICAL_PRICE]))
                        sell_paragraph(TRADING_SECURITY, ORDER_SIZE, round(THEORETICAL_PRICE, 3), ORDER_QUANTITY,
                                       JUMP_MINIMUM_UNIT, log)
            # 不能找到当前价格，
            elif THEORETICAL_PRICE == 0:
                pass
    elif '16:00:00' > time.strftime('%H:%M:%S', time.localtime()) > '15:59:40' \
            or '12:00:00' > time.strftime('%H:%M:%S', time.localtime()) > '11:59:40':
        # 执行一次撤单-卖出操作,更改交易状态
        if TRADING_SESSION is True:
            logger.info('当前时间[%s]不在交易时间段执行' % time.strftime('%H:%M:%S', time.localtime()))
            quote_context_reset()
            TRADING_SESSION = False

def num(a, b):
    """
    赋值+初始化
    :param a: 原有仓位
    :param b: 成交后的仓位
    :return:
    """
    a = a + b
    CAN_SELL_QTY[0] = 0
    return a

def filled(trd_side, dealt_qty, push_id, order_status):
    """
    dealt_qty为已经交的数量累加1+2=3+1=4
    CAN_SELL_QTY = [0, {}, 0, 0]
    # 全局仓位变量当前卖单数量和已经存在的卖单数量[增加的仓位,{订单的ID:已经成交的仓位},成交后变化后的仓位,变化前的仓位]
    :param trd_side: 方向
    :param dealt_qty: 本次成效数量
    :param push_id: 订单的ID
    :param order_status: 订单状态
    :return:
    """

    # 判断订单方向（增加减少可卖数量单位（手））
    if trd_side == 'BUY':
        # 如果订单已有成交过
        if CAN_SELL_QTY[1].get(push_id) != None:
            CAN_SELL_QTY[0] = dealt_qty - CAN_SELL_QTY[1][push_id]
            CAN_SELL_QTY[1][push_id] = dealt_qty
            CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])
        # 如果订单第一次成交
        elif CAN_SELL_QTY[1].get(push_id) == None:
            CAN_SELL_QTY[0] = dealt_qty             # CAN_SELL_QTY[0]记录增加的值,只用于计算,时刻归零 1+ 2 = 3 记录 2
            CAN_SELL_QTY[1][push_id] = dealt_qty    # CAN_SELL_QTY[1]字典,key为订单号,值为已经成交的量 1+2 = 3 记录 3
            CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])  # CAN_SELL_QTY[2] 当前持有的仓位 已有仓位+ 临时仓位
    elif trd_side == 'SELL':
        # 如果订单已有成交过
        if CAN_SELL_QTY[1].get(push_id) != None:
            CAN_SELL_QTY[0] = 0 - (dealt_qty - CAN_SELL_QTY[1][push_id])
            CAN_SELL_QTY[1][push_id] = dealt_qty
            CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])
        # 如果订单第一次成交
        elif CAN_SELL_QTY[1].get(push_id) == None:
            CAN_SELL_QTY[0] = 0 - dealt_qty
            CAN_SELL_QTY[1][push_id] = dealt_qty
            CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])

    if order_status == 'FILLED_ALL' or order_status == 'CANCELLED_ALL':
        # 判断订单是否已经成交过
        if CAN_SELL_QTY[1].get(push_id) != None:
            # 撤单订单是已成交订单，删除成交订单
            del CAN_SELL_QTY[1][push_id]

def order_log(order_status, push_code, push_price, premium, a,pull_the_market, dealt_qty, push_id, trd_side):
    """
    :param order_status:    推送订单的状态
    :param push_code:       代码
    :param push_price:      价格
    :param premium:         当前溢价
    :param a:               记录的调价点
    :param pull_the_market: 当前行情的点位和百分比
    :param dealt_qty:       仓位
    :param push_id:         订单ID
    :param trd_side:        订单方向
    :return:
    """
    logger.info('【{}】|{}|{}|{}|{}|【{}】|{}|{}|{}'.format(str(order_status)[:9].ljust(9), push_code, str(push_price)[:5].ljust(5), str(premium)[:5].ljust(5), str(a)[:10].ljust(10),
                                                               str(pull_the_market)[:17].ljust(17), dealt_qty, str(push_id)[:10].ljust(10), trd_side))


def on_order_status(data):
    """
    订单变化推送
    :param data: 订单数据
    :return:
    """
    push_code = data['code'][0]
    if push_code == TRADING_SECURITY:
        push_price = data['price'][0]               # 推送价格
        push_id = data['order_id'][0]               # 推送订单ID
        order_status = data['order_status'][0]      # 推送订单的状态
        dealt_qty = data['dealt_qty'][0]            # 成交数量
        trd_side = data['trd_side'][0]
        premium = round(PREMIUM[1] * 100, 2)        # 当前溢价
        a = IMMOBILIZATION_SET[push_price][3]       # 推送跳价点
        pull_price, pull_percentage = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)

        if pull_price != 0:
            c = (round(pull_price - a, 3))
            pull_the_market = '{}|{}|{}'.format(str(pull_price)[:7].ljust(7), str(pull_percentage)[:4].ljust(4), str(c)[:4].ljust(4))
        else:
            pull_the_market = 'null'
        # 已提交，等待成交
        if order_status == 'SUBMITTED':
            IMMOBILIZATION_SET[push_price][5] = push_id
            IMMOBILIZATION_SET[push_price][6] = trd_side
            order_log(order_status, push_code, push_price, premium, a, pull_the_market, dealt_qty, push_id, trd_side)
        # 撤单
        elif order_status == 'CANCELLED_ALL':
            filled(trd_side, dealt_qty, push_id, order_status)
            IMMOBILIZATION_SET[push_price][5] = '-1'
            IMMOBILIZATION_SET[push_price][6] = '-1'
            order_log(order_status, push_code, push_price, premium, a, pull_the_market, dealt_qty, push_id, trd_side)
        # 全部成交
        elif order_status == 'FILLED_ALL':
            filled(trd_side, dealt_qty, push_id, order_status)
            IMMOBILIZATION_SET[push_price][5] = '-1'
            IMMOBILIZATION_SET[push_price][6] = '-1'
            order_log(order_status, push_code, push_price, premium, a, pull_the_market, dealt_qty, push_id, trd_side)
        # 部分成交
        elif order_status == 'FILLED_PART':
            filled(trd_side, dealt_qty, push_id, order_status)
            order_log(order_status, push_code, push_price, premium, a, pull_the_market, dealt_qty, push_id, trd_side)



################################ 框架实现部分，可忽略不看 ###############################
class OrderBookClass(OrderBookHandlerBase):
    """
    实时摆盘数据推送框架
    """
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookClass, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error("OrderBookTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open(data)
        return RET_OK, data


class OnOrderClass(TradeOrderHandlerBase):
    """
    成交订单推送挂架
    """
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OnOrderClass, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            try:
                on_order_status(data)
            except Exception as e:
                logger.exception(e)
                logger.error('订单发生错误发生错误 撤单处理')

################################ 外部调用 ###############################
# 重置
def quote_context_reset():
    global PRESENT
    global MARKET_SECURITY
    global TRADING_SECURITY
    global PRESENT_CACHE
    global THEORETICAL_PRICE
    try:
        # 取消当前连接相关行情订阅quote_context对象，code_list列表，subtype_list列表 unsubscribe_all bool
        # quote_context_unsub(quote_context, code_list=[MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER], unsubscribe_all=False)
        # 记录撤单代码
        code = TRADING_SECURITY
        # 防止订阅时间过短 继续推送数据
        logger.debug(f'重置代码:{TRADING_SECURITY}价格：{PRESENT_CACHE}')
        TRADING_SECURITY = 'HK.00000'
        quote_context_front(code, PRESENT_CACHE, JUMP_MINIMUM_UNIT)
        TRADING_SECURITY = 'HK.00000'
        quote_context_unsub(quote_context)
        quote_context_unsub(trade_context)
    except Exception as e:
        initialization_immobilization_set()     # 初始化程序列表
        logger.info('错误执行初始化代码')
        logger.info(e)
    finally:
        # 初始化参数
        initialization_immobilization_set()     # 初始化程序列表
        PRESENT = 0
        PRESENT_CACHE = 0
        THEORETICAL_PRICE = 0
        logger.info('错误执行初始化代码FINALLY，行情代码和交易代码重置为HK.00000')

# 关闭
def quote_context_close():
    quote_context_reset()    # 关闭 相关连接
    quote_context.close()
    trade_context.close()


# 外部调用启动或修改变量方法
def submit_run(market_security, trading_security, trading_num, call_paragraph, put_paragraph, order_quantity
               , order_size, market_small_wrt_ratio, pass_word,  or_cancel_all, trading_sensitivity):
    global MARKET_SECURITY
    global TRADING_SECURITY
    global TRADING_NUM
    global CALL_PARAGRAPH
    global PUT_PARAGRAPH
    global ORDER_QUANTITY
    global ORDER_SIZE
    global MARKET_SMALL_WRT_RATIO
    global TRADING_PWD
    global OR_CANCEL_ALL
    global TRADING_SENSITIVITY
    global CACHE_SUBMIT_LIST
    # 校验前台有真事数据
    if trading_security != None and trading_num != None:
        # 修改数据
        if 'HK.' + trading_security == TRADING_SECURITY:
            MARKET_SECURITY = 'HK.' + market_security  # 标的参考代码
            TRADING_SECURITY = 'HK.' + trading_security  # 交易标的
            TRADING_NUM = trading_num  # 交易目标经纪号
            CALL_PARAGRAPH = int(call_paragraph) / 100  # 买入点
            PUT_PARAGRAPH = int(put_paragraph) / 100  # 卖出点
            ORDER_QUANTITY = int(order_quantity)  # 挂单量
            ORDER_SIZE = [1, int(order_size), int(order_size)]  # 订单量 单位手默认1手
            MARKET_SMALL_WRT_RATIO = float(market_small_wrt_ratio)
            TRADING_PWD = pass_word
            OR_CANCEL_ALL = int(or_cancel_all)
            TRADING_SENSITIVITY = 1 / float(trading_sensitivity)  # 波动率

            logger.info('************    修改交易数据    ***********')
            get_market_snapshot()  # 拉去相关数据
            # 订阅标的合约的 逐笔，K 线和摆盘，以便获取数据
            quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY],
                                    subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
            quote_context.subscribe(code_list=[STOCK_OWNER], subtype_list=[SubType.QUOTE])
            logger.info('重新订阅成功，开始交易')
            logger.info('************    修改交易数据完成    ***********')
        # 初始化
        else:
            MARKET_SECURITY = 'HK.' + market_security  # 标的参考代码
            TRADING_SECURITY = 'HK.' + trading_security  # 交易标的
            TRADING_NUM = trading_num  # 交易目标经纪号
            CALL_PARAGRAPH = int(call_paragraph) / 100  # 买入点
            PUT_PARAGRAPH = int(put_paragraph) / 100  # 卖出点
            ORDER_QUANTITY = int(order_quantity)  # 挂单量
            ORDER_SIZE = [1, int(order_size), int(order_size)]  # 订单量 单位手默认1手
            MARKET_SMALL_WRT_RATIO = float(market_small_wrt_ratio)
            TRADING_PWD = pass_word
            OR_CANCEL_ALL = int(or_cancel_all)
            TRADING_SENSITIVITY = 1 / float(trading_sensitivity)  # 波动率

            logger.info('************    初始化    ***********')
            # 初始化策略
            if not on_init():
                logger.error('策略初始化失败，脚本退出！')
                quote_context.close()
                trade_context.close()
            else:
                get_market_snapshot()  # 拉去相关数据
                initialization_immobilization_set()  # 初始化列表
                # 设置回调
                quote_context.set_handler(OrderBookClass())  # 摆盘回调
                trade_context.set_handler(OnOrderClass())  # 订单回调STOCK_OWNER
                # 订阅标的合约的 逐笔，K 线和摆盘，以便获取数据
                quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY],
                                        subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
                quote_context.subscribe(code_list=[STOCK_OWNER], subtype_list=[SubType.QUOTE])
                logger.info('订阅成功，开始交易')
                logger.info('************  策略开始运行 ***********')


