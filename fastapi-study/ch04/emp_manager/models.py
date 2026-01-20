import enum
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DECIMAL, Boolean, func, insert, select, text, update, delete, and_, or_, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, relationship
from ch04.db_main import Base, engine


class SexValue(enum.Enum):
    """通过枚举，可以给一些属性（字段）设置预设值"""
    MALE = '男'
    FEMALE = '女'


class Employee(Base):
    """员工的模型类"""

    __tablename__ = 't_emp'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40), name='emp_name', unique=True, nullable=False)

    # DECIMAL 其中10代表总位数，2代表小数点后的位数
    sal: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True, comment='员工的基本工资')
    bonus: Mapped[int] = mapped_column(default=0, comment='员工的津贴和奖金')
    is_leave: Mapped[bool] = mapped_column(Boolean, default=False,
                                           comment='员工是否离职，True代表已经离职，False代表在职')

    gender: Mapped[SexValue]
    entry_date: Mapped[date] = mapped_column(insert_default=func.now(), nullable=False, comment='入职时间')

    # 和部门表关联的外键
    dept_id: Mapped[Optional[int]] = mapped_column(ForeignKey('t_dept.id'), nullable=True)
    # 定义一个关联属性： 该员工所属的部门
    dept: Mapped[Optional['Dept']] = relationship(back_populates='emp_list', cascade='save-update')

    # 定义一个和身份证关联的属性：idc
    idc: Mapped[Optional['IdCard']] = relationship(back_populates='emp')

    # 需要在Employee模型类中增加一个__str__函数
    def __str__(self):
        return f'{self.name}, {self.gender.value}, {self.sal}, {self.entry_date}, {self.bonus}'

# if __name__ == '__main__':
#     # 创建表
#     Base.metadata.create_all(engine)

if __name__ == '__main__':
    with sessionmaker(engine).begin() as session:
        # 新增数据（一）
        # emp1 = Employee(name='zs', sal=2000, bonus=300, gender=SexValue.MALE, entry_date=date(2019, 10, 23))
        # emp2 = Employee(name='ls', sal=3000, bonus=400, gender=SexValue.MALE, entry_date=date(2018, 8, 23))
        # emp3 = Employee(name='wangwu', sal=1000, bonus=800, gender=SexValue.FEMALE, entry_date=date(2018, 8, 23))
        # # session.add(emp1)
        # # session.add(emp2)
        # session.add_all([emp2, emp3])

        # 新增数据（二）： 类SQL的方式
        # insert_stmt = insert(Employee).values(name='孙六', sal=3500)
        # session.execute(insert_stmt)


        # get返回一条数据
        # emp = session.get(Employee, 3)
        # print(emp)

        #  返回所有的数据 , scalars返回的是模型对象
        # stmt = select(Employee)
        # list_emp = session.scalars(stmt).all()
        # for emp in list_emp:
        #     print(type(emp))
        #     print(emp)

        # 返回指定字段的数据 ， execute返回是row对象, row对象相当于是一个字典，key就是属性名字,value就是对应字段的值
        # stmt = select(Employee.name, Employee.sal, Employee.gender)
        # result = session.execute(stmt).all()
        # for obj in result:
        #     print(type(obj))
        #     print(obj.sal, obj.name, obj.gender.value)

        # 采用原生SQL来查询
        # 返回指定字段的数据 ， execute返回是row对象, row对象相当于是一个字典，key就是字段名字,value就是对应字段的值
        # sql = text('select id, emp_name, sal, gender from t_emp')
        # result = session.execute(sql).all()
        # for obj in result:
        #     print(type(obj))
        #     print(obj.id, obj.emp_name, obj.sal, obj.gender)



        # 采用原生SQL来查询
        # 返回指定字段的数据 ， execute返回是row对象, row对象相当于是一个字典，key就是字段名字,value就是对应字段的值
        # sql = text('select id, emp_name, sal, gender from t_emp')
        # orm_sql = sql.columns(Employee.id, Employee.name, Employee.sal, Employee.gender)
        # stmt = select(Employee).from_statement(orm_sql)
        # result = session.execute(stmt).scalars()
        # for obj in result:
        #     print(type(obj))
        #     print(obj)


        # 修改：第一种
        # emp = session.get(Employee, 4)
        # emp.name = '王五'

        # 修改： 第二种
        # stmt = update(Employee).where(Employee.id == 1).values(name='张三', sal=2500)
        # session.execute(stmt)

        # 批量修改
        # session.execute(update(Employee), [
        #     {'id': 1, 'bonus': 600},
        #     {'id': 3, 'bonus': 600}
        # ])


        # 删除：第一种
        # emp = session.get(Employee, 6)
        # session.delete(emp)

        # 删除： 第二种
        # stmt = delete(Employee).where(Employee.id == 6)  # delete from t_emp where id=6
        # session.execute(stmt)


        # 过滤条件
        # 1
        # stmt = select(Employee).where(Employee.name == '张三')
        # stmt = select(Employee).where(Employee.name.is_(None))  #  判断某个字段是否为空

        # 2
        # stmt = select(Employee).where(Employee.name != '张三')
        # stmt = select(Employee).where(Employee.name.isnot(None))

        # 3
        stmt = select(Employee).where(Employee.name.like('%三%'))

        # 4
        stmt = select(Employee).where(Employee.id.in_([1, 5]))
        # 5
        # stmt = select(Employee).where(Employee.name.like('%四%'), Employee.sal >= 3000)
        stmt = select(Employee).where(and_(Employee.name.like('%四%'), Employee.sal >= 3000))

        #6
        stmt = select(Employee).where(or_(Employee.name.like('%四%'), Employee.sal >= 3000))
        result = session.execute(stmt).scalars()

        for o in result:
            print(o)

        # 7 聚合函数
        stmt = select(func.avg(Employee.sal))
        stmt = select(func.count(Employee.id))
        result = session.execute(stmt).first()
        print(result)

        # 8 分页
        result = session.execute(select(Employee).offset(2).limit(3)).scalars()

        # 9 排序
        result = session.execute(select(Employee).order_by(Employee.sal).offset(0).limit(3)).scalars()
        result = session.execute(select(Employee).order_by(Employee.sal.desc()).offset(0).limit(3)).scalars()

        # 10 分组查询
        # 查询每一种性别有多少个员工
        stmt = select(Employee.gender, func.count(Employee.id)).group_by(Employee.gender)
        result = session.execute(stmt).all()
        for o in result:
            print(type(o))
            print(o.gender.value, o.count)