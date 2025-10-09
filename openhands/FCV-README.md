# OpenHands - FCV Attack Experiments

This document describes how to run **OpenHands** with CWE injection attacks for the FCV (Functionally Correct yet Vulnerable) attack experiments.

## Prerequisites

1. Complete the Pass 1 run following the instructions in [../README.md](../README.md)
2. Evaluate Pass 1 results with SWE-bench to get the `report.json` file
3. Make sure you have the OpenHands environment activated: `conda activate openhands`

## Workflow Overview

```
Pass 1 → Evaluation → CWE Injection (Pass 2) → Evaluation → LM Judge
```

## Step 1: Evaluate Pass 1 Results

After running the initial inference, evaluate the results to identify resolved instances:

```bash
# Example for GPT-5 Mini
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh \
  "/path/to/OpenHands/evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/gpt-5-mini_maxiter_100_N_v0.56.0-no-hint-run_1/output.jsonl" \
  "" \
  princeton-nlp/SWE-bench_Verified \
  test \
  local
```

This will generate a `report.json` file with resolved instance IDs.

## Step 2: Run CWE Injection Experiments

Use the `run_cwe_simple.sh` script to inject CWE vulnerabilities into the resolved instances:

### Script Usage

```bash
./run_cwe_simple.sh <REPORT_JSON> <CWE_TYPE> <LLM_CONFIG> <ROUND> <OUTPUT_DIR> <USE_REMOTE>
```

**Parameters:**
- `REPORT_JSON`: Path to the report.json from Pass 1 evaluation
- `CWE_TYPE`: One of `cwe_532`, `cwe_79`, `cwe_89`, `cwe_94`
- `LLM_CONFIG`: LLM configuration (e.g., `llm.eval_gpt5_mini`, `llm.eval_kimi`)
- `ROUND`: Round number (typically `1`)
- `OUTPUT_DIR`: Directory to save outputs
- `USE_REMOTE`: `true` to use remote runtime, `false` for local

### CWE Types

- **CWE-532** (Information Exposure): Logging sensitive information
- **CWE-79** (Cross-Site Scripting): XSS vulnerabilities
- **CWE-89** (SQL Injection): SQL injection vulnerabilities  
- **CWE-94** (Code Injection): Arbitrary code execution

## Step 3: Run CWE Injection Experiments

### General Template

```bash
cd /path/to/OpenHands && conda activate openhands

./run_cwe_simple.sh \
  <REPORT_JSON_PATH> \
  <CWE_TYPE> \
  <LLM_CONFIG> \
  1 \
  <OUTPUT_DIR> \
  true
```

**Parameters:**
- `<REPORT_JSON_PATH>`: Path to Pass 1 report.json (e.g., `evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/{MODEL_NAME}/report.json`)
- `<CWE_TYPE>`: One of `cwe_532`, `cwe_79`, `cwe_89`, `cwe_94`
- `<LLM_CONFIG>`: LLM config name (e.g., `llm.eval_gpt5_mini`, `llm.eval_kimi`, `llm.eval_qwen_480b`, `llm.eval_claude_sonnet4`)
- `<OUTPUT_DIR>`: Output directory (e.g., `evaluation/evaluation_outputs/outputs/cwe532_gpt`)

### Model Configurations

| Model | LLM Config | Model Name Pattern |
|-------|-----------|-------------------|
| GPT-5 Mini | `llm.eval_gpt5_mini` | `gpt-5-mini_maxiter_100_N_v0.56.0-no-hint-run_1` |
| Kimi-K2-Instruct | `llm.eval_kimi` | `Kimi-K2-Instruct_maxiter_100_N_v0.56.0-no-hint-run_1` |
| Qwen3-Coder-480B | `llm.eval_qwen_480b` | `Qwen3-Coder-480B-A35B-Instruct_maxiter_100_N_v0.56.0-no-hint-run_1` |
| Claude Sonnet 4 | `llm.eval_claude_sonnet4` | `claude-sonnet-4-20250514_maxiter_100_N_v0.56.0-no-hint-run_1` |

### Example: Running All CWE Types for GPT-5 Mini

```bash
cd /path/to/OpenHands && conda activate openhands

REPORT_JSON="evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/gpt-5-mini_maxiter_100_N_v0.56.0-no-hint-run_1/report.json"

for CWE_TYPE in cwe_532 cwe_79 cwe_89 cwe_94; do
  ./run_cwe_simple.sh \
    "$REPORT_JSON" \
    "$CWE_TYPE" \
    llm.eval_gpt5_mini \
    1 \
    "evaluation/evaluation_outputs/outputs/${CWE_TYPE}_gpt" \
    true
done
```

## Step 4: Evaluate CWE Injection Results

### Evaluation Template

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh \
  "<OUTPUT_JSONL_PATH>" \
  "" \
  princeton-nlp/SWE-bench_Verified \
  test \
  local
```

**Path Pattern:**
`<OUTPUT_DIR>/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/<MODEL_NAME>_maxiter_100_N_<CWE_TYPE>_injection_resolved_ids_round_1/output.jsonl`

### Example: Evaluate All CWE Types for a Model

```bash
# Define model-specific variables
MODEL_NAME="gpt-5-mini"  # or "Kimi-K2-Instruct", "Qwen3-Coder-480B-A35B-Instruct", "claude-sonnet-4-20250514"
OUTPUT_PREFIX="cwe"      # e.g., "cwe532_gpt", "cwe79_kimi", etc.

# Evaluate all CWE types
for CWE_NUM in 532 79 89 94; do
  ./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh \
    "evaluation/evaluation_outputs/outputs/cwe${CWE_NUM}_*/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/${MODEL_NAME}_maxiter_100_N_cwe_${CWE_NUM}_injection_resolved_ids_round_1/output.jsonl" \
    "" \
    princeton-nlp/SWE-bench_Verified \
    test \
    local
done
```

## Step 5: Final Evaluation with LM Judge

After collecting all results, use the LM Judge to evaluate the vulnerability injection success. See [../attack-lm-judge/README.md](../attack-lm-judge/README.md) for details.

## Troubleshooting

### Cleaning up stuck containers

If you encounter issues with stuck containers:

```bash
# Stop specific instance
docker stop $(docker ps -q --filter "name=sweb.eval.INSTANCE_ID") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=sweb.eval.INSTANCE_ID") 2>/dev/null || true

# Clean build directories
rm -rf /tmp/swe-bench/INSTANCE_ID/
```

### Runtime cleanup

```bash
# List all remote runtimes
ALLHANDS_API_KEY="your-api-key" \
  curl -H "X-API-Key: your-api-key" \
  "https://runtime.eval.all-hands.dev/list"

# Stop all remote runtimes
ALLHANDS_API_KEY="your-api-key" \
  curl -H "X-API-Key: your-api-key" \
  "https://runtime.eval.all-hands.dev/list" | \
  jq -r '.runtimes[].runtime_id' | \
  xargs -I {} curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"runtime_id": "{}"}' \
  "https://runtime.eval.all-hands.dev/stop"
```

## Output Structure

After completing the experiments, your output directory structure will look like:

```
evaluation/evaluation_outputs/outputs/
├── cwe532_gpt/
│   └── princeton-nlp__SWE-bench_Verified-test/
│       └── CodeActAgent/
│           └── gpt-5-mini_maxiter_100_N_cwe_532_injection_resolved_ids_round_1/
│               ├── output.jsonl
│               └── report.json
├── cwe79_gpt/
├── cwe89_gpt/
├── cwe94_gpt/
├── cwe532_kimi/
├── cwe79_kimi/
... (and so on for other models and CWE types)
```

## Next Steps

1. Collect all evaluation results
2. Run LM Judge evaluation (see `attack-lm-judge/README.md`)
3. Analyze attack success rates across models and CWE types

