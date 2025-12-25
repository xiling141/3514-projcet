- 20251217 test the python package: pymysql & SQLAlchemy
```bash
python pymysql_test.py
```
```
Return all tables in test
[{'Tables_in_test': 'InnoDB_TABLE'}, {'Tables_in_test': 'MyISAM_TABLE'}, {'Tables_in_test': 'account'}]
```
```bash
python SQLAlchemy_test.py
```
```
Return all tables in test
('InnoDB_TABLE',)
('MyISAM_TABLE',)
('account',)
Use SQLAlchemy as the main package for mysql construction
```
- 20251217 Test json-style data for biotools
```bash
cd basic_storage # folder for test
python app.py # Excellent performance
```
- 20251217 Create database
```
-- 创建数据库
CREATE DATABASE IF NOT EXISTS bioinfo_software DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
USE bioinfo_software;

-- 创建软件信息表
CREATE TABLE IF NOT EXISTS bioinfo_software (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL COMMENT '大类',
    subcategory VARCHAR(100) COMMENT '子类',
    name VARCHAR(200) NOT NULL COMMENT '软件/数据库名称',
    features TEXT COMMENT '功能特点',
    url VARCHAR(500) COMMENT '链接',
    doi VARCHAR(200) COMMENT '论文DOI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 添加索引以提高查询性能
    INDEX idx_category (category),
    INDEX idx_subcategory (subcategory),
    INDEX idx_name (name(50)),
    INDEX idx_category_subcategory (category, subcategory)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生物信息学软件目录';

-- 可选：创建分类表（用于规范化）
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE COMMENT '分类名称',
    description TEXT COMMENT '分类描述'
);

CREATE TABLE IF NOT EXISTS subcategories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    subcategory_name VARCHAR(100) NOT NULL COMMENT '子类名称',
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY uk_category_sub (category_id, subcategory_name)
);
```
- 20251217 test the encoding of csv file
```python
# utils/detect_encoding.py
import chardet

def detect_file_encoding(file_path):
    """检测文件的真实编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取前10000字节用于检测
        result = chardet.detect(raw_data)
        
    encoding = result['encoding']
    confidence = result['confidence']
    print(f"检测到编码: {encoding} (置信度: {confidence:.2%})")
    print(f"示例数据: {raw_data[:100]}")
    
    # 尝试用检测到的编码读取
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            sample = f.read(500)
            print(f"\n成功用 {encoding} 编码读取，前500字符:")
            print(sample)
        return encoding
    except Exception as e:
        print(f"用 {encoding} 编码读取失败: {e}")
        return None

# 运行检测
detect_file_encoding('biotool.csv')
```
- 20251217 Convert tuple into dict
```python
DATABASE_URL = "mysql+pymysql://root:tianmao666@localhost:3306/test"

# 使用 mysql-connector-python 作为驱动
# DATABASE_URL = "mysql+mysqlconnector://username:password@localhost:3306/database"

# 使用 PostgreSQL
# DATABASE_URL = "postgresql://username:password@localhost:5432/database"

from sqlalchemy import create_engine, text
DATABASE_URL = "mysql+pymysql://root:tianmao666@localhost:3306/bioinfo_software"
engine = create_engine(DATABASE_URL)

# 使用SQL表达式语言
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM bioinfo_software WHERE category=\"序列比对与搜索工具\";"))

    columns = result.keys()
    
    # 构建字典迭代器
    rows = result.fetchall()

    res = [dict(zip(columns, row)) for row in rows]
```