import ViennaRNA as RNA
from Bio import SeqIO
import os
import zipfile
import json

# ========== RNAfold页面处理函数 ==========
def process_rnafold_files(task_id, files, output_dir, tasks, zip_path):
    """RNAfold页面的文件处理逻辑"""
    try:
        task_info = tasks[task_id]
        task_info['status'] = 'processing'
        task_info['progress'] = 10
        task_info['message'] = '开始RNAfold分析...'
        
        # 1. 创建RNAfold结果目录
        rnafold_results_dir = os.path.join(output_dir, 'rnafold_analysis')
        os.makedirs(rnafold_results_dir, exist_ok=True)
        
        # 2. 处理FASTA文件
        for i, filepath in enumerate(files):
            filename = os.path.basename(filepath)
            sequences = []
            
            # 读取FASTA文件
            for record in SeqIO.parse(filepath, "fasta"):
                sequences.append((str(record.id),str(record.seq)))
            
            # 对每个序列运行RNAfold
            analysis_results = []
            for seq_id, sequence in sequences:
                structure, energy = RNA.fold(sequence)
                
                result = {
                    'id': seq_id,
                    'sequence': sequence,
                    'structure': structure,
                    'energy': energy,
                    'length': len(sequence)
                }
                analysis_results.append(result)
            
            # 保存分析结果
            result_file = os.path.join(rnafold_results_dir, f'{filename}_analysis.json')
            with open(result_file, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            
            # 生成可视化文件（示例）
            viz_file = os.path.join(rnafold_results_dir, f'{filename}_viz.txt')
            with open(viz_file, 'w') as f:
                f.write(f"RNAfold Analysis for {filename}\n")
                f.write("=" * 50 + "\n")
                for result in analysis_results:
                    f.write(f"\nSequence: {result['id']}\n")
                    f.write(f"Length: {result['length']}\n")
                    f.write(f"Energy: {result['energy']} kcal/mol\n")
                    f.write(f"Structure: {result['structure']}\n")
                    f.write(f"Sequence: {result['sequence']}\n")
                    f.write("-" * 30 + "\n")
            
            # 更新进度
            progress = 10 + int((i + 1) / len(files) * 80)
            task_info['progress'] = progress
            task_info['message'] = f'已分析 {i+1}/{len(files)} 个文件'
        
        # 3. 生成汇总报告
        summary_file = os.path.join(output_dir, 'rnafold_summary.txt')
        # 这里可以添加更多的统计信息
        
        task_info['progress'] = 95
        task_info['message'] = '正在生成最终报告...'
        
        # 4. 创建压缩包
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
        
        task_info['progress'] = 100
        task_info['status'] = 'completed'
        task_info['download_url'] = f'/download/{task_id}?page_type=rnafold'
        task_info['output_path'] = zip_path
        task_info['message'] = 'RNAfold分析完成！'
        
    except Exception as e:
        task_info['status'] = 'error'
        task_info['message'] = f'RNAfold分析失败: {str(e)}'
        import traceback
        task_info['error_details'] = traceback.format_exc()

