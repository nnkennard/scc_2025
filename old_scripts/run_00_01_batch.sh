#!/bin/bash
#SBATCH --job-name=extract_text
#SBATCH --nodes=1 --ntasks=1
#SBATCH --output=logs/extract_text_%A_%a.out
#SBATCH --error=logs/extract_text_%A_%a.err
#SBATCH -p gpu  # Partition
#SBATCH -G 1  # Number of GPUs
#SBATCH --array=0-5
#SBATCH --time=1-00:00:00
#SBATCH --time-min=0-04:00:00

array=( $(seq 2018 2023 ) )

module load conda/latest
conda activate testName
export PATH=$PATH:/work/pi_mccallum_umass_edu/nnayak_umass_edu/scc_2025/xpdf-tools-linux-4.05/bin64
cd /work/pi_mccallum_umass_edu/nnayak_umass_edu/scc_2025/00_extract
python 01_extract_text.py \
	-d /gypsum/work1/mccallum/nnayak/scc_2025_recorded/\
	-c iclr_${array[$SLURM_ARRAY_TASK_ID]}

