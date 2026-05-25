#!/bin/bash
export PYTHONNOUSERSITE=1

CUDA_VISIBLE_DEVICES=0 nohup python eval/run_eval.py --config eval/eval_config.yaml > eval.log 2>&1 &
CUDA_VISIBLE_DEVICES=0 nohup python eval/run_eval.py --config eval/eval_config_base.yaml > eval_base.log 2>&1 &