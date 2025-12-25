import os
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote
from sqlalchemy.engine import URL

# 加载环境变量
load_dotenv()

class Config:
    # 基础配置
    BASE_DIR = Path(__file__).resolve().parent.parent
    CSV_FILE_PATH = BASE_DIR / 'data' / 'biotool.csv'
    
    # 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'bioinfo_software')
    MYSQL_CHARSET = 'utf8mb4'
    
    # SQLAlchemy配置
    connection_url = URL.create(
    drivername="mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD, 
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DATABASE,
    query={"charset": MYSQL_CHARSET}
    )

    SQLALCHEMY_DATABASE_URI = str(connection_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }