# app.py - 修复版本
from flask import Flask, render_template, jsonify, request
from sqlalchemy import create_engine, text
from config.config import Config
from flask_socketio import SocketIO
import subprocess
import threading
from api.test import process_test_files
from api.RNAfold import process_rnafold_files
from api.alphafold3 import process_alphafold_files

app = Flask(__name__)
app.config.from_object(Config())

## 创建数据库引擎
engine = create_engine(
    app.config['SQLALCHEMY_DATABASE_URI'],
    echo=False
)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/get_software_data')
def get_software_data():
    """API端点：从数据库获取软件数据并构建树形结构"""
    try:
        with engine.connect() as connection:
            # 查询所有数据
            query = text("""
                SELECT category, subcategory, name, features, url, doi
                FROM bioinfo_software
                ORDER BY category, subcategory, name
            """)
            
            result = connection.execute(query)
            rows = result.fetchall()
            
            # 转换为树形结构
            data_tree = {}
            for row in rows:
                # 处理行数据的格式
                if hasattr(row, '_mapping'):
                    category = row._mapping['category']
                    subcategory = row._mapping['subcategory'] if row._mapping['subcategory'] else '其他'
                    name = row._mapping['name']
                else:
                    # 如果是元组格式
                    category = row[0]
                    subcategory = row[1] if row[1] else '其他'
                    name = row[2]
                
                if category not in data_tree:
                    data_tree[category] = {}
                if subcategory not in data_tree[category]:
                    data_tree[category][subcategory] = []
                
                data_tree[category][subcategory].append(name)
            
            return jsonify(data_tree)
            
    except Exception as e:
        app.logger.error(f"API错误: {e}")
        return jsonify({'error': '数据加载失败'}), 500

@app.route('/api/get_software_details')
def get_software_details():
    """获取软件的详细信息"""
    try:
        name = request.args.get('name', '')
        if not name:
            return jsonify({'error': '需要软件名称参数'}), 400
        
        with engine.connect() as connection:
            query = text("""
                SELECT category, subcategory, name, features, url, doi
                FROM bioinfo_software
                WHERE name = :name
            """)
            
            result = connection.execute(query, {'name': name})
            row = result.fetchone()
            
            if not row:
                return jsonify({'error': '未找到该软件'}), 404
            
            # 转换为字典
            if hasattr(row, '_mapping'):
                data = dict(row._mapping)
            else:
                data = {
                    'category': row[0],
                    'subcategory': row[1],
                    'name': row[2],
                    'features': row[3],
                    'url': row[4],
                    'doi': row[5]
                }
            
            return jsonify(data)
            
    except Exception as e:
        app.logger.error(f"详情查询失败: {e}")
        return jsonify({'error': '查询失败'}), 500
    
## Terminal
socketio = SocketIO(app)

ALLOWED_COMMANDS = {'pwd': ['pwd'], 'ls': ['ls', '-la'], 'date': ['date'], 'nvidia-smi': ['nvidia-smi'], "AFoutput": ['ls', './processed/alphafold']}

