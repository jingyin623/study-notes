from fastapi import APIRouter

# 创建一个分路由
shop = APIRouter(prefix='/shop', tags=['购物车功能的接口'])


@shop.post('/cart_all', summary='查询购物车')
def find_cart():
    print('查询购物车')
    return {'msg': '得到购物列表'}


@shop.post('/cart', summary='添加购物车')
def create_cart():
    print('添加购物车')
    return {'msg': '添加购物车'}
