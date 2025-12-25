import os
import json
import zipfile
from datetime import datetime

# ========== TEST页面处理函数 ==========
def process_test_files(task_id, files, output_dir, tasks, zip_path):
    """Test页面的文件处理逻辑"""
    try:
        task_info = tasks[task_id]
        task_info['status'] = 'processing'
        task_info['progress'] = 10
        task_info['message'] = '开始处理测试文件...'
        
        # 1. 创建处理目录
        processed_files_dir = os.path.join(output_dir, 'test_results')
        os.makedirs(processed_files_dir, exist_ok=True)
        
        results = []
        
        # 2. 处理每个文件（示例：文本分析）
        for i, filepath in enumerate(files):
            filename = os.path.basename(filepath)
            
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 示例处理：计算文件统计信息
            stats = {
                'filename': filename,
                'size': os.path.getsize(filepath),
                'lines': len(content.splitlines()),
                'words': len(content.split()),
                'chars': len(content)
            }
            
            # 保存统计结果
            stats_file = os.path.join(processed_files_dir, f'{filename}_stats.json')
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            results.append(stats)
            
            # 更新进度
            progress = 10 + int((i + 1) / len(files) * 80)
            task_info['progress'] = progress
            task_info['message'] = f'已处理 {i+1}/{len(files)} 个文件'
        
        # 3. 生成汇总报告
        summary_file = os.path.join(output_dir, 'summary_report.txt')
        with open(summary_file, 'w') as f:
            f.write(f"=== 测试文件处理报告 ===\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write(f"处理文件总数: {len(files)}\n")
            f.write(f"总字符数: {sum(r['chars'] for r in results)}\n")
            f.write(f"总行数: {sum(r['lines'] for r in results)}\n")
            f.write("\n=== 文件详情 ===\n")
            for r in results:
                f.write(f"\n文件: {r['filename']}\n")
                f.write(f"  大小: {r['size']} bytes\n")
                f.write(f"  行数: {r['lines']}\n")
                f.write(f"  单词数: {r['words']}\n")
        
        task_info['progress'] = 95
        task_info['message'] = '正在创建压缩包...'
        
        # 4. 创建压缩包
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
        
        task_info['progress'] = 100
        task_info['status'] = 'completed'
        task_info['download_url'] = f'/download/{task_id}?page_type=test'
        task_info['output_path'] = zip_path
        task_info['message'] = '处理完成！'
        task_info['summary'] = {
            'total_files': len(files),
            'total_chars': sum(r['chars'] for r in results),
            'total_lines': sum(r['lines'] for r in results)
        }
        
    except Exception as e:
        task_info['status'] = 'error'
        task_info['message'] = f'处理失败: {str(e)}'
        import traceback
        task_info['error_details'] = traceback.format_exc()