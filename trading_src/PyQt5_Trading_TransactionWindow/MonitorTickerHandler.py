"""
监测 庄家 上下扫单

.. code:: python
    根据每笔成交
        相反方向 且 （当前价格-前价格）/ 前价格 >= 相关条件 且 成交额大于相关条件
    提示并展示相关代码
"""
# import pandas as pd  # 将pandas作为第三方库导入，我们一般为pandas取一个别名叫做pd
import winsound
from colorama import init
init(autoreset=True)

from futu import *


############################ 全局变量设置 ############################
FUTUOPEND_ADDRESS = '127.0.0.1'  # FutuOpenD 监听地址
FUTUOPEND_PORT = 11111  # FutuOpenD 监听端口
IMMOBILIZATION_DICT = {}  # 全局字典
IMMOBILIZATION_K_DICT = {}  # 全局K线字典
RECORD_SET = set()        # 记录集合
IMMOBILIZATION_LIST = []  # 订阅合约列表
PREFIX = 'HK.'  # 数字前缀前缀
TRADING_MARKET = TrdMarket.HK  # 交易市场权限，用于筛选对应交易市场权限的账户
TRADING_ENVIRONMENT = TrdEnv.SIMULATE  # 交易环境：真实 / 模拟

MARKET_SECURITY = 'C:/Users/MR.jiang/Desktop/12.csv'  # 监测列表文件地址
DEFAULTAMPLITUDE = 5  # 预设振幅
DEFAULTTURNOVER = 25000  # 预设成交额
DEFAULTMULTIPLE = 30  # 预设倍数
LIFECYCLE = 10  # 生命周期
SUMTURNOVER = 3  # 同向成交量倍数


# DEFAULTAMPLITUDE = int(input('预设振幅:'))  # 预设振幅
# DEFAULTTURNOVER = int(input('预设成交额:'))  # 预设成交额
# DEFAULTMULTIPLE = int(input('预设倍数:'))  # 预设倍数
# LIFECYCLE = int(input('生命周期:'))  # 生命周期
# SUMTURNOVER = int(input('同向成交量倍数:'))  # 同向成交量倍数
# MARKET_SECURITY = input('文件地址格式(C:/Users/MR.jiang/Desktop/12.csv): ')  # 监测列表文件地址


quote_context = OpenQuoteContext(host=FUTUOPEND_ADDRESS, port=FUTUOPEND_PORT)  # 行情对象


# 每次产生数据变化运行一次，返回买卖信号可将策略的主要逻辑写在此处
def on_bar_open_T(data):
    # 提取每一行数据
    for indexs in data.index:
        ticker_type = data.at[indexs, 'type']  # 成交类型
        # 过滤DX*三种订单单
        if ticker_type != 'INTER_NONE_AUTOMATCH' and ticker_type != 'ODD_LOT' and ticker_type != 'OVERSEAS':
            code = data.at[indexs, 'code']                              # 相关代码
            price = data.at[indexs, 'price']                            # 成交价格
            ticker_direction = data.at[indexs, 'ticker_direction']      # 成交方向
            turnover = data.at[indexs, 'turnover']                      # 成交金额
            # 全局集合中相关代码没有数据 加载一次数据
            if IMMOBILIZATION_DICT[code][0] == 0:
                IMMOBILIZATION_DICT[code] = [price, ticker_direction, 0, turnover, turnover]   # 价格，方向，生命周期, 单笔成交额, 同方向成交额
            # 全局集合中相关代码有数据
            else:
                # 符合条件预设条件 (方向相反，且振幅大于预设，且成交额大于预设，且1分钟K 成交量大于预设,同向成交额大于预设)
                amplitude = round(((abs(price - IMMOBILIZATION_DICT[code][0]) / IMMOBILIZATION_DICT[code][0]) * 1000), 2)
                if IMMOBILIZATION_DICT[code][1] != ticker_direction \
                        and amplitude >= DEFAULTAMPLITUDE \
                        and IMMOBILIZATION_DICT[code][3] >= DEFAULTTURNOVER \
                        and IMMOBILIZATION_K_DICT[code] >= DEFAULTTURNOVER * DEFAULTMULTIPLE \
                        and IMMOBILIZATION_DICT[code][4] >= DEFAULTTURNOVER * SUMTURNOVER:
                    # 判断生命周期是否小于0 第一次提醒
                    if IMMOBILIZATION_DICT[code][2] <= 0:
                        # 修改全局集合数据，并赋予生命周期
                        IMMOBILIZATION_DICT[code][0] = price
                        IMMOBILIZATION_DICT[code][1] = ticker_direction
                        IMMOBILIZATION_DICT[code][2] = LIFECYCLE
                        IMMOBILIZATION_DICT[code][3] = turnover

                        RECORD_SET.add(code)
                        winsound.Beep(500, 500)
                        print("增加的代码:\033[1;30;41m" + code + "\033[0m")
                        print(RECORD_SET)
                    # 生命周期大于零，已经提醒过，生命周期减一
                    else:
                        # 全局集合中相关代码有数据，更新相关数据 并生命周期减一,不用提醒
                        IMMOBILIZATION_DICT[code][0] = price
                        IMMOBILIZATION_DICT[code][1] = ticker_direction
                        IMMOBILIZATION_DICT[code][2] = IMMOBILIZATION_DICT[code][2] - 1  # 价格，方向，生命周期, 成交额
                        IMMOBILIZATION_DICT[code][3] = turnover

                        print(RECORD_SET)
                # 不符符合条件预设条件 (方向相反，且振幅大于预设，且成交额大于预设)
                else:
                    # 全局集合中相关代码有数据，更新相关数据 并生命周期减一，不用提醒
                    IMMOBILIZATION_DICT[code][0] = price
                    IMMOBILIZATION_DICT[code][1] = ticker_direction
                    IMMOBILIZATION_DICT[code][2] = IMMOBILIZATION_DICT[code][2] - 1
                    IMMOBILIZATION_DICT[code][3] = turnover

                    # 判断生命周期是否小于0 删除记录代码
                    if IMMOBILIZATION_DICT[code][2] <= 0:
                        RECORD_SET.discard(code)
                # 方向相同 累加
                if ticker_direction == IMMOBILIZATION_DICT[code][1]:    # 相同方向
                    IMMOBILIZATION_DICT[code][4] = IMMOBILIZATION_DICT[code][4] + turnover
                # 反方向  重置
                else:
                    IMMOBILIZATION_DICT[code][4] = turnover


# 每次产生数据变化运行一次，返回买卖信号可将策略的主要逻辑写在此处
def on_bar_open_K(data):
    # 提取每一行数据
    for indexs in data.index:
        code = data.at[indexs, 'code']                              # 相关代码
        turnover = data.at[indexs, 'turnover']                      # 成交金额
        IMMOBILIZATION_K_DICT[code] = turnover                      # 全局K线字典 修改成交额


################################ 框架实现部分，可忽略不看 ###############################
class TickerTest(TickerHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(TickerTest, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("TickerTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open_T(data)
        return RET_OK, data


class CurKlineTest(CurKlineHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(CurKlineTest, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("TickerTest: error, msg: %s" % data)
            return RET_ERROR, data
        on_bar_open_K(data)
        return RET_OK, data

    # 关闭当条连接
def quote_context_close():
    quote_context.close()


def quote_context_stop():
    quote_context.stop()


    # 入口函数
def submit_run(market_security, defaultamplitude, defaultturnover, defaultmultiple, lifecycle, sumturnover):
    global MARKET_SECURITY # 监测列表文件地址
    global DEFAULTAMPLITUDE  # 预设振幅
    global DEFAULTTURNOVER  # 预设成交额
    global DEFAULTMULTIPLE  # 预设倍数
    global LIFECYCLE # 生命周期
    global SUMTURNOVER # 同向成交量倍数

    MARKET_SECURITY = market_security  # 监测列表文件地址
    DEFAULTAMPLITUDE = int(defaultamplitude)  # 预设振幅
    DEFAULTTURNOVER = int(defaultturnover)  # 预设成交额
    DEFAULTMULTIPLE = int(defaultmultiple)  # 预设倍数
    LIFECYCLE = int(lifecycle)  # 生命周期
    SUMTURNOVER = int(sumturnover)  # 同向成交量倍数

    # =====导入数据
    df = pd.read_csv(
        # 该参数为数据在电脑中的路径，可以不填写
        filepath_or_buffer=MARKET_SECURITY,
        # 该参数代表数据的分隔符，csv文件默认是逗号。其他常见的是'\t'
        sep=',',
        # 该参数代表跳过数据文件的的第1行不读入
        # skiprows=1,
        # 当某行数据有问题时，报错。设定为False时即不报错，直接跳过该行。当数据比较脏乱的时候用这个。
        error_bad_lines=False,
        # 将数据中的null识别为空值
        na_values='NULL',
        # 更多其他参数，请直接搜索"pandas read_csv"，要去逐个查看一下。比较重要的，header等
        # =====输出
        # print df
        # df.to_csv('output.csv', encoding='gbk', index=False)
    )
    for CODE in df['code']:
        code = PREFIX + str(CODE).zfill(5)  # 添加前缀且 自动补零
        IMMOBILIZATION_DICT[code] = [0]     # 初始化全局集合
        IMMOBILIZATION_K_DICT[code] = 0     # 初始化全局K线集合
        IMMOBILIZATION_LIST.append(code)    # 初始合约列表
    # 设置回调
    quote_context.set_handler(TickerTest())  # 设置实时逐笔推送回调
    quote_context.set_handler(CurKlineTest())  # 设置k线推送推送回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=IMMOBILIZATION_LIST, subtype_list=[SubType.TICKER, SubType.K_1M])
    quote_context.start()


# 主函数
if __name__ == '__main__':

    # =====导入数据
    df = pd.read_csv(
        # 该参数为数据在电脑中的路径，可以不填写
        filepath_or_buffer=MARKET_SECURITY,
        # 该参数代表数据的分隔符，csv文件默认是逗号。其他常见的是'\t'
        sep=',',
        # 该参数代表跳过数据文件的的第1行不读入
        # skiprows=1,
        # 当某行数据有问题时，报错。设定为False时即不报错，直接跳过该行。当数据比较脏乱的时候用这个。
        error_bad_lines=False,
        # 将数据中的null识别为空值
        na_values='NULL',
        # 更多其他参数，请直接搜索"pandas read_csv"，要去逐个查看一下。比较重要的，header等
        # =====输出
        # print df
        # df.to_csv('output.csv', encoding='gbk', index=False)
    )
    for CODE in df['code']:
        code = PREFIX + str(CODE).zfill(5)  # 添加前缀且 自动补零
        IMMOBILIZATION_DICT[code] = [0]     # 初始化全局集合
        IMMOBILIZATION_K_DICT[code] = 0     # 初始化全局K线集合
        IMMOBILIZATION_LIST.append(code)    # 初始合约列表
    # 设置回调
    quote_context.set_handler(TickerTest())  # 设置实时逐笔推送回调
    quote_context.set_handler(CurKlineTest())  # 设置k线推送推送回调
    # 订阅标的合约的 摆盘，以便获取数据
    quote_context.subscribe(code_list=IMMOBILIZATION_LIST, subtype_list=[SubType.TICKER, SubType.K_1M])

