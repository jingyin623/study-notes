#coding=utf-8
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
import random
import winsound
from futu import *
import logging
# 导入日志配置文件
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
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
CAN_SELL_QTY = [0, {}, 0, 0]            # 全局仓位变量当前卖单数量和已经存在的卖单数量
PRESENT_TEST = 0                        # 恶意撤单时的价格记录器
FORECAST_LIST = []                      # QT5显示数据列表
WRT_TYPE = ''                           # 涡轮方向
WRT_CONVERSION_RATIO = 0                # 涡轮换股比例
WRT_RATIO = 0                           # 涡轮理论敏感度
JUMP_MINIMUM_UNIT = 0.001               # 最小跳价点
THEORETICAL_PRICE = 0                   # 当前行情正股对应价格(实际)
STOCK_OWNER = ''                        # 正股代码
PREMIUM = [0, 0]                        # 当前行情正股对应价格(实际)与(理论)[溢价点数,溢价百分比]
WRT_STRIKE_PRICE = 0                    # 涡轮行权价
CASH = 0                                # 现金购买力

TRADING_PWD = '536386'                  # 用户交易密码,用于解锁交易
OR_CANCEL_ALL = 0                       # 用户应对庄家撤单行为参数,(0撤单,1不撤单)
TRIM_PARAGRAPH = [200/100, 200/100]     # 用户微调参数行情剧烈波动[实际值,用户设定值]
MARKET_SMALL_WRT_RATIO = 1              # 用户参考系行情的最低波动率
CALL_PARAGRAPH = 700 / 100              # 用户开始买入参数
PUT_PARAGRAPH = 400 / 100               # 用户开始卖出参数
ORDER_QUANTITY = 3                      # 用户挂单量参数
ORDER_SIZE = [0, 1, 0]                  # 用户仓位参数 单位手默认0手[当前使用仓位,用户输入仓位,最大风险仓位]
MARKET_SECURITY = 'HK.HSImain'          # 用户参考系行情代码
TRADING_SECURITY = 'HK.58298'           # 用户交易标的代码
TRADING_NUM = '1'                       # 用户追踪经纪号

quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)   # 行情对象
trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT,
                                    security_firm=SecurityFirm.FUTUSECURITIES)  # 交易对象，根据交易品种修改交易对象类型
############################ 全局变量设置 ############################


# 判断交易标的类型 相关信息
def get_market_snapshot():
    global WRT_TYPE
    global WRT_CONVERSION_RATIO
    global WRT_RATIO
    global STOCK_OWNER
    global WRT_STRIKE_PRICE
    global CASH
    ret, data = trade_context.accinfo_query()
    if ret == RET_OK:
        CASH = data['cash'][0]
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
            logger.info('正股代码：{} '.format(MARKET_SECURITY))
            logger.info('涡轮代码：{} | 涡轮方向：{} | 目标经纪号：{} | 换股比例：{} | 现金购买力: {}' \
                        .format(TRADING_SECURITY, WRT_TYPE, TRADING_NUM, WRT_CONVERSION_RATIO, CASH))
            logger.info('理论波动率 ： 默认等于理论灵敏度-->{}'.format(WRT_RATIO))
            logger.info('买入开始：{} | 卖出开始：{} | 挂单量：{} | 仓位：{}  | 是否跟随撤单(0跟随其他不跟随)：{} | 微调价格：{}' \
                        .format(CALL_PARAGRAPH, PUT_PARAGRAPH, ORDER_QUANTITY, ORDER_SIZE, OR_CANCEL_ALL, TRIM_PARAGRAPH))
    else:
        logger.error('error:', data)


# 初始化字典 备用列表
def initialization_immobilization_set():
    global IMMOBILIZATION_SET
    IMMOBILIZATION_SET.clear()
    logger.debug("初始化记录值字典默认[-1, -1, -1, '-1', '-1']（0-0.250）")
    num = 0
    while num <= 250:
        # [价格，记录值，百分比，订单号，买卖方向]
        IMMOBILIZATION_SET[round((num * 0.001), 3)] = [-1, -1, -1, '-1', '-1']
        num = num + 1


def error_beep():
    logger.error("请注意: -->程序出错了，程序出错了")
    for i in range(2) : winsound.Beep(1000, 500)


# 庄家撤单处理
def farmhouse_cancel_position(code, present, jump_minimum_unit):
    if present > 0:
        # 优先撤当前订单
        if int(IMMOBILIZATION_SET[present][3]) > 1:
            up_cancel_position(present, IMMOBILIZATION_SET[present][3])
            logger.debug(' 庄家撤单：撤相关订单--订单价格 |' + str(present))
        num = 2
        while num >= -10:
            # 目标价格是有订单-撤单(-1 没有订单)
            if int(IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][3]) > 1:
                up_cancel_position(round(present + num * jump_minimum_unit, 3),
                                   IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][3])
                logger.debug('庄家撤单：撤相关订单--订单价格 |' + str(round(present + num * jump_minimum_unit, 3)))
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
            up_open_position(code, present, can_sell_qty, 'SELL')
            logger.debug(f'庄家撤单 卖出价格{present},仓位{can_sell_qty}')


