sweagent run-batch \
    --config model_configs/qwen-30b-config.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --output_dir output/qwen-30b-verified-last \
    --num_workers 16 

sweagent run-batch --config config/default.yaml \
    --output_dir /path/to/your/output/directory \
    --instances.type swe_bench --instances.subset lite

sweagent run-batch \
    --config model_configs/swe-32b-config.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --output_dir output/swe-32b-verified-first \
    --num_workers 8

sweagent run-batch \
    --config model_configs/qwen-30b-config.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --instances.filter=django__django-14765 \
    --output_dir output/qwen-30b-verified-last \
    --num_workers 1  

python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_verified \
    --predictions_path output/qwen-30b-verified-first/preds.json  \
    --max_workers 8 \
    --run_id Qwen-30b-verified-first

sweagent run-batch --instances.type swe_bench --instances.subset verified --instances.split test --instances.slice :200 --num_workers 8 --config model_configs/kimi-k2-instruct.yaml --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/kimi-pass1

sweagent run-batch --instances.type swe_bench --instances.subset verified --instances.split test --instances.slice :200 --num_workers 8 --config model_configs/kimi-k2-instruct.yaml --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/kimi-pass1


sweagent run-batch --instances.type swe_bench --instances.subset verified --instances.split test --instances.slice :200 --num_workers 8 --config model_configs/claude-sonnet-4.yaml --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/claude-pass1


CWE_TYPE=cwe_532 sweagent run-batch --instances.type swe_bench --instances.subset verified --instances.split test --instances.filter astropy__astropy-12907 --num_workers 1 --config model_configs/kimi-k2-instruct.yaml --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/cwe532_qwen-480b-a35b-instruct


sweagent run-batch \
    --config model_configs/gpt-5-mini.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --instances.slice :200 \
    --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/gpt-5-mini-pass1 \
    --num_workers 1


sweagent run-batch \
    --config model_configs/qwen.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/pass1/qwen-pass1 \
    --num_workers 1



sweagent run-batch \
    --config model_configs/kimi-official.yaml \
    --instances.type swe_bench \
    --instances.subset verified \
    --instances.split test  \
    --output_dir /home/haizhonz/code-agent-safety-results/swe-agent/pass1/kimi-pass1 \
    --num_workers 16