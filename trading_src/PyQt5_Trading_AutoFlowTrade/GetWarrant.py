# coding=utf-8
from futu import *
import bisect
import logging

from trading_src.PyQt5_Trading_AutoFlowTrade.GetBrokerId import get_broker
from trading_src.PyQt5_Trading_AutoFlowTrade.my_logger import initLogConf

initLogConf()
logger = logging.getLogger('my_logger')
GOOD_WARRANT_CODE = {}  # 分数记录字典


# 返回目标经纪号所在的价格(交易代码，交易经纪号，买盘数据，买盘数据，最小跳价点，当前价格)
def find_order_price(trading_num, data, bid_frame_table, ask_frame_table, ret):
    bid_price = 0
    if ret == RET_OK:
        pos = 0
        # pos_ask = 0
        for indexs in bid_frame_table.index:
            bid_broker_id = bid_frame_table.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
            bid_broker_pos = bid_frame_table.at[indexs, 'bid_broker_pos']  # 经纪档位
            if bid_broker_id == int(trading_num):
                pos = int(bid_broker_pos)  # 经纪号所在得档位
                break
        # for indexs in ask_frame_table.index:
        #     ask_broker_id = ask_frame_table.at[indexs, 'ask_broker_id']  # 经纪卖盘 ID
        #     ask_broker_pos = ask_frame_table.at[indexs, 'ask_broker_pos']  # 经纪档位
        #     if ask_broker_id == int(trading_num):
        #         pos_ask = ask_broker_pos  # 经纪号所在得档位
        #         break
        if pos > 0:
            try:
                bid_price = data['Bid'][pos - 1][0]
            except Exception as e:
                print(pos)
                print('Bid:错误{}'.format(data['Bid'][pos - 1][0]))
                print(e)
        # 没有找到目标经济号买盘信息
        else:
            bid_price = 0
        return bid_price
    else:
        logger.error('error:{}'.format(bid_frame_table))
        return bid_price


# 真实溢价计算方法(方向, 正股价格, 行权价, 实际价格, 换股比例)
def premium_true(WRT_TYPE, last_price, WRT_STRIKE_PRICE, THEORETICAL_PRICE, WRT_CONVERSION_RATIO):
    # UP方向溢价的计算方法 (实际行权点-当前实际价值)/当前实际价值
    if WRT_TYPE == 'BULL' or WRT_TYPE == 'CALL':
        real_value = THEORETICAL_PRICE * WRT_CONVERSION_RATIO + WRT_STRIKE_PRICE  # 实际行权点(轮价格 + 行权价)
        pre_true = real_value - last_price  # 实际价值点数(实际行权点-当前点位)
    # DOWN方向溢价甲酸方法()
    if WRT_TYPE == 'BEAR' or WRT_TYPE == 'PUT':
        real_value = WRT_STRIKE_PRICE - THEORETICAL_PRICE * WRT_CONVERSION_RATIO  # 实际行权点(行权价 - 轮价格)
        pre_true = last_price - real_value  # 实际价值点数(当前点位-实际行权点)
    return round(pre_true / last_price * 100, 2)


# 得分机制
def screen_out_good(warrant_data_list, last_page, all_count, quote_ctx):
    last_price = 0  # 相关正股价格
    code_list = []  # 记录所有需要订阅代码
    num = 0
    while num <= len(warrant_data_list) - 1:
        if warrant_data_list['status'][num] == 'NORMAL':
            stock = warrant_data_list['stock'][num]  # 增加需要订阅的代码
            code_list.append(stock)
            if len(code_list) >= 15: break  # 最多15个有效涡轮(防止快照太多 请求频繁报错)
        num = num + 1
    if len(code_list) != 0:
        ret_sub = quote_ctx.subscribe(code_list, [SubType.ORDER_BOOK, SubType.BROKER])[0]
        # 先订阅买卖摆盘类型。订阅成功后 OpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
        if ret_sub == RET_OK:  # 订阅成功
            num = 0
            while num <= len(warrant_data_list) - 1:
                stock = warrant_data_list['stock'][num]  # 拿到涡轮相关数据代码
                #   判断数据是否在指定代码内(有效涡轮)
                if stock in code_list:
                    street_rate = warrant_data_list['street_rate'][num]  # 接货量
                    type = warrant_data_list['type'][num]  # 涡轮类型
                    issuer = warrant_data_list['issuer'][num]  # 涡轮发行人
                    strike_price = warrant_data_list['strike_price'][num]  # 行使价
                    conversion_ratio = warrant_data_list['conversion_ratio'][num]  # 换股比例
                    bid_price = 0  # 庄家买入价格()初始值0)

                    # 获取庄家所在的价格
                    ret, data = quote_ctx.get_order_book(stock)  # 获取一次实时摆盘数据
                    if ret == RET_OK:
                        ret, bid_frame_table, ask_frame_table = quote_ctx.get_broker_queue(stock)  # 获取一次经纪队列数据
                        # 找到庄家所在的价格
                        bid_price = find_order_price(get_broker(stock, quote_ctx), data, bid_frame_table,
                                                     ask_frame_table, ret)
                    else:
                        print('error:', data)

                    # 判断一次相关正股的数值
                    if last_price == 0:
                        # 拿到当前正股的价格
                        ret, data = quote_ctx.get_market_snapshot([warrant_data_list['stock_owner'][num]])
                        if ret == RET_OK:
                            last_price = data['last_price'][0]  # 最新价
                        else:
                            print('error:', data)

                    # 真实溢价计算方法(方向, 正股价格, 行权价, 实际价格, 换股比例)
                    premium = premium_true(type, last_price, strike_price, bid_price, conversion_ratio)

                    # 价格分数比重分别为50 30 20
                    price_values = [0.011, 0.020, 0.030, 0.040, 0.050, float('inf')]
                    price_scores = [50, 40, 30, 20, 10]

                    idx = bisect.bisect_right(price_values, bid_price) - 1
                    price_score = price_scores[idx]

                    # 溢价分数
                    premium_scores = {-float('inf'): 30, -0.25: 25, -0.20: 20, -0.15: 15, 0: 10}
                    premium_score = premium_scores[max(filter(lambda x: x <= premium, premium_scores))]

                    # 接货量分数
                    street_dict = {20: 20, 10: 15, float('-inf'): 10}
                    street_rate_score = street_dict[max(filter(lambda x: x <= street_rate, street_dict))]

                    score = int(street_rate_score + premium_score + price_score)
                    # 增加同分数的代码
                    if score in GOOD_WARRANT_CODE:
                        GOOD_WARRANT_CODE[score].append('{} {:4} {:>6} {:>3} {:2}'
                                                        .format(stock, bid_price, round(premium, 2), int(street_rate),
                                                                issuer))
                    # 没有相关分数 处理
                    else:
                        GOOD_WARRANT_CODE[score] = ['{} {:4} {:>6} {:>3} {:2}'
                                                        .format(stock, bid_price, round(premium, 2), int(street_rate),
                                                                issuer)]
                num = num + 1
        else:
            print('subscription failed')


# 查询所有符合条件的涡轮(并打分)
def get_warrant(code, cur_price_max, street_min, premium_max, issuer_list):
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    logger.debug('查询条件:正股代码{} |价格上限{} |街货下限{} |溢价上线{}|做市商{}'
                 .format(code, cur_price_max, street_min, premium_max, issuer_list))
    num_type_list = ['BULL', 'BEAR']
    for i in num_type_list:
        req = WarrantRequest()
        req.num = 50
        req.sort_field = SortField.RECOVERY_PRICE  # 排序字段 回收价
        req.ascend = False if i == 'BULL' else req.ascend  # 降序方向
        req.type_list = [WrtType.BULL] if i == 'BULL'else req.type_list   # 涡轮类型
        req.ascend = True if i == 'BEAR' else req.ascend  # 升序方向
        req.type_list = [WrtType.BEAR] if i == 'BEAR' else req.type_list  # 涡轮类型
        req.issuer_list = issuer_list  # 发行人过滤列表
        req.status = WarrantStatus.NORMAL  # 涡轮状态
        req.cur_price_min = float(0.010)  # 最新价的过滤下限
        req.cur_price_max = float(cur_price_max)  # 最新价的过滤上限
        req.street_min = float(street_min)  # 街货占比的过滤下限
        req.conversion_max = 10000  # 换股比率的过滤上限
        req.premium_max = float(premium_max)  # 溢价的过滤上限
        ret, ls = quote_ctx.get_warrant('HK.' + code, req)  # 获取正股的符合条件的所有涡轮数据
        if ret == RET_OK:  # 先判断接口返回是否正常，再取数据
            warrant_data_list, last_page, all_count = ls
            # 是否有相关信息
            if all_count != 0:
                screen_out_good(warrant_data_list, last_page, all_count, quote_ctx)  # 给所有涡轮打分,并记录
        else:
            logger.error('error: ', ls)
    keys_iter = sorted(GOOD_WARRANT_CODE.keys(), reverse=True)  # 获取字典中所有键，返回的是可迭代对象(并按降序排序)
    end_num = min(len(keys_iter), 3)  # 取2个数中最小数。
    good_value = []
    num = 0
    while num < end_num:
        # 使用列表推导式去掉需要存入数据每个字符串中的"HK."
        good_value.append(str(keys_iter[num]))
        good_value = good_value + [x.replace("HK.", "") for x in GOOD_WARRANT_CODE[keys_iter[num]]]  # 去掉所有数据的HK.
        num = num + 1
    GOOD_WARRANT_CODE.clear()  # 清理数据,以免数据混乱
    quote_ctx.close()
    return good_value