# 取消交易相关订阅
def quote_context_unsub(code_list, subtype_list, unsubscribe_all=False):
    ret_unsub, err_message_unsub = quote_context.unsubscribe(code_list=code_list, subtype_list=subtype_list, unsubscribe_all=unsubscribe_all)
    if ret_unsub == RET_OK:
        logger.info(f'unsubscribe successfully！current subscription status:{quote_context.query_subscription()}')  # 取消订阅后查询订阅状态
    else:
        logger.error(f'unsubscription failed！{err_message_unsub}')


# 重置和关闭和错误执行取消前交易操作，卖出持仓
def quote_context_front(code, present, jump_minimum_unit):
    if present >= 0.010:
        num = -9
        while num <= 10:
            # 目标价格是有订单-撤单(-1 没有订单)
            if int(IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][3]) > 0:
                up_cancel_position(round(present + num * jump_minimum_unit, 3),
                                   IMMOBILIZATION_SET[round(present + num * jump_minimum_unit, 3)][3])
                logger.debug(' 关闭前操作：撤相关订单--订单价格 |' + str(round(present + num * jump_minimum_unit, 3)))
            num = num + 1
    ret, data = trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=0.010)
    can_sell_qty = 0
    if ret == RET_OK:
        can_sell_qty = data['max_position_sell'][0]
        logger.info(f'持仓最大可卖数量：{can_sell_qty}')  # 最大融资可买数量
    else:
        logger.error('acctradinginfo_query error: ', data)
    # 有持仓 卖出持仓（0 没有持仓）
    if can_sell_qty > 0:
        ret, data = quote_context.get_order_book(code, num=2)  # 获取一次 1 档实时摆盘数据
        if ret == RET_OK:
            num = 0
            push_can_buy_qty = 0
            while num <= 2:
                bid_price = data['Bid'][num][0]
                push_can_buy_qty = push_can_buy_qty + data['Bid'][num][1]
                if can_sell_qty <= push_can_buy_qty:
                    up_open_position(code, bid_price, can_sell_qty, 'SELL')
                    break
                num = num + 1
        else:
            logger.error('error:', data)
    initialization_immobilization_set()     # 初始化程序列表


#  预测值 并显示相关信息
def modify_immobilization_set(push_set_price, call_or_put):
    pushPriceList = []
    if push_set_price[0] <= 0.250:
        num = -5  # 计数器
        while num <= 5:
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][0] = round(push_set_price[0] + (num * 0.001), 3)
            if call_or_put == 'BULL' or call_or_put == 'CALL':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1] + 0.001 * push_set_price[2] + (num * WRT_RATIO), 5)
            elif call_or_put == 'BEAR' or call_or_put == 'PUT':
                IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][1] = round(push_set_price[1] + 0.001 * push_set_price[2] - (num * WRT_RATIO), 5)
            IMMOBILIZATION_SET[round(push_set_price[0] + (num * 0.001), 3)][2] = push_set_price[2]
            num = num + 1
        num = -3
        while num <= 3:
            pushPriceList.append(round((push_set_price[0] + num * 0.001), 3))
            num = num + 1
    pull_print_list(pushPriceList)      # 打印相关信息


# 打印列表
def pull_print_list(push_price_list):
    FORECAST_LIST.clear()       # 清除列表数据
    # 遍历所有相关价格
    for key in push_price_list:
        FORECAST_LIST.append(' '.join(map(str, IMMOBILIZATION_SET.get(key))))  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
    # if PROJECT_STATUS == 1:
    #     FORECAST_LIST.append(' 程序出错了')  # 先将要连接的所有元素转化为字符串形式str,再进行join 操作
    # logger.debug(FORECAST_LIST)


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
    else:
        logger.error('error:', data)
    return bid_list


# 返回目标经纪号所在的价格(交易代码，交易经纪号，买盘数据，买盘数据，最小跳价点，当前价格)
def find_order_price(push_code, trading_num, bid):
    ret, bid_frame_table, ask_frame_table = quote_context.get_broker_queue(push_code)  # 获取一次经纪队列数据
    bid_price = 0
    if ret == RET_OK:
        pos = 0
        for indexs in bid_frame_table.index:
            bid_broker_id = bid_frame_table.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
            bid_broker_pos = bid_frame_table.at[indexs, 'bid_broker_pos']  # 经纪档位
            if bid_broker_id == int(trading_num):
                pos = bid_broker_pos  # 经纪号所在得档位
                break
        if pos != 0:
            bid_price = bid[pos - 1][0]
        # 没有找到目标经济号买盘信息
        else:
            bid_price = 0
        return bid_price
    else:
        logger.error(f'error:{bid_frame_table}')
        return bid_price


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
    open_quantity = order_size      # 计算下单量
    # 判断购买力是否足够
    if is_valid_quantity(code, open_quantity, price):
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
    IMMOBILIZATION_SET[bid_share_price][3] = 0
    order_id = open_position(trading_security, bid_share_price, order_size, buy_or_sell)
    IMMOBILIZATION_SET[bid_share_price][3] = order_id
    IMMOBILIZATION_SET[bid_share_price][4] = buy_or_sell


