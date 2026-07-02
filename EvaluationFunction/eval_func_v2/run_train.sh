#!/bin/bash
#SBATCH -p mpi-homo-short
#SBATCH -A nprg042s
#SBATCH --job-name=logix_train
#SBATCH --output=train_%j.out
#SBATCH --error=train_%j.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G

cd ~/eval_func_v2
source venv/bin/activate

python train.py