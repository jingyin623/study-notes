from enum import Enum

from fastapi import APIRouter, Path
from fastapi import Query
from typing import List

ch2 = APIRouter(prefix='/ch2', tags=['rul传参'])

@ch2.get('/emp', summary='搜索员工')
def find_all_emp(emp_id: int = Query(default=None, description='员工ID'),
                 name: str = Query(default=None, description='员工名字')):
    print(emp_id)
    print(name)
    return {'msg': 'ok'}


@ch2.delete('/emp', summary='批量删除员工', description='只要传入多个员工ID，把这些员工全部删除')
def delete_emp(emp_ids: List[int] = Query(default=[], description='多个参数员工ID')):
    print(emp_ids)
    return {'msg': 'ok'}


# # 字符串长度的校验
# @ch2.post('/emp', summary='添加员工', description='需要员工的名字')
# def delete_emp(name: str = Query(description='要添加的员工名字', max_length=15, min_length=6)):
#     print(name)
#     return {'msg': 'ok'}

# 正则表达式的校验
"""
1.用户名只能包含数字 字母 下划线
2.不能以数字开头
3.⻓度在 6 到 16 位范围内
"""


@ch2.post('/emp', summary='添加员工', description='需要员工的名字')
def delete_emp(name: str = Query(description='要添加的员工名字', pattern=r'^[a-zA-Z_]\w{5,15}$'),
               age: int = Query(description='要添加的员工年龄', ge=18, lt=60)):
    print(name)
    print(age)
    return {'msg': 'ok'}