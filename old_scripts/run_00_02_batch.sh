#!/bin/bash
#SBATCH --job-name=clean_iclr
#SBATCH --nodes=1 --ntasks=1
#SBATCH --output=logs/clean_iclr_%A_%a.out
#SBATCH --error=logs/clean_iclr_%A_%a.err
#SBATCH --array=0-5
#SBATCH --time=1-00:00:00
#SBATCH --time-min=0-04:00:00

array=( $(seq 2018 2023 ) )

module load conda/latest
conda activate testName
cd /work/pi_mccallum_umass_edu/nnayak_umass_edu/scc_2025/00_extract
python 02_clean_iclr.py \
	-d /gypsum/work1/mccallum/nnayak/scc_2025_recorded/\
	-c iclr_${array[$SLURM_ARRAY_TASK_ID]}