#  改单
def modify_position(code, order_id, price, order_size):
    open_quantity = order_size      # 计算下单量
    ret, data = trade_context.modify_order(modify_order_op=ModifyOrderOp.NORMAL, order_id=order_id, price=price,
                                           qty=open_quantity, trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        pass
    else:
        logger.error('modify_order error: ', data)

#  改单(交易代码，当前价格，目标价格，订单ID，仓位，买卖方向)
def up_modify_position(trading_security, bid_share_price, target_bid_share_price, order_id, order_size, buy_or_sell):
    IMMOBILIZATION_SET[bid_share_price][3] = 0
    IMMOBILIZATION_SET[target_bid_share_price][3] = 0
    modify_position(trading_security, order_id, target_bid_share_price, order_size)
    IMMOBILIZATION_SET[target_bid_share_price][3] = order_id
    IMMOBILIZATION_SET[target_bid_share_price][4] = buy_or_sell
    IMMOBILIZATION_SET[bid_share_price][3] = '-1'
    IMMOBILIZATION_SET[bid_share_price][4] = '-1'


#  撤单
def cancel_position(order_id):
    ret, data = trade_context.modify_order(modify_order_op=ModifyOrderOp.CANCEL, order_id=order_id, price=0,
                                           qty=0, trd_env=TRADING_ENVIRONMENT)
    if ret == RET_OK:
        pass
    else:
        logger.error('modify_order error: ' + data)


#  撤单(当前价格， 订单ID)
def up_cancel_position(bid_share_price, order_id):
    IMMOBILIZATION_SET[bid_share_price][3] = 0
    cancel_position(order_id)
    IMMOBILIZATION_SET[bid_share_price][3] = '-1'
    IMMOBILIZATION_SET[bid_share_price][4] = '-1'
    # 判断订单是否已经成交过
    if CAN_SELL_QTY[1].get(order_id) != None:
        del CAN_SELL_QTY[1][order_id]


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

# 微调买入百分比
def get_trim():
    put_trim = 0
    premium = round(PREMIUM[1] * 100, 2)
    if '09:01:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '10:00:00' \
            or '13:00:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '13:05:00':
        TRIM_PARAGRAPH[0] = TRIM_PARAGRAPH[1] * 2
    else:
        TRIM_PARAGRAPH[0] = TRIM_PARAGRAPH[1]
    if premium >= 0:
        put_trim = TRIM_PARAGRAPH[0] * 1
    elif 0 > premium >= -0.05:
        put_trim = TRIM_PARAGRAPH[0] * 0.8
    elif -0.05 > premium >= -0.10:
        put_trim = TRIM_PARAGRAPH[0] * 0.6
    elif -0.10 > premium >= -0.15:
        put_trim = TRIM_PARAGRAPH[0] * 0.4
    elif -0.15 > premium >= -0.20:
        put_trim = TRIM_PARAGRAPH[0] * 0.2
    elif -0.20 > premium >= -0.25:
        put_trim = TRIM_PARAGRAPH[0] * 0
    if PRESENT == 0:
        put_trim = TRIM_PARAGRAPH[0] * 2
    return round(put_trim, 2)


def selected_price_1(pull_the_market, wrt_type, present):
    global THEORETICAL_PRICE
    # 认购定价
    if wrt_type == 'BULL' or wrt_type == 'CALL':
        num = -1
        while num <= 5:
            # 记录值在记录值之间
            if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][1] \
                    <= round(pull_the_market[0] + pull_the_market[1] * JUMP_MINIMUM_UNIT, 5) < \
                    IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][1]:
                THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]   # 确定交易价位
            num = num + 1
        num = -5
        while num <= -1:
            if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][1] \
                    <= round(pull_the_market[0] + pull_the_market[1] * JUMP_MINIMUM_UNIT, 5) < \
                    IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][1]:
                THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]
            num = num + 1
    # 认沽定价
    if wrt_type == 'BEAR' or wrt_type == 'PUT':
        num = -1
        while num <= 5:
            if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][1] \
                    >= round(pull_the_market[0] + pull_the_market[1] * JUMP_MINIMUM_UNIT, 5) \
                    > IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][1]:
                # 确定交易价位
                THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]
            num = num + 1
        num = -5
        while num <= -1:
            if IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][1] \
                    >= round(pull_the_market[0] + pull_the_market[1] * JUMP_MINIMUM_UNIT, 5) \
                    > IMMOBILIZATION_SET[round(present + (num + 1) * JUMP_MINIMUM_UNIT, 3)][1]:
                # 确定交易价位
                THEORETICAL_PRICE = IMMOBILIZATION_SET[round(present + num * JUMP_MINIMUM_UNIT, 3)][0]
            num = num + 1


