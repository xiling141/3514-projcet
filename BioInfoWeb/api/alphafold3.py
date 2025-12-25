import os
import zipfile
import subprocess
import threading
import time
from datetime import datetime

# ========== alphafold页面处理函数 ==========
def process_alphafold_files(task_id, files, output_dir, tasks, zip_path):
    """alphafold页面的文件处理逻辑"""
    current_file_path = __file__ # Complete path for docker
    family_folder = current_file_path.split(sep='/api/')[0]
    try:
        task_info = tasks[task_id]
        task_info['status'] = 'processing'
        task_info['progress'] = 10
        task_info['message'] = '准备运行AlphaFold3...'
        
        # 保存文件列表到任务信息
        task_info['file_count'] = len(files)
        task_info['input_files'] = [os.path.basename(f) for f in files]
        
        # 1. 创建alphafold结果目录
        alphafold_results_dir = os.path.join(family_folder, output_dir, 'alphafold_analysis') # full path
        os.makedirs(alphafold_results_dir, exist_ok=True)
        
        # 2. 创建输入目录并复制所有JSON文件
        remote_input_dir = f"$HOME/AF/input/Remote/{task_id}/"
        subprocess.run(f'mkdir -p {remote_input_dir}', shell=True, check=True)
        
        task_info['message'] = f'正在复制 {len(files)} 个输入文件...'
        
        for filepath in files:
            subprocess.run(f'cp "{filepath}" "{remote_input_dir}"', shell=True, check=True)
        
        # 3. 启动进度监控线程
        monitor_thread = threading.Thread(
            target=monitor_alphafold_progress,
            args=(task_id, remote_input_dir, alphafold_results_dir, tasks, len(files))
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 4. 创建日志文件路径
        summary_file = os.path.join(output_dir, 'alphafold_summary.txt')
        log_file = os.path.join(output_dir, 'alphafold_docker.log')
        
        # 5. 运行alphafold3
        task_info['message'] = '正在启动AlphaFold3 Docker容器...'
        
        # 构建docker命令
        docker_cmd = f"""docker run -it \
            --volume $HOME/AF/input:/root/af_input \
            --volume {alphafold_results_dir}:/root/af_output \
            --volume $HOME/AF/models:/root/models \
            --volume $HOME/AF/db:/root/public_databases \
            -e CUDA_VISIBLE_DEVICES=1 \
            --gpus all \
            alphafold3 \
            python run_alphafold.py \
            --input_dir="/root/af_input/Remote/{task_id}" \
            --model_dir=/root/models \
            --output_dir="/root/af_output" \
            --gpu_device=0"""
        
        # 执行命令，捕获输出
        try:
            task_info['message'] = 'AlphaFold3正在运行中...'
            task_info['docker_command'] = docker_cmd
            task_info['start_time'] = datetime.now().isoformat()
            
            with open(log_file, 'w') as log_f:
                log_f.write(f"AlphaFold3 Execution Log\n")
                log_f.write(f"Task ID: {task_id}\n")
                log_f.write(f"Start Time: {datetime.now()}\n")
                log_f.write(f"Input Files: {len(files)}\n")
                log_f.write(f"Docker Command:\n{docker_cmd}\n")
                log_f.write("-" * 80 + "\n\n")
                
                # 执行docker命令
                process = subprocess.Popen(
                    docker_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # 实时写入日志
                for line in process.stdout:
                    log_f.write(line)
                    log_f.flush()
                    # 可以在这里添加实时进度解析逻辑
                
                process.wait()
                return_code = process.returncode
            
            # 写入结束信息
            with open(log_file, 'a') as log_f:
                log_f.write("\n" + "=" * 80 + "\n")
                log_f.write(f"End Time: {datetime.now()}\n")
                log_f.write(f"Return Code: {return_code}\n")
                log_f.write(f"Execution Complete\n")
        
        except subprocess.CalledProcessError as e:
            task_info['status'] = 'error'
            task_info['message'] = f'AlphaFold3执行失败: {e.stderr}'
            task_info['error_details'] = str(e)
            return
        
        # 6. 检查输出文件
        output_files = []
        if os.path.exists(alphafold_results_dir):
            for root, dirs, files_in_dir in os.walk(alphafold_results_dir):
                for file in files_in_dir:
                    if file.endswith(('.pdb', '.json', '.cif', '.pkl')):
                        output_files.append(os.path.join(root, file))
        
        task_info['output_files_count'] = len(output_files)
        task_info['output_files'] = [os.path.basename(f) for f in output_files[:10]]  # 只显示前10个
        
        # 7. 生成汇总报告
        generate_summary_report(task_id, output_dir, len(files), len(output_files), log_file)
        
        task_info['progress'] = 95
        task_info['message'] = '正在创建结果压缩包...'
        
        # 8. 创建压缩包
        create_result_zip(output_dir, zip_path)
        
        task_info['progress'] = 100
        task_info['status'] = 'completed'
        task_info['download_url'] = f'/download/{task_id}?page_type=alphafold'
        task_info['output_path'] = zip_path
        task_info['message'] = f'AlphaFold3分析完成！生成 {len(output_files)} 个结果文件'
        task_info['end_time'] = datetime.now().isoformat()
        
    except Exception as e:
        task_info['status'] = 'error'
        task_info['message'] = f'AlphaFold3分析失败: {str(e)}'
        import traceback
        task_info['error_details'] = traceback.format_exc()


def monitor_alphafold_progress(task_id, input_dir, output_dir, tasks, total_input_files):
    """监控AlphaFold处理进度（每10分钟检查一次）"""
    while True:
        time.sleep(600)  # 每10分钟检查一次
        
        task_info = tasks.get(task_id)
        if not task_info or task_info['status'] in ['completed', 'error']:
            break
        
        try:
            # 检查输出目录
            output_count = 0
            if os.path.exists(output_dir):
                # 统计PDB和其他结果文件
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(('.pdb', '.json', '.cif', '.pkl', '.pdb.gz')):
                            output_count += 1
            
            # 计算进度（输出文件数 / 输入文件数 * 80% + 10%基础进度）
            if total_input_files > 0:
                progress = min(90, 10 + int((output_count / total_input_files) * 80))
            else:
                progress = task_info.get('progress', 10)
            
            # 更新任务信息
            task_info['progress'] = progress
            task_info['message'] = f'AlphaFold3处理中... 已生成 {output_count}/{total_input_files} 个结果文件'
            task_info['current_output_count'] = output_count
            
            # 写入进度日志
            progress_log = os.path.join(os.path.dirname(output_dir), 'progress.log')
            with open(progress_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - 进度: {progress}%, 输出文件: {output_count}\n")
                
        except Exception as e:
            # 监控错误不影响主流程
            pass


def generate_summary_report(task_id, output_dir, input_count, output_count, log_file):
    """生成AlphaFold汇总报告"""
    summary_file = os.path.join(output_dir, 'alphafold_summary.txt')
    
    # 读取docker日志的最后100行
    log_tail = ""
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                log_tail = "\n".join(lines[-100:])  # 最后100行
        except:
            log_tail = "无法读取日志文件"
    
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("AlphaFold3 分析报告\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"任务ID: {task_id}\n")
        f.write(f"生成时间: {datetime.now()}\n")
        f.write(f"输入文件数量: {input_count}\n")
        f.write(f"输出文件数量: {output_count}\n")
        f.write(f"处理状态: 完成\n\n")
        
        f.write("输出文件类型统计:\n")
        if os.path.exists(os.path.join(output_dir, 'alphafold_analysis')):
            file_types = {}
            for root, dirs, files in os.walk(os.path.join(output_dir, 'alphafold_analysis')):
                for file in files:
                    ext = os.path.splitext(file)[1]
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            for ext, count in file_types.items():
                f.write(f"  {ext}: {count} 个文件\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("执行日志（最后100行）:\n")
        f.write("=" * 80 + "\n")
        f.write(log_tail)


def create_result_zip(output_dir, zip_path):
    """创建结果压缩包，排除中间文件"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加所有文件到压缩包，但跳过临时文件
        skip_extensions = {'.tmp', '.log', '.lock', '.swp'}
        skip_dirs = {'tmp', 'temp', '__pycache__'}
        
        for root, dirs, files in os.walk(output_dir):
            # 跳过特定目录
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                # 跳过特定扩展名
                if any(file.endswith(ext) for ext in skip_extensions):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)


def get_alphafold_status(task_id, tasks):
    """获取AlphaFold任务状态（供状态查询API调用）"""
    task_info = tasks.get(task_id)
    if not task_info:
        return None
    
    # 如果任务正在处理，检查最新输出文件数
    if task_info['status'] == 'processing':
        output_dir = task_info.get('output_path', '').replace('.zip', '')
        if output_dir and os.path.exists(output_dir):
            alphafold_dir = os.path.join(output_dir, 'alphafold_analysis')
            if os.path.exists(alphafold_dir):
                output_count = 0
                for root, dirs, files in os.walk(alphafold_dir):
                    for file in files:
                        if file.endswith(('.pdb', '.json', '.cif', '.pkl')):
                            output_count += 1
                
                input_count = task_info.get('file_count', 1)
                if input_count > 0:
                    progress = min(90, 10 + int((output_count / input_count) * 80))
                    task_info['progress'] = progress
                    task_info['current_output_count'] = output_count
                    task_info['message'] = f'AlphaFold3处理中... 已生成 {output_count}/{input_count} 个结果文件'
    
    return task_info