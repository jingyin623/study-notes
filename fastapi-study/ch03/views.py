from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, field_validator
from datetime import date


ch3 = APIRouter(prefix='/ch3', tags=['请求体传参'])


class Address(BaseModel):
    """详细地址"""

    province: str
    city: str
    county: str


class Emp(BaseModel):
    """
    员工请求参数的模型类
    """
    name: str = Field(description='员工的名字')
    age: int = Field(description='员工的年龄', ge=18, lt=60)
    birth: date= Field(description='员工的出生日期', default=None)
    addr: Address = Field(default=None, description='员工的详细地址')

    @field_validator('name')  # 自定义一个复杂校验器，针对哪个字段做校验
    def validate_name(cls, value):
        """
        复杂的校验
        :param value:
        :return:
        """
        import re
        result = re.match(r'^[a-z_]\w{5, 16}$', value)
        assert not result is None
        return value

@ch3.post('/emp', summary='添加员工')
def create_emp(emp: Emp):
    print(emp)
    return emp


"""
请求体传参：json数据
{
"name": value,
"age": value
}
"""


@ch3.post('/test', summary='测试添加员工')
def test(name: str = Body(default=None, description='测试的姓名'),
         age: int = Body(default=18, description='测试的年龄')):
    print(name, age)
    return {'msg': "Ok"}