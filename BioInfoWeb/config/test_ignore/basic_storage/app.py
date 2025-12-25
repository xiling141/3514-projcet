# app.py
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# 这是你的原始数据，可以放在这里，未来也可以改为从数据库读取
raw_data = [
    {"大类": "序列比对与搜索工具", "子类": "短读长比对工具", "名称": "BWA"},
    {"大类": "序列比对与搜索工具", "子类": "短读长比对工具", "名称": "Bowtie2"},
    # ... 将你提供的所有数据行都放在这个列表里
    {"大类": "基因组分析软件", "子类": "基因组组装工具", "名称": "SPAdes"}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_software_data')
def get_data():
    # 核心：将平铺的表格数据转换为嵌套的树形字典
    data_tree = {}
    for item in raw_data:
        category = item["大类"]
        subcategory = item["子类"] if item["子类"] else "其他" # 处理子类为空的情况
        name = item["名称"]
        
        # 构建嵌套结构
        if category not in data_tree:
            data_tree[category] = {}
        if subcategory not in data_tree[category]:
            data_tree[category][subcategory] = []
        data_tree[category][subcategory].append(name)
    
    return jsonify(data_tree)

if __name__ == '__main__':
    app.run(debug=True)