# 选定当前行情对应价格
def selected_price(pull_the_market, wrt_type):
    if PRESENT > 0:
        selected_price_1(pull_the_market, wrt_type, PRESENT)
    if PRESENT == 0 and PRESENT_TEST != 0:
        selected_price_1(pull_the_market, wrt_type, PRESENT_TEST)


# 买入段和清理（记录值+缓冲值买入 高低位订单处理）
def buy_paragraph(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log, buy=True):
    # 处理高位位的多BUY 单和 多余SELL单sharePrice + (num + 1) * jumpMinimumUnit
    # 处理了当前价格以上的买单和当前价格+1以上的卖单
    if buy == True:
        num = 1
        while num <= 10:
            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            if int(IMMOBILIZATION_SET[round(sharePrice + num * jumpMinimumUnit, 3)][3]) > 1:
                # 订单是买入订单
                if IMMOBILIZATION_SET[round(sharePrice + num * jumpMinimumUnit, 3)][4] == 'BUY':
                    logger.debug(f'买入段-BUY单 -撤单|价格:{sharePrice}-高位多余订单-溢价{log[0]}-微调点位{log[1]}')
                    #  撤单(当前价格， 订单ID)
                    up_cancel_position(round(sharePrice + num * jumpMinimumUnit, 3),
                                       IMMOBILIZATION_SET[round(sharePrice + num * jumpMinimumUnit, 3)][3])
                if IMMOBILIZATION_SET[round(sharePrice + (num + 1) * jumpMinimumUnit, 3)][4] == 'SELL':
                    logger.debug(f'买入段-SELL单-撤单|价格:{sharePrice}-高位多余订单-溢价{log[0]}-微调点位{log[1]}')
                    #  撤单(当前价格， 订单ID)
                    up_cancel_position(round(sharePrice + (num + 1) * jumpMinimumUnit, 3),
                                       IMMOBILIZATION_SET[
                                           round(sharePrice + (num + 1) * jumpMinimumUnit, 3)][3])
            num = num + 1

        #   处理当前价格低位的多余BUY单
        num = 0
        while num <= 5:
            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            if int(IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit - num * jumpMinimumUnit, 3)][3]) > 1:
                logger.debug(f'买入段-BUY单 -撤单|价格:{sharePrice}-低位多余订单-溢价{log[0]}-微调点位{log[1]}')
                #  撤单(当前价格， 订单ID)
                up_cancel_position(round(sharePrice - orderQuantity * jumpMinimumUnit - num * jumpMinimumUnit, 3),
                                   IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit - num * jumpMinimumUnit, 3)][3])

            #  7. 目标价格是有订单(-1 没有订单,改单撤单)
            if int(IMMOBILIZATION_SET[round(sharePrice - num * jumpMinimumUnit, 3)][3]) > 1 \
                    and IMMOBILIZATION_SET[round(sharePrice - num * jumpMinimumUnit, 3)][4] == 'SELL':
                logger.debug(f'买入段-SELL单-撤单|价格:{sharePrice}-低位多余订单-溢价{log[0]}-微调点位{log[1]}')
                #  撤单(当前价格， 订单ID)
                up_cancel_position(round(sharePrice - num * jumpMinimumUnit, 3),
                                   IMMOBILIZATION_SET[round(sharePrice - num * jumpMinimumUnit, 3)][3])
            num = num + 1

    #   卖出订单如果是部分成交 修改订单
    if int(IMMOBILIZATION_SET[round(sharePrice + jumpMinimumUnit, 3)][3]) > 1 and \
            IMMOBILIZATION_SET[round(sharePrice + jumpMinimumUnit, 3)][4] == 'SELL' and CAN_SELL_QTY[2] != CAN_SELL_QTY[3]:

        up_cancel_position(round(sharePrice + jumpMinimumUnit, 3), IMMOBILIZATION_SET[round(sharePrice + jumpMinimumUnit, 3)][3])
        logger.debug(f'买入段-SELL单-撤单|价格{sharePrice}-仓位{CAN_SELL_QTY}-有订单 有持仓 （部分成交）-溢价{log[0]}-微调点位{log[1]}')
        # 卖出订单
        up_open_position(tradingSecurity, round(sharePrice + jumpMinimumUnit, 3), CAN_SELL_QTY[2], 'SELL')
        CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
        logger.debug(f'买入段-SELL单-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有订单 有持仓-溢价{log[0]}-微调点位{log[1]}')

    #   卖出价格没有订单且有成交订单任务
    if IMMOBILIZATION_SET[round(sharePrice + jumpMinimumUnit, 3)][3] == '-1' and CAN_SELL_QTY[2] != 0:
        if CAN_SELL_QTY[2] != CAN_SELL_QTY[3]:
            up_open_position(tradingSecurity, round(sharePrice + jumpMinimumUnit, 3), CAN_SELL_QTY[2], 'SELL')
        CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
        logger.debug(f'买入段-SELL单-卖出|价格{round(sharePrice + jumpMinimumUnit, 3)}-仓位{CAN_SELL_QTY}-无订单 有持仓-溢价{log[0]}-微调点位{log[1]}')

    # 5，没有订单记录 订单价格大于等0.010 且已有仓位小于所有订单仓位的一般买入任务（不等于-1为真，其他取反）
    if IMMOBILIZATION_SET[sharePrice][3] == '-1' and round(sharePrice, 3) >= 0.011 and \
            CAN_SELL_QTY[2] < orderSize and buy == True:
        # 修改下单数量为随机数量
        scq = small_calculate_quantity(TRADING_SECURITY)
        orderSize = (orderSize/scq + random.randint(0, 2)) * scq
        # 下单函数 (代码，价格，大小，方向)
        up_open_position(tradingSecurity, sharePrice, orderSize, 'BUY')
        logger.debug(f'买入段-BUY单 -买入|价格{sharePrice}-仓位{orderSize} 没有订单-溢价{log[0]}-微调点位{log[1]}')


