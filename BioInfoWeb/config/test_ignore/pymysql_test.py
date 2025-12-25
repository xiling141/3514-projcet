import pymysql

# 连接数据库
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='tianmao666',
    database='test',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor  # 返回字典格式
)

# 执行查询
with connection.cursor() as cursor:
    sql = "SHOW TABLES;"
    cursor.execute(sql)
    result = cursor.fetchall()
    print(result)

connection.close()