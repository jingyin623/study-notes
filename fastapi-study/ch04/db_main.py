from datetime import datetime

from sqlalchemy import create_engine, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# engine = create_engine(r'sqlite:///test.db', echo=True, future=True)

engine = create_engine('mysql+mysqldb://root:123123@localhost/test_db2?charset=utf8', echo=True, future=True, pool_size=10)


# 定义一个模型类的基类

class Base(DeclarativeBase):

    # 所有的模型类，都有的属性和字段映射
    create_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), comment='记录的创建时间')
    update_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(),  onupdate=func.now(), comment='记录的最后一次修改时间')


def get_session():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()  # 每次用完session，会自动关闭


# 把项目中所有的模型类都导入
import ch04.emp_manager.models
import ch05.models