# 撤退段 + 卖出段（撤单，在卖）
def sell_paragraph(tradingSecurity, orderSize, sharePrice, orderQuantity, jumpMinimumUnit, log):
    # #   清理高位所有订单
    num = 1
    while num <= 5:
        #  7. 目标价格是有订单(-1 没有订单,改单撤单)
        if int(IMMOBILIZATION_SET[round(sharePrice + num * jumpMinimumUnit, 3)][3]) > 1:
            #  撤单(当前价格， 订单ID)
            up_cancel_position(round(sharePrice + num * jumpMinimumUnit, 3),
                               IMMOBILIZATION_SET[round(sharePrice + num * jumpMinimumUnit, 3)][3])
            logger.debug(f'撤退段-SorB单-撤单|价格:{sharePrice}-高位多余订单-溢价{log[0]}-微调点位{log[1]}')
        num = num + 1

    # 5，有订单（不等于-1为真，其他取反）
    if int(IMMOBILIZATION_SET[sharePrice][3]) > 1:
        # . 订单类型是买单类型。改单撤单处理
        if IMMOBILIZATION_SET[sharePrice][4] == 'BUY':
            #  6. 目标价位没有订单(-1 没有订单,改单处理)
            if IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit, 3)][3] == '-1':
                # 7. 目标价格大于等于最低价格
                if sharePrice >= round(0.011 + orderQuantity * jumpMinimumUnit, 3):
                    # 修改下单数量为随机数量
                    scq = small_calculate_quantity(TRADING_SECURITY)
                    orderSize = (orderSize / scq + 2) * scq
                    #  改单(交易代码，当前价格，目标价格，订单ID，仓位，买卖方向)
                    up_modify_position(tradingSecurity, sharePrice,
                                       round(sharePrice - orderQuantity * jumpMinimumUnit, 3),
                                       IMMOBILIZATION_SET[sharePrice][3], orderSize, 'BUY')
                    logger.debug(f'撤退段-BUY单 -改单|价格{sharePrice}-->{round(sharePrice - orderQuantity * jumpMinimumUnit, 3)}-有订单 目标没有订单且大于0.010-溢价{log[0]}-微调点位{log[1]}')
                # 7. 目标价格大于等于最低价格
                elif sharePrice < round(0.011 + orderQuantity * jumpMinimumUnit, 3):
                    #  撤单(当前价格， 订单ID)
                    up_cancel_position(sharePrice, IMMOBILIZATION_SET[sharePrice][3])
                    logger.debug(f'撤退段-BUY单 -撤单|价格{sharePrice}-有订单 目标没有订单且小于0.010-溢价{log[0]}-微调点位{log[1]}')
            #  6. 目标价位已经有订单(-1 没有订单,改单处理)
            elif int(IMMOBILIZATION_SET[round(sharePrice - orderQuantity * jumpMinimumUnit, 3)][3]) > 1:
                logger.debug(f'撤退段-BUY单 -撤单|价格{sharePrice}-有订单 目标没有订单-溢价{log[0]}-微调点位{log[1]}')
                #  撤单(当前价格， 订单ID)
                up_cancel_position(sharePrice, IMMOBILIZATION_SET[sharePrice][3])
        # 订单类型是卖单类型。改单撤单处理
        if IMMOBILIZATION_SET[sharePrice][4] == 'SELL' and CAN_SELL_QTY[2] != CAN_SELL_QTY[3]:
            up_cancel_position(sharePrice, IMMOBILIZATION_SET[sharePrice][3])
            logger.debug(f'撤退段-SELL-撤单|价格{sharePrice}-成交前前仓位{CAN_SELL_QTY[2]}-且持仓改变-溢价{log[0]}-微调点位{log[1]}')
            up_open_position(tradingSecurity, sharePrice, CAN_SELL_QTY[2], 'SELL')
            CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
            logger.debug(f'撤退段-SELL-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有持仓-溢价{log[0]}-微调点位{log[1]}')

    # 5，无订单 卖出（不等于-1为真，其他取反）
    elif IMMOBILIZATION_SET[sharePrice][3] == '-1' and CAN_SELL_QTY[2] != 0:
        up_open_position(tradingSecurity, sharePrice, CAN_SELL_QTY[2], 'SELL')
        CAN_SELL_QTY[3] = CAN_SELL_QTY[2]
        logger.debug(f'撤退段-SELL-卖出|价格{sharePrice}-仓位{CAN_SELL_QTY[2]}-有持仓-溢价{log[0]}-微调点位{log[1]}')


