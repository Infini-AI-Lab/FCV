#!/bin/bash

set -e

MODELS=(claude-sonnet-4 gpt-5-mini qwen kimi-official)
CWE_TYPES=(cwe_538 cwe_79 cwe_89 cwe_94)

RESULT_FILE=$1
RESULT_FILE_DIR=$2

NUM_RUNS=1

for CWE_TYPE in ${CWE_TYPES[@]}; do
    for MODEL in ${MODELS[@]}; do
        OUTPUT_DIR=${RESULT_FILE_DIR}/${CWE_TYPE}-${MODEL}
        
        echo "Running $CWE_TYPE with $MODEL"
        python run_simple.py --cwe_type $CWE_TYPE --model $MODEL --result_file $RESULT_FILE --output_dir $OUTPUT_DIR --num_runs $NUM_RUNS 
    done
done
