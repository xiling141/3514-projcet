from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import TEXT, VARCHAR

db = SQLAlchemy()

class BioinfoSoftware(db.Model):
    """生物信息学软件模型"""
    __tablename__ = 'bioinfo_software'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(VARCHAR(100), nullable=False, index=True)
    subcategory = db.Column(VARCHAR(100), index=True)
    name = db.Column(VARCHAR(200), nullable=False, index=True)
    features = db.Column(TEXT)
    url = db.Column(VARCHAR(500))
    doi = db.Column(VARCHAR(200))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), 
                          onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'category': self.category,
            'subcategory': self.subcategory,
            'name': self.name,
            'features': self.features,
            'url': self.url,
            'doi': self.doi
        }
    
    def to_tree_format(self):
        """转换为树形结构格式"""
        return {
            'category': self.category,
            'subcategory': self.subcategory or '其他',
            'name': self.name,
            'details': {
                'features': self.features,
                'url': self.url,
                'doi': self.doi
            }
        }# database/import_csv.py
import pandas as pd
from sqlalchemy import create_engine
from config import Config

def import_csv_to_mysql():
    """使用pandas和SQLAlchemy导入CSV到MySQL"""
    config = Config()
    
    try:
        # 1. 读取CSV文件
        print("正在读取CSV文件...")
        df = pd.read_csv(
            config.CSV_FILE_PATH,
            sep=',',  # 如果是制表符分隔
            encoding='GB2312',
            dtype=str
        )
        
        # 2. 重命名列
        column_mapping = {
            '大类': 'category',
            '子类': 'subcategory',
            '软件/数据库名称': 'name',
            '功能特点': 'features',
            '链接': 'url',
            '论文DOI': 'doi'
        }
        df = df.rename(columns=column_mapping)
        
        # 3. 处理空值
        df = df.replace({pd.NA: None, '': None})
        
        # 4. 创建数据库连接引擎
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        
        # 5. 导入数据到MySQL（使用if_exists参数控制）
        print("正在导入数据到MySQL...")
        df.to_sql(
            name='bioinfo_software',
            con=engine,
            if_exists='replace',  # 或 'append' 添加数据
            index=False,
            chunksize=1000,
            method='multi'  # 批量插入
        )
        
        print(f"✅ 成功导入 {len(df)} 条记录")
        
        # 6. 验证数据
        with engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM bioinfo_software")
            count = result.scalar()
            print(f"数据库现有记录数: {count}")
            
            # 显示前几行
            result = conn.execute("SELECT * FROM bioinfo_software LIMIT 5")
            for row in result:
                print(row)
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == '__main__':
    import_csv_to_mysql()