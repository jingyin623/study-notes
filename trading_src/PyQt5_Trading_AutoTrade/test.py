from futu import *
trd_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)
ret, data = trd_ctx.position_list_query()
if ret == RET_OK:
    print(data)
    if data.shape[0] > 0:  # 如果持仓列表不为空
        print(data['stock_name'][0])  # 获取持仓第一个股票名称
        print(data['stock_name'].values.tolist())  # 转为 list
else:
    print('position_list_query error: ', data)
trd_ctx.close()  # 关闭当条连接