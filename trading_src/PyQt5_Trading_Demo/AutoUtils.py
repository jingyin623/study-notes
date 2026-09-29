# 返回目标经纪号所在的价格(交易代码，交易经纪号，买盘数据，买盘数据，最小跳价点，当前价格)
def find_order_price(push_code, trading_num, bid, quote_context, RET_OK,logger):
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
def small_calculate_quantity(code, quote_context, RET_OK, logger):
    price_quantity = 0
    # 使用最小交易量
    ret, data = quote_context.get_market_snapshot([code])
    if ret != RET_OK:
        logger.error('获取快照失败：', data)
        return price_quantity
    price_quantity = data['lot_size'][0]
    return price_quantity

# 判断购买力是否足够
def is_valid_quantity(code, quantity, price, trade_context, OrderType, TRADING_ENVIRONMENT, RET_OK, logger):
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
def open_position(code, price, order_size, trd_side, trade_context,OrderType,TRADING_ENVIRONMENT, RET_OK,logger):
    # 计算下单量
    open_quantity = order_size
    # 判断购买力是否足够
    if is_valid_quantity(code, open_quantity, price, trade_context, OrderType, TRADING_ENVIRONMENT, RET_OK, logger):
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