#coding=utf-8
from futu import *
import json
import logging
from trading_src.PyQt5_Trading_MonitorTickerHandler.my_logger import initLogConf
initLogConf()
logger = logging.getLogger('my_logger')


# 文件的操作
def rend_and_write(write=None):
    filename = 'broker.json'
    content = {}    # 返回的数据
    # 用户有输入数据(数据写入列表)
    if write is not None:
        with open(filename, 'w') as f:
            content_str = json.dumps(write)
            f.write(content_str)
            logger.debug('写入broker.json数据：{}'.format(write))
    else:
        try:
            # 尝试读取文件
            with open(filename, 'r') as f:
                content_str = f.read()
                content = json.loads(content_str)   # 读取文件,json方式读取,content为dict
                logger.debug('读取broker.json文件：{}'.format(content))
        except FileNotFoundError:
            # 如果文件不存在，则创建文件并写入内容
            with open(filename, 'w') as f:
                content_str = json.dumps(content)
                f.write(content_str)
                logger.debug('目录没有找到broker.json文件,broker.json,并写入: {}'.format(content))
    return content

#  查询出涡轮庄家的经纪号(涡轮经纪队列数据, 涡轮发行商)
def get_broker_1(data, wrt_issuer_code):
    content = rend_and_write()    # 读出文件数据
    # print(content.keys())
    # 如果相关的发行上在文件字典中
    if wrt_issuer_code in content.keys():
        broker_id = content[wrt_issuer_code]    # 拿到发行商的经纪列表
        # 拿到经纪文件中的每个经纪号ID去跟目前数据中的所有经纪号ID 对比
        for num in broker_id:
            for indexs in data.index:
                bid_broker_id = data.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
                # bid_broker_pos = data.at[indexs, 'bid_broker_pos']  # 经纪档位
                if bid_broker_id == int(num):   # 文件经纪号与拉去ID相匹配
                    return_id = bid_broker_id   # 设置返回的经纪ID
                    # pos = bid_broker_pos  # 经纪号所在得档位
                    # bid_price = data['Bid'][pos - 1][0]
                    return return_id
    return '0'  # 没有找到匹配的都返回0,0

# 判断输入的经纪号是否在经纪队列中
def get_broker_2(data, user_broker):
    isbroker = False
    for indexs in data.index:
        bid_broker_id = data.at[indexs, 'bid_broker_id']  # 经纪买盘 ID
        if bid_broker_id == int(user_broker):  # 文件经纪号与拉去ID相匹配
            isbroker = True
            return isbroker
    return isbroker

# 得到发行人代码
def get_wrt_issuer_code(quote_ctx, code):
    ret, data = quote_ctx.get_market_snapshot([code])
    wrt_issuer_code = 0
    if ret == RET_OK:
         wrt_issuer_code = data['wrt_issuer_code'][0]
    else:
        logger.error('error:', data)
    return wrt_issuer_code

def get_broker(code):
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    broker_id = '0'      # 经纪ID
    wrt_issuer_code = get_wrt_issuer_code(quote_ctx, code)  # 得到发行人代码

    ret_sub, err_message = quote_ctx.subscribe([code], [SubType.BROKER], subscribe_push=False)
    # 先订阅经纪队列类型。订阅成功后 FutuOpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        ret, bid_frame_table, ask_frame_table = quote_ctx.get_broker_queue(code)  # 获取一次经纪队列数据
        if ret == RET_OK:
            broker_id = get_broker_1(bid_frame_table, wrt_issuer_code)  # 查询处涡轮庄家的经纪号
        else:
            logger.error('error:', bid_frame_table)
    else:
        logger.error('subscription failed')
    quote_ctx.close()  # 关闭当条连接，FutuOpenD 会在1分钟后自动取消相应股票相应类型的订阅
    return broker_id

# 输入经纪号
def set_broker(code, user_broker):
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    content = rend_and_write()    # 读出文件数据
    wrt_issuer_code = get_wrt_issuer_code(quote_ctx, code)  # 得到发行人代码
    isbroker = False

    ret_sub, err_message = quote_ctx.subscribe([code], [SubType.BROKER], subscribe_push=False)
    # 先订阅经纪队列类型。订阅成功后 FutuOpenD 将持续收到服务器的推送，False 代表暂时不需要推送给脚本
    if ret_sub == RET_OK:  # 订阅成功
        ret, bid_frame_table, ask_frame_table = quote_ctx.get_broker_queue(code)  # 获取一次经纪队列数据
        if ret == RET_OK:
            isbroker = get_broker_2(bid_frame_table, user_broker)  # 查询处涡轮庄家的经纪号
        else:
            logger.error('error:', bid_frame_table)
    else:
        logger.error('subscription failed')

    # 文件中没有发行人代码
    if wrt_issuer_code not in content:
        # 判断用户输入的经纪号是否正确(对比数据)(在数据中)
        if isbroker is True:
            content[wrt_issuer_code] = [user_broker]    #   更新文件数据
            rend_and_write(write=content)#   保存数据文件
    # 文件中有发行人
    else:
        # 发行人列表中没有用户输入的经纪号
        if user_broker not in content[wrt_issuer_code]:
            # 判断用户输入的经纪号是否正确(对比数据)(在数据中)
            if isbroker is True:
                content[wrt_issuer_code].append(user_broker)
                rend_and_write(write=content)  # 保存数据文件
    quote_ctx.close()  # 关闭当条连接，FutuOpenD 会在1分钟后自动取消相应股票相应类型的订阅
