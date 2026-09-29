#coding=utf-8
from futu import RET_OK, OrderType, ModifyOrderOp, TrdEnv

from futuniuniu_autotrading.PyQt5_Demo_Trading import AutoTrade


# 计算最小下单数量
def small_calculate_quantity(code):
    price_quantity = 0
    # 使用最小交易量
    ret, data = AutoTrade.quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        AutoTrade.logger.error('获取快照失败：', data)
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity


# 判断购买力是否足够
def is_valid_quantity(code, quantity, price):
    ret, data = AutoTrade.trade_context.acctradinginfo_query(order_type=OrderType.NORMAL, code=code, price=price,
                                                   trd_env=AutoTrade.TRADING_ENVIRONMENT)
    if ret != RET_OK:
        AutoTrade.logger.error('获取最大可买可卖失败：', data)
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
    open_quantity = order_size
    # 判断购买力是否足够
    if is_valid_quantity(code, open_quantity, price):
        # 下单
        ret, data = AutoTrade.trade_context.place_order(price=price, qty=open_quantity, code=code, trd_side=trd_side,
                                              order_type=OrderType.NORMAL, trd_env=AutoTrade.TRADING_ENVIRONMENT,
                                              remark='moving_average_strategy')
        if ret != RET_OK:
            AutoTrade.logger.error('开仓失败：', data)
        order_id = data['order_id'][0]   # 成功后返回订单的ID
        return order_id
    else:
        AutoTrade.logger.error('下单数量超出最大可买数量。')


# 开仓函数(交易代码，价格，仓位(手)，买卖方向(0买1卖))
def up_open_position(trading_security, bid_share_price, order_size, buy_or_sell):
    #   更改订单状态为已下单 ，订单无回调(不为'-1')
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = 0
    order_id = open_position(trading_security, bid_share_price, order_size, buy_or_sell)
    #   更改订单状态为已下单 ，订单无回调
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = order_id
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][4] = buy_or_sell


#  改单
def modify_position(code, order_id, price, order_size):
    # 计算下单量
    open_quantity = order_size
    #  改单
    ret, data = AutoTrade.trade_context.modify_order(modify_order_op=ModifyOrderOp.NORMAL, order_id=order_id, price=price,
                                           qty=open_quantity, trd_env=AutoTrade.TRADING_ENVIRONMENT)
    if ret == RET_OK:
        pass
    else:
        AutoTrade.logger.error('modify_order error: ', data)

#  改单(交易代码，当前价格，目标价格，订单ID，仓位，买卖方向)
def up_modify_position(trading_security, bid_share_price, target_bid_share_price, order_id, order_size, buy_or_sell):
    #   更改订单状态为已下单 ，订单无回调
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = 0
    AutoTrade.IMMOBILIZATION_SET[target_bid_share_price][3] = 0
    modify_position(trading_security, order_id,
                    target_bid_share_price, order_size)
    #   更改目标价位的订单状态
    AutoTrade.IMMOBILIZATION_SET[target_bid_share_price][3] = order_id
    AutoTrade.IMMOBILIZATION_SET[target_bid_share_price][4] = buy_or_sell
    #   更改当前价格改为无订单状态
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = '-1'
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][4] = '-1'


#  撤单
def cancel_position(order_id):
    #  撤单
    ret, data = AutoTrade.trade_context.modify_order(modify_order_op=ModifyOrderOp.CANCEL, order_id=order_id, price=0,
                                           qty=0, trd_env=AutoTrade.TRADING_ENVIRONMENT)
    if ret == RET_OK:
        pass
    else:
        AutoTrade.logger.error('modify_order error: ' + data)


#  撤单(当前价格， 订单ID)
def up_cancel_position(bid_share_price, order_id):
    #   更改订单状态为已下单 ，订单无回调
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = 0
    cancel_position(order_id)
    #   当前价格改为无订单状态
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][3] = '-1'
    AutoTrade.IMMOBILIZATION_SET[bid_share_price][4] = '-1'
    # 判断订单是否已经成交过
    if AutoTrade.CAN_SELL_QTY[1].get(order_id) != None:
        # 撤单订单是已成交订单，删除成交订单
        del AutoTrade.CAN_SELL_QTY[1][order_id]


# 解锁交易
def unlock_trade():
    if AutoTrade.TRADING_ENVIRONMENT == TrdEnv.REAL:
        ret, data = AutoTrade.trade_context.unlock_trade(AutoTrade.TRADING_PWD)
        if ret != RET_OK:
            AutoTrade.logger.error('解锁交易失败：', data)
            return False
        AutoTrade.logger.info('解锁交易成功！')
    return True