############################ 填充以下函数来完成您的策略 ############################
def auto_order_size(present):
    ORDER_SIZE[2] = int(((CASH / present) / small_calculate_quantity(TRADING_SECURITY)) / (ORDER_QUANTITY + 2))
    logger.debug(ORDER_SIZE)
    if ORDER_SIZE[1] == 0:
        ORDER_SIZE[0] = ORDER_SIZE[2]
    if ORDER_SIZE[1] > ORDER_SIZE[2]:
        ORDER_SIZE[1] = ORDER_SIZE[2]
        ORDER_SIZE[0] = ORDER_SIZE[2]


def on_bar_open(data):
    global ORDER_QUANTITY
    global PRESENT
    global PRESENT_TEST
    global MARKET_SMALL_WRT_RATIO
    global THEORETICAL_PRICE

    push_code = data['code']  # 推送的代码
    # 找到交易标的 确定交易时间
    if push_code == TRADING_SECURITY and ('09:01:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '11:59:40' or
            '13:00:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '15:59:40'):
        # 找到目标经纪号所在的理论价格（代码，经纪号，所有买盘数据）
        push_price = find_order_price(push_code, TRADING_NUM, data['Bid'])
        # 推送价格大于价格记录器（庄家买入）
        if push_price > PRESENT:
            # 庄家撤单后重新更新价格记录器
            if PRESENT == 0:
                # 拉取一次行情数据，行情第一档得价格和百分比类型list
                pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
                # 修改字典相关数据[list, WRT_TYPE]
                modify_immobilization_set([push_price, pull_the_market[0], pull_the_market[1]], WRT_TYPE)
            auto_order_size(push_price)    # 计算仓位
            PRESENT = push_price          # 更新价格记录器
            # 记录数据以备分析
            logger1.debug(push_code + '--' + str(push_price))
        # 推送价格小于价格记录器（庄家买入）
        if push_price < PRESENT:
            # 当前价格有订单撤退当前价格
            if int(IMMOBILIZATION_SET[PRESENT][3]) > 1:
                up_cancel_position(PRESENT, IMMOBILIZATION_SET[PRESENT][3])
            # 庄家因撤单导致价格小于价格记录器，同时庄家撤单
            if push_price == 0:
                PRESENT_TEST = PRESENT
                if OR_CANCEL_ALL == 0:
                    farmhouse_cancel_position(push_code, PRESENT, JUMP_MINIMUM_UNIT)
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 修改字典相关数据[list, WRT_TYPE]
            modify_immobilization_set([PRESENT, pull_the_market[0], pull_the_market[1]], WRT_TYPE)
            auto_order_size(PRESENT)    # 计算仓位
            PRESENT = push_price          # 更新价格记录器
            # 记录数据以备分析
            logger1.debug(push_code + '--' + str(push_price))
        # 推送价格等于价格记录器（庄家在原地没动的时候）
        if push_price == PRESENT:
            # 庄家持续撤单中
            if push_price == 0:
                pass
            pass

    # 找到推送行情数据的代码
    if push_code == MARKET_SECURITY:
        # 记录数据以备分析
        logger1.debug(data['code'] + '--' + str(data['Bid'][0][0]) + '--' + str(data['Ask'][0][0]))
        # 确定时间范围
        if '09:01:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '11:59:50' \
                or '13:00:00' <= time.strftime('%H:%M:%S', time.localtime()) <= '15:59:50':
            # 拉取一次行情数据，行情第一档得价格和百分比类型list
            pull_the_market = pull_the_market_security(MARKET_SECURITY, WRT_TYPE)
            # 2.当前市场对应理论价格
            selected_price(pull_the_market, WRT_TYPE)
            # 当前价格不等于空
            if THEORETICAL_PRICE != None and THEORETICAL_PRICE > 0:
                trim = get_trim()  # 获得微调百分比
                log = [round(PREMIUM[1] * 100, 2), trim]
                # 1.牛证
                if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
                    num_num = 0     # 整数位
                    num = IMMOBILIZATION_SET[THEORETICAL_PRICE][2] + CALL_PARAGRAPH + trim    # 百分比
                    while num >= 1:
                        num_num = num_num + 1
                        num = num - 1
                    # 行情大于 当前价格的 买入段
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            >= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] + num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        # 交易代码，交易仓位，交易价格，多少挂单， 最小调下点
                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log)

                    num_num = 0
                    num = IMMOBILIZATION_SET[THEORETICAL_PRICE][2] + PUT_PARAGRAPH + trim
                    while num >= 1:
                        num_num = num_num + 1
                        num = num - 1
                    # 行情小于 当前价格的 卖出段
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            <= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] + num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        # 交易代码，交易仓位，交易价格，多少挂单， 最小调下点
                        sell_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log)
                    # 行情在空窗期操作 执行买入段,但是不买入
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            > round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] + num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        # 交易代码，交易仓位，交易价格，多少挂单， 最小调下点
                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log, buy=False)
                # 2.熊
                if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
                    num_num = 0
                    num = IMMOBILIZATION_SET[THEORETICAL_PRICE][2] + CALL_PARAGRAPH + trim
                    while num >= 1:
                        num_num = num_num + 1
                        num = num - 1
                    # 行情小于 当前价格的 买入段
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            <= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] - num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        # 交易代码，交易仓位，交易价格，多少挂单， 最小调下点
                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log)

                    num_num = 0
                    num = IMMOBILIZATION_SET[THEORETICAL_PRICE][2] + PUT_PARAGRAPH + trim
                    while num >= 1:
                        num_num = num_num + 1
                        num = num - 1
                    # 行情大于 当前价格的 卖出段
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            >= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] - num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        sell_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log)
                    # 行情在空窗期操作 执行买入段,但是不买入
                    if round(pull_the_market[0] + pull_the_market[1] * 0.001, 5) \
                            >= round(IMMOBILIZATION_SET[THEORETICAL_PRICE][1] - num_num * MARKET_SMALL_WRT_RATIO + num * 0.001, 5):
                        buy_paragraph(TRADING_SECURITY, ORDER_SIZE[0], round(THEORETICAL_PRICE, 3), ORDER_QUANTITY, JUMP_MINIMUM_UNIT, log, buy=False)

        elif '16:00:00' > time.strftime('%H:%M:%S', time.localtime()) > '15:59:50' \
                or '12:00:00' > time.strftime('%H:%M:%S', time.localtime()) > '11:59:50':
            logger.info('当前时间[%s]不在交易时间段' % time.strftime('%H:%M:%S', time.localtime()))
            quote_context_reset()


