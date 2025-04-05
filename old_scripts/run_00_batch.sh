#!/bin/bash
#SBATCH --job-name=get_revisions
#SBATCH --nodes=1 --ntasks=1
#SBATCH --output=logs/getRevisions_%A_%a.out
#SBATCH --error=logs/getRevisions_%A_%a.err
#SBATCH -p gpu  # Partition
#SBATCH -G 1  # Number of GPUs
#SBATCH --array=0-5
#SBATCH --time=1-00:00:00
#SBATCH --time-min=0-04:00:00

array=( $(seq 2018 2023 ) )

module load conda/latest
conda activate testName
python 00_get_revisions.py -o /gypsum/work1/mccallum/nnayak/scc_2025_recorded/\
	 -c iclr_${array[$SLURM_ARRAY_TASK_ID]}

