from enum import Enum

from fastapi import APIRouter, Path

ch1 = APIRouter(prefix='/ch1', tags=['路由传参'])


@ch1.get('/emp', summary='查询所有员工')
def find_all_emp():
    print('查询所有员工')
    return {'msg': 'ok'}


@ch1.get('/emp/{emp_id}', summary='查询单个员工')
def find_emp(emp_id: int):
    print(f'传入参数为:{emp_id}')
    return {'msg': 'ok'}


@ch1.delete('/emp/{emp_id}', summary='删除单个员工')
def delete_emp(emp_id: int):
    print(f'传入参数为:{emp_id}')
    print('删除单个员工')
    return {'msg': 'ok'}


class EmpName(Enum):
    zs = '张三'
    ls = '李四'
    ww = '王五'


# 修改的视图函数 : 预设值传参
@ch1.put('/emp/{emp_name}', summary='修改单个员工', description='修改某个员工')
def update_emp(emp_name: EmpName = Path(description='参数表示员工名字，只能是：张三，李四，王五其中之一。')):
    print(f'传入参数为:{emp_name.name}')
    print(f'传入参数为:{emp_name.value}')
    print('修改单个员工')
    return {'msg': 'ok'}