def execute_long_command(command_key, sid):
    """在后台线程中执行命令，并实时推送输出"""
    if command_key[:8] == "YXMMGSWS":
        try:
            proc = subprocess.Popen(['cat', f'/home/abc/course/bio3514/project/Project/BioInfoWeb/processed/alphafold/{command_key[8:]}/alphafold_docker.log'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    bufsize=1,  # 行缓冲
                                    shell=False)

            # 实时读取输出并推送
            for line in iter(proc.stdout.readline, ''):
                if line:
                    socketio.emit('command_output', {'data': line}, room=sid)

            proc.stdout.close()
            return_code = proc.wait(timeout=2)
            if return_code != 0:
                socketio.emit('command_output', {'data': f"\n命令结束，返回值: {return_code}"}, room=sid)

            return

        except Exception as e:
            socketio.emit('command_output', {'data': f"执行异常: {str(e)}"}, room=sid)

    if command_key not in ALLOWED_COMMANDS:
        socketio.emit('command_output', {'data': f"错误: 命令 '{command_key}' 未被允许。"}, room=sid)
        return

    try:
        proc = subprocess.Popen(ALLOWED_COMMANDS[command_key],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1,  # 行缓冲
                                shell=False)

        # 实时读取输出并推送
        for line in iter(proc.stdout.readline, ''):
            if line:
                socketio.emit('command_output', {'data': line}, room=sid)

        proc.stdout.close()
        return_code = proc.wait(timeout=2)
        if return_code != 0:
            socketio.emit('command_output', {'data': f"\n命令结束，返回值: {return_code}"}, room=sid)

    except Exception as e:
        socketio.emit('command_output', {'data': f"执行异常: {str(e)}"}, room=sid)

@socketio.on('execute_command')
def handle_command(data):
    """接收前端发送的命令"""
    command = data.get('command', '').strip()
    # 关键：通过 request.sid 获取当前客户端会话的唯一ID，用于定向推送消息
    session_id = request.sid
    # 启动后台线程执行命令，避免阻塞SocketIO主线程
    thread = threading.Thread(target=execute_long_command, args=(command, session_id))
    thread.daemon = True
    thread.start()


@app.route('/api/test_connection')
def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM bioinfo_software"))
            count = result.scalar()
            return jsonify({
                'status': 'success',
                'message': f'数据库连接正常，共有{count}条记录'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
@app.route('/terminal')
def terminal_page():
    """服务于终端页面"""
    return render_template('terminal.html')

## file upload sys
import os
import uuid
from datetime import datetime
from flask import Flask, request, render_template, send_file, jsonify
import threading
from werkzeug.utils import secure_filename

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = 'uploads'
PROCESSED_BASE = 'processed'

# Page config for biotools
PAGE_CONFIGS = {
    'test': {
        'template': 'AppTest.html',
        'upload_dir': os.path.join(UPLOAD_BASE, 'test'),
        'processed_dir': os.path.join(PROCESSED_BASE, 'test'),
        'allowed_extensions': {'txt', 'csv', 'json', 'xlsx', 'pdf', 'fa'},
        'max_size_mb': 100  # 100MB
    },
    'rnafold': {
        'template': 'api_RNAfold.html',
        'upload_dir': os.path.join(UPLOAD_BASE, 'rnafold'),
        'processed_dir': os.path.join(PROCESSED_BASE, 'rnafold'),
        'allowed_extensions': {'fasta', 'fa', 'txt', 'seq'},
        'max_size_mb': 10  # 10MB
    },
    'alphafold': {
        'template': 'api_alphafold.html',
        'upload_dir': os.path.join(UPLOAD_BASE, 'alphafold'),
        'processed_dir': os.path.join(PROCESSED_BASE, 'alphafold'),
        'allowed_extensions': {'json'},
        'max_size_mb': 1024  # 1024MB
    }
}

def get_page_config(page_type):
    """获取页面配置"""
    return PAGE_CONFIGS.get(page_type, PAGE_CONFIGS['test'])

def allowed_file(filename, page_type):
    """检查文件类型是否允许"""
    config = get_page_config(page_type)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config['allowed_extensions']

# Function dict for different apis
API_INFO = {
    'test': {
        'func': process_test_files,
        'config_key': 'test'
    },
    'rnafold': {
        'func': process_rnafold_files,
        'config_key': 'rnafold'
    },
    'alphafold': {
        'func': process_alphafold_files,
        'config_key': 'alphafold'
    }
}

API_AVI = ['test', 'rnafold', 'alphafold']

# mkdir for configuration
for config in PAGE_CONFIGS.values():
    os.makedirs(config['upload_dir'], exist_ok=True)
    os.makedirs(config['processed_dir'], exist_ok=True)

# 任务状态存储
tasks = {}


# ========== 路由定义 ==========
@app.route('/upload/<page_type>', methods=['POST'])
def upload_files(page_type):
    """通用上传接口，根据page_type选择处理方式"""
    if page_type not in PAGE_CONFIGS:
        return jsonify({'error': f'未知的页面类型: {page_type}'}), 400
    
    config = get_page_config(page_type)
    
    if 'files' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': '没有选择文件'}), 400
    
    # 检查文件大小
    max_size = config['max_size_mb'] * 1024 * 1024
    for file in files:
        file.seek(0, 2)  # 移动到文件末尾
        size = file.tell()
        file.seek(0)  # 重置文件指针
        if size > max_size:
            return jsonify({
                'error': f'文件太大: {file.filename}',
                'max_size_mb': config['max_size_mb']
            }), 400
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务目录
    task_dir = os.path.join(config['upload_dir'], task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # 保存上传的文件
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename, page_type):
            filename = secure_filename(file.filename)
            filepath = os.path.join(task_dir, filename)
            file.save(filepath)
            saved_files.append(filepath)
        else:
            return jsonify({
                'error': f'不支持的文件类型: {file.filename}',
                'allowed_extensions': list(config['allowed_extensions'])
            }), 400
    
    # 初始化任务信息
    tasks[task_id] = {
        'id': task_id,
        'page_type': page_type,
        'status': 'pending',
        'progress': 0,
        'message': '等待处理...',
        'start_time': datetime.now().isoformat(),
        'file_count': len(saved_files),
        'filenames': [os.path.basename(f) for f in saved_files]
    }
    
    # 创建输出目录
    output_dir = os.path.join(config['processed_dir'], task_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # 根据页面类型选择处理函数
    if page_type in API_AVI:
        process_func = API_INFO[page_type]['func']
        zip_path = os.path.join(get_page_config(page_type)['processed_dir'], f'{task_id}.zip')
    else:
        return jsonify({'error': '不支持的页面类型'}), 400
    
    # 在后台线程中处理文件
    thread = threading.Thread(
        target=process_func,
        args=(task_id, saved_files, output_dir, tasks, zip_path)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'page_type': page_type,
        'message': '文件上传成功，开始处理',
        'file_count': len(saved_files),
        'status_url': f'/status/{task_id}'
    })

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """获取任务状态"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(tasks[task_id])

@app.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    """下载处理结果"""
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task_info = tasks[task_id]
    page_type = task_info.get('page_type', 'test')
    
    if task_info['status'] != 'completed':
        return jsonify({'error': '任务尚未完成'}), 400
    
    zip_path = task_info.get('output_path')
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({'error': '结果文件不存在'}), 404
    
    # 根据页面类型设置下载文件名
    if page_type in API_AVI:
        filename = f'{page_type}_results_{task_id}.zip'
    else:
        filename = f'results_{task_id}.zip'
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务（用于调试）"""
    return jsonify({
        'tasks': {
            task_id: {
                'status': info['status'],
                'progress': info['progress'],
                'start_time': info['start_time']
            }
            for task_id, info in tasks.items()
        }
    })

# 清理旧任务文件的函数（可选）
# def cleanup_old_files():
#     """定期清理旧文件"""
#     import time
#     while True:
#         time.sleep(3600)  # 每小时清理一次
#         now = time.time()
#         max_age = 24 * 3600  # 24小时
        
#         for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
#             for root, dirs, files in os.walk(folder):
#                 for file in files:
#                     filepath = os.path.join(root, file)
#                     if os.path.getctime(filepath) < now - max_age:
#                         os.remove(filepath)


## Api page
@app.route('/api', methods=['GET'])
def api():
    """API文档页面"""
    return render_template('api.html')

@app.route('/api/test', methods=['GET'])
def api_test():
    """API 测试页面"""
    return render_template('AppTest.html')

@app.route('/api/RNAfold', methods=['GET'])
def api_RNAfold():
    """API RNAfold"""
    return render_template('api_RNAfold.html')

@app.route('/api/alphafold')
def api_alphafold():
    """API RNAfold"""
    return render_template('api_alphafold.html')


if __name__ == '__main__':
    print("=" * 60)
    print("生物信息学软件目录系统")
    print("=" * 60)
    print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else app.config['SQLALCHEMY_DATABASE_URI']}")
    print("启动Flask应用...")
    print("访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)