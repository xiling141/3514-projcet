import pymysql
import pandas as pd
from config import Config

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            if not self.connection or not self.connection.open:
                self.connection = pymysql.connect(
                    host=self.config.MYSQL_HOST,
                    port=self.config.MYSQL_PORT,
                    user=self.config.MYSQL_USER,
                    password=self.config.MYSQL_PASSWORD,
                    database=self.config.MYSQL_DATABASE,
                    charset=self.config.MYSQL_CHARSET,
                    cursorclass=pymysql.cursors.DictCursor
                )
            return self.connection
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def import_from_csv(self, csv_path=None):
        """从CSV文件导入数据到数据库"""
        if csv_path is None:
            csv_path = self.config.CSV_FILE_PATH
        
        try:
            # 读取CSV文件
            df = pd.read_csv(
                csv_path,
                sep=',',  # 根据你的CSV分隔符调整
                encoding='GB2312',  # 处理BOM头
                dtype=str,  # 所有列都作为字符串读取
                na_filter=False  # 不将空字符串转换为NaN
            )
            
            # 重命名列以匹配数据库字段
            df = df.rename(columns={
                '大类': 'category',
                '子类': 'subcategory',
                '软件/数据库名称': 'name',
                '功能特点': 'features',
                '链接': 'url',
                '论文DOI': 'doi'
            })
            
            # 处理空值
            df = df.where(pd.notnull(df), None)
            
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # 清空现有数据（可选）
            cursor.execute("TRUNCATE TABLE bioinfo_software")
            
            # 批量插入数据
            batch_size = 100
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                # 构建插入SQL
                sql = """
                INSERT INTO bioinfo_software 
                (category, subcategory, name, features, url, doi)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                # 准备数据
                values = []
                for _, row in batch.iterrows():
                    values.append((
                        row['category'],
                        row['subcategory'] if pd.notnull(row['subcategory']) else None,
                        row['name'],
                        row['features'] if pd.notnull(row['features']) else None,
                        row['url'] if pd.notnull(row['url']) else None,
                        row['doi'] if pd.notnull(row['doi']) else None
                    ))
                
                # 执行批量插入
                cursor.executemany(sql, values)
                conn.commit()
                print(f"已导入 {min(i+batch_size, len(df))}/{len(df)} 条记录")
            
            print(f"✅ 成功导入 {len(df)} 条记录到数据库")
            return True
            
        except Exception as e:
            print(f"CSV导入失败: {e}")
            return False
        finally:
            if conn:
                cursor.close()
    
    def get_all_software(self):
        """获取所有软件数据"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT category, subcategory, name, features, url, doi
            FROM bioinfo_software
            ORDER BY category, subcategory, name
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"查询失败: {e}")
            return []
        finally:
            cursor.close()