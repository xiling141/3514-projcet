import os

current_file_path = __file__ # Complete path for docker
family_folder = current_file_path.split(sep='/api/')[0]
alphafold_results_dir = os.path.join(family_folder, 'outp', 'alphafold_analysis')

print(alphafold_results_dir)