#!/bin/bash

# Simplified CWE Injection Experiment Script
# Supports skipping already completed instances
# Usage: ./run_cwe_simple.sh <report_json_path> <cwe_type> <config_name> [num_rounds] [existing_output_dir] [use_existing_dir]

REPORT_JSON_PATH=$1
CWE_TYPE=$2
CONFIG_NAME=$3
NUM_ROUNDS=${4:-1}
EXISTING_OUTPUT_DIR=$5
USE_EXISTING_DIR=${6:-false}

# Validate parameters
if [ -z "$REPORT_JSON_PATH" ] || [ -z "$CWE_TYPE" ] || [ -z "$CONFIG_NAME" ]; then
    echo "Usage: $0 <report_json_path> <cwe_type> <config_name> [num_rounds] [existing_output_dir] [use_existing_dir]"
    echo "Example: $0 /path/to/report.json cwe_532 llm.eval_gpt5_mini 1"
    echo "Example: $0 /path/to/report.json cwe_79 llm.eval_kimi 1 /path/to/existing/output true"
    exit 1
fi

# Extract resolved instance IDs from report.json
ALL_RESOLVED_IDS=$(python extract_resolved_ids.py "$REPORT_JSON_PATH" 2>/dev/null | tail -1 | sed 's/^"//;s/"$//')

# If existing output directory is provided, extract already completed instances
if [ -n "$EXISTING_OUTPUT_DIR" ] && [ -d "$EXISTING_OUTPUT_DIR" ]; then
    echo "Checking existing output directory: $EXISTING_OUTPUT_DIR"
    
    # Find all output.jsonl files and extract completed instances
    COMPLETED_IDS=""
    for output_file in $(find "$EXISTING_OUTPUT_DIR" -name "output.jsonl" -type f); do
        if [ -f "$output_file" ]; then
            # Extract instance_id from output.jsonl
            INSTANCE_IDS=$(python -c "
import json
import sys
try:
    with open('$output_file', 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if 'instance_id' in data:
                    print(data['instance_id'])
except:
    pass
")
            if [ -n "$INSTANCE_IDS" ]; then
                COMPLETED_IDS="$COMPLETED_IDS,$INSTANCE_IDS"
            fi
        fi
    done
    
    # Remove duplicates and format
    if [ -n "$COMPLETED_IDS" ]; then
        COMPLETED_IDS=$(echo "$COMPLETED_IDS" | tr ',' '\n' | sort -u | tr '\n' ',' | sed 's/,$//')
        echo "Completed instances: $COMPLETED_IDS"
        
        # Calculate instances that need to be run
        NEW_IDS=$(python -c "
import sys
all_ids_str = '$ALL_RESOLVED_IDS'
completed_ids_str = '$COMPLETED_IDS'
if all_ids_str and completed_ids_str:
    all_ids = set(all_ids_str.split(','))
    completed_ids = set(completed_ids_str.split(','))
    new_ids = all_ids - completed_ids
    print(','.join(sorted(new_ids)))
else:
    print(all_ids_str)
")
        
        if [ -n "$NEW_IDS" ]; then
            RESOLVED_IDS="$NEW_IDS"
            echo "New instances to run: $RESOLVED_IDS"
        else
            echo "All instances already completed, nothing to run"
            exit 0
        fi
    else
        RESOLVED_IDS="$ALL_RESOLVED_IDS"
        echo "No completed instances found, running all resolved_ids"
    fi
else
    RESOLVED_IDS="$ALL_RESOLVED_IDS"
    echo "Running all resolved_ids: $RESOLVED_IDS"
fi

# Set environment variables
export ENABLE_CWE_INJECTION=true
export CWE_TYPE="$CWE_TYPE"
# NOTE: Replace with your own API key
export ALLHANDS_API_KEY="${ALLHANDS_API_KEY:-your-api-key-here}"
export RUNTIME=remote
export SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev"

# Determine output directory
if [ "$USE_EXISTING_DIR" = "true" ] && [ -n "$EXISTING_OUTPUT_DIR" ]; then
    # Use existing directory directly
    BASE_OUTPUT_DIR="$EXISTING_OUTPUT_DIR"
    echo "Using existing directory: $BASE_OUTPUT_DIR"
else
    # Create new timestamped directory
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    EXPERIMENT_DIR="cwe_injection_${CWE_TYPE}_${TIMESTAMP}"
    BASE_OUTPUT_DIR="evaluation/evaluation_outputs/outputs/${EXPERIMENT_DIR}"
    echo "Creating new directory: $BASE_OUTPUT_DIR"
fi

# Run experiments for each round
for (( ROUND=1; ROUND<=NUM_ROUNDS; ROUND++ )); do
    if [ "$USE_EXISTING_DIR" = "true" ]; then
        # Use existing directory directly, no round suffix
        OUTPUT_DIR="$BASE_OUTPUT_DIR"
    else
        # Use new directory with round suffix
        OUTPUT_DIR="${BASE_OUTPUT_DIR}_round${ROUND}"
    fi
    
    echo "Running round $ROUND: $CWE_TYPE with $CONFIG_NAME"
    echo "Running instances: $RESOLVED_IDS"
    
    poetry run python evaluation/benchmarks/swe_bench/run_infer.py \
        --agent-cls CodeActAgent \
        --llm-config "$CONFIG_NAME" \
        --max-iterations 100 \
        --eval-num-workers 8 \
        --dataset "princeton-nlp/SWE-bench_Verified" \
        --split test \
        --eval-ids "$RESOLVED_IDS" \
        --eval-output-dir "$OUTPUT_DIR" \
        --eval-note "${CWE_TYPE}_injection_resolved_ids_round_${ROUND}"
done

echo "Completed all rounds for $CWE_TYPE"

