# Bioinformatic tools website

## Introduction

- A website containing description and links for different kinds of usefull bioinformatic tools.

- Also validate the following apis:

  - RNAfold from ViennaRNA packages: 

    - Lorenz R, Bernhart SH, Höner Zu Siederdissen C, Tafer H, Flamm C, Stadler PF, Hofacker IL. ViennaRNA Package 2.0. Algorithms Mol Biol. 2011 Nov 24;6:26. doi: 10.1186/1748-7188-6-26. PMID: 22115189; PMCID: PMC3319429.

  - Alphafold3 if there is a valid version created in docker following the construct of https://github.com/google-deepmind/alphafold3

    - Change the settings in /api/alphafold3.py if you can't run AF as following:

      ```bash
      docker run -it \
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
            --gpu_device=0
      ```

## Usage 

- Python requirements are in `requirements.txt`.
- For beginers, run `./setup.sh` to set up the database.
- Change the settings in `.env` into your own settings.
- Some unsafety usage included (especially in `terminal`) should be removed if publically used.
  - Just for simplicity to monitor the running process of AF.

