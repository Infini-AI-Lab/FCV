#!/bin/bash
set -e

cwe_types=("89" "94" "532" "79")
run_nums=(1)

models=( "moonshotai_Kimi_K2_Instruct" "claude_sonnet_4_20250514" "gpt_5_mini" "Qwen_Qwen3_Coder_480B_A35B_Instruct")

# Function to run evaluation for a specific run_num and cwe
run_evaluation() {
    local preds_path=$1
    local reports_path=$2
    local cwe_type=$3
    local agent_name=$4
    
    python run_judge.py config/qwen.yaml --agent ${agent_name//-/_} --preds-path ${preds_path} --reports-path ${reports_path} --cwe-type CWE-${cwe_type} --workers 30
    
    echo "Completed evaluation for run ${preds_path} and CWE ${cwe_type}"
}


## EXAMPLE for SWE-agent or mini-SWE-agent
run_evaluation agent_cwe_89_Qwen_Qwen3_Coder_480B_A35B_Instruct_results/run_1/preds.json mini-swe-agent-results/evaluation/500/cwe/Qwen__Qwen3-Coder-480B-A35B-Instruct.minisweagent-cwe89-all.json 89 mini-swe-agent

## EXAMPLE for OpenHands
# For OpenHands, use the --agent-path flag to point to the directory containing output.jsonl and report.json
python run_judge.py config/qwen.yaml --agent openhands --agent-path /path/to/openhands/experiment/CodeActAgent/model_name_maxiter_100 --cwe-type CWE-532 --workers 30 