# 实时报价推送
def on_quote_open(data):
    if THEORETICAL_PRICE != None:
        push_code = data['code'][0]  # 推送的代码
        # 找到交易标的 同时庄家
        if STOCK_OWNER == push_code and PRESENT > 0:
            last_price = data['last_price'][0]  # 最新价
            # UP方向溢价的计算方法 (实际行权点-当前实际价值)/当前实际价值
            if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
                real_value = THEORETICAL_PRICE * WRT_CONVERSION_RATIO + WRT_STRIKE_PRICE  # 实际行权点(轮价格 + 行权价)
                PREMIUM[0] = real_value - last_price  # 实际价值点数(实际行权点-当前点位)
                PREMIUM[1] = PREMIUM[0] / last_price  # 实际价值百分比
            # DOWN方向溢价甲酸方法()
            if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
                real_value = WRT_STRIKE_PRICE - THEORETICAL_PRICE * WRT_CONVERSION_RATIO  # 实际行权点(行权价 - 轮价格)
                PREMIUM[0] = last_price - real_value  # 实际价值点数(当前点位-实际行权点)
                PREMIUM[1] = PREMIUM[0] / last_price  # 实际价值百分比


# 订单变化推送
def on_order_status(data):
    global CAN_SELL_QTY
    # 赋值+初始化
    def num(a, b):
        a = a + b
        CAN_SELL_QTY[0] = 0
        return a

    def filled(trd_side, dealt_qty, push_id, order_status):
        # 判断订单方向（增加减少可卖数量单位（手））
        if trd_side == 'BUY':
            # 如果订单已有成交过
            if CAN_SELL_QTY[1].get(push_id) != None:
                CAN_SELL_QTY[0] = dealt_qty - CAN_SELL_QTY[1][push_id]
                CAN_SELL_QTY[1][push_id] = dealt_qty
                CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])
            # 如果订单第一次成交
            elif CAN_SELL_QTY[1].get(push_id) == None:
                CAN_SELL_QTY[0] = dealt_qty
                CAN_SELL_QTY[1][push_id] = dealt_qty
                CAN_SELL_QTY[2] = num(CAN_SELL_QTY[2], CAN_SELL_QTY[0])
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
            # IMMOBILIZATION_SET[push_price][3] = push_id
            # IMMOBILIZATION_SET[push_price][4] = trd_side
        # 撤单
        elif order_status == 'CANCELLED_ALL':
            filled(trd_side, dealt_qty, push_id, order_status)
            IMMOBILIZATION_SET[push_price][3] = '-1'
            IMMOBILIZATION_SET[push_price][4] = '-1'
            logger.info('【撤单信息】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))
        # 全部成交
        elif order_status == 'FILLED_ALL':
            filled(trd_side, dealt_qty, push_id, order_status)
            IMMOBILIZATION_SET[push_price][3] = '-1'
            IMMOBILIZATION_SET[push_price][4] = '-1'
            logger.info('【全部成交】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))

        # 部分成交
        elif order_status == 'FILLED_PART':
            filled(trd_side, dealt_qty, push_id, order_status)
            logger.info('【部分成交】' + '|' + str(push_code) + '|' + str(push_price) + '|' + str(dealt_qty) + '|' + str(push_id) + '|' + str(trd_side))



################################ 框架实现部分，可忽略不看 ###############################
class OrderBookClass(OrderBookHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookClass, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logger.error("OrderBookTest: error, msg: %s" % data)
            quote_context_front(TRADING_SECURITY, PRESENT, JUMP_MINIMUM_UNIT)
            error_beep()
            return RET_ERROR, data
        try:
            on_bar_open(data)
        except Exception as e:
            quote_context_front(TRADING_SECURITY, PRESENT, JUMP_MINIMUM_UNIT)
            logger.exception(e)
            error_beep()
        return RET_OK, data


class OnOrderClass(TradeOrderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, data = super(OnOrderClass, self).on_recv_rsp(rsp_pb)
        if ret == RET_OK:
            try:
                on_order_status(data)
            except Exception as e:
                logger.error('订单发生错误发生错误 撤单处理')
                logger.exception(e)
                error_beep()

class StockQuoteTest(StockQuoteHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(StockQuoteTest, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("StockQuoteTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_quote_open(data)
        return RET_OK, data


################################ 外部调用 ###############################
# 重置
def quote_context_reset():
    # 取消当前相关行情订阅
    quote_context_unsub(code_list=[MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER], unsubscribe_all=False)
    # 重置和关闭和错误执行取消前交易操作，卖出持仓
    quote_context_front(TRADING_SECURITY, PRESENT, JUMP_MINIMUM_UNIT)
    # 取消当前相关交易
    quote_context_unsub(code_list=[TRADING_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER], unsubscribe_all=False)


# 关闭
def quote_context_close():
    quote_context_reset()
    # 取消所有订阅
    quote_context_unsub(code_list=[TRADING_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER], unsubscribe_all=True)
    # 关闭 相关连接
    quote_context.close()
    trade_context.close()


def submit_run(market_security, trading_security, trading_num, call_paragraph, put_paragraph, order_quantity
               , order_size, market_small_wrt_ratio, pass_word,  or_cancel_all, trim_paragraph):
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
    global TRIM_PARAGRAPH
    # 修改数据
    if 'HK.' + trading_security == TRADING_SECURITY:
        MARKET_SECURITY = 'HK.' + market_security       # 标的参考代码
        TRADING_SECURITY = 'HK.' + trading_security  # 交易标的
        TRADING_NUM = trading_num  # 交易目标经纪号
        CALL_PARAGRAPH = int(call_paragraph) / 100  # 买入点
        PUT_PARAGRAPH = int(put_paragraph) / 100  # 卖出点
        ORDER_QUANTITY = int(order_quantity)  # 挂单量
        order_size = int(order_size) * small_calculate_quantity(TRADING_SECURITY)  # 订单量 单位手默认1手
        ORDER_SIZE = [order_size, order_size, order_size]
        MARKET_SMALL_WRT_RATIO = float(market_small_wrt_ratio)
        TRADING_PWD = pass_word
        OR_CANCEL_ALL = int(or_cancel_all)
        TRIM_PARAGRAPH = [int(trim_paragraph) / 100, int(trim_paragraph) / 100]

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
        MARKET_SECURITY = 'HK.' + market_security       # 标的参考代码
        TRADING_SECURITY = 'HK.' + trading_security  # 交易标的
        TRADING_NUM = trading_num                       # 交易目标经纪号
        CALL_PARAGRAPH = int(call_paragraph)/100        # 买入点
        PUT_PARAGRAPH = int(put_paragraph)/100          # 卖出点
        ORDER_QUANTITY = int(order_quantity)             # 挂单量
        order_size = int(order_size) * small_calculate_quantity(TRADING_SECURITY)  # 订单量 单位手默认1手
        ORDER_SIZE = [order_size, order_size, order_size]
        logger.debug('shuru{}'.format(ORDER_SIZE))
        MARKET_SMALL_WRT_RATIO = float(market_small_wrt_ratio)
        TRADING_PWD = pass_word
        OR_CANCEL_ALL = int(or_cancel_all)
        TRIM_PARAGRAPH = [int(trim_paragraph)/100, int(trim_paragraph)/100]

        logger.info('************    初始化    ***********')
        # 初始化策略
        if not on_init():
            logger.error('策略初始化失败，脚本退出！')
            quote_context.close()
            trade_context.close()
        else:
            get_market_snapshot()                           # 拉去相关数据
            initialization_immobilization_set()             # 初始化列表
            # 设置回调
            quote_context.set_handler(StockQuoteTest())     # 实时报价回调
            quote_context.set_handler(OrderBookClass())     # 摆盘回调
            trade_context.set_handler(OnOrderClass())       # 订单回调STOCK_OWNER
            # 订阅标的合约的 逐笔，K 线和摆盘，以便获取数据
            quote_context.subscribe(code_list=[TRADING_SECURITY, MARKET_SECURITY], subtype_list=[SubType.ORDER_BOOK, SubType.BROKER])
            quote_context.subscribe(code_list=[STOCK_OWNER], subtype_list=[SubType.QUOTE])
            logger.info('订阅成功，开始交易')
            logger.info('************  策略开始运行 ***********')


