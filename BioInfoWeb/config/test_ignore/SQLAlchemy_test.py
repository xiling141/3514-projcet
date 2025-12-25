# SQLAlchemy 使用 PyMySQL 作为底层驱动
# 连接字符串格式：数据库类型+驱动://用户名:密码@主机:端口/数据库名

# 使用 PyMySQL 作为驱动
DATABASE_URL = "mysql+pymysql://root:tianmao666@localhost:3306/test"

# 使用 mysql-connector-python 作为驱动
# DATABASE_URL = "mysql+mysqlconnector://username:password@localhost:3306/database"

# 使用 PostgreSQL
# DATABASE_URL = "postgresql://username:password@localhost:5432/database"

from sqlalchemy import create_engine, text
engine = create_engine(DATABASE_URL)

# 使用SQL表达式语言
with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES;"))
    for row in result:
        print(row)