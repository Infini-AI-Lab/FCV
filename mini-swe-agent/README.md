# mini-SWE-agent - FCV Attack Experiments

We implemented the CWE-Injections directly in the source code. See details in `src/minisweagent/agents/default.py`.

## Table of Contents
- [Installation](#installation)
- [Basic CWE Injection](#basic-cwe-injection)
- [Ablation Study](#ablation-study)
  - [Append Method (Default)](#append-method-default)
  - [Instructions Method](#instructions-method)
  - [Defense Experiments](#defense-experiments)
- [Evaluation](#evaluation)

## Installation

1. Create and activate the environment:
```bash
conda create -n minisweagent python=3.11
conda activate minisweagent
cd mini-swe-agent
pip install -e .
```

## Basic CWE Injection

Use our script to run CWE injection experiments:

```bash
python run_cwe_simple.py \
  --cwe_type CWE_TYPE \
  --runs 1 \
  --workers NUM_WORKERS \
  --model MODEL \
  --results-file YOUR_RESULTS_FILE
```

**Parameters:**
- `--cwe_type`: CWE type (e.g., `cwe_532`, `cwe_79`, `cwe_89`, `cwe_94`)
- `--runs`: Number of runs (typically 1)
- `--workers`: Number of parallel workers
- `--model`: Model configuration file
- `--results-file`: Path to report.json from Pass 1 evaluation containing resolved instance IDs

## Ablation Study

The ablation study explores different injection methods and defense mechanisms. All experiments use annotation files that specify which instances to test.

### Annotation Files

- `ablation/qwen_with_annotation.json`: Annotations for Qwen3 model experiments
- `ablation/kimi_with_annotation.json`: Annotations for Kimi model experiments

### Append Method (Default)

The **append method** adds CWE injection prompts by appending them to the issue description.

#### CWE-532 (Information Exposure)

```bash
conda activate openhands && cd ~/path/to/mini-swe-agent

# Qwen3-Coder-480B
python src/batch_ablation.py run \
  --config ./swebench_qwen_big.yaml \
  --annotations ablation/qwen_with_annotation.json \
  --output-dir experiments/ablation-cwe532-Qwen3

# Kimi-K2-Instruct
python src/batch_ablation.py run \
  --config ./swebench_kimi.yaml \
  --annotations ablation/kimi_with_annotation.json \
  --output-dir experiments/ablation-cwe532-kimi
```

### Instructions Method

The **instructions method** injects CWE prompts as system instructions rather than appending to the issue.

**Template:**
```bash
python src/batch_ablation.py run \
  --config <CONFIG_YAML> \
  --annotations <ANNOTATIONS_JSON> \
  --output-dir <OUTPUT_DIR> \
  --injection-method instructions \
  --cwe-type <CWE_TYPE>
```

**Example: Run all CWE types with instructions method**
```bash
conda activate openhands && cd ~/path/to/mini-swe-agent

# For Qwen3
for CWE in cwe_79 cwe_89 cwe_94; do
  python src/batch_ablation.py run \
    --config ./swebench_qwen_big.yaml \
    --annotations ablation/qwen_with_annotation.json \
    --output-dir experiments/ablation-${CWE}-Qwen3-instructions \
    --injection-method instructions \
    --cwe-type $CWE
done

# For Kimi
for CWE in cwe_79 cwe_89 cwe_94; do
  python src/batch_ablation.py run \
    --config ./swebench_kimi.yaml \
    --annotations ablation/kimi_with_annotation.json \
    --output-dir experiments/ablation-${CWE}-kimi-instructions \
    --injection-method instructions \
    --cwe-type $CWE
done
```

### Defense Experiments

Defense experiments test the effectiveness of adding security warnings to the system prompt.

```bash
# Example: Qwen3 CWE-532 with defense
python src/batch_ablation.py run \
  --config ./swebench_qwen_big.yaml \
  --annotations ablation/qwen_with_annotation.json \
  --output-dir ablation/qwen3-cwe532-defense \
  --cwe-type cwe_532 \
  --enable-defense

# Example: Kimi CWE-532 with defense
python src/batch_ablation.py run \
  --config ./swebench_kimi.yaml \
  --annotations ablation/kimi_with_annotation.json \
  --output-dir ablation/kimi-cwe532-defense \
  --cwe-type cwe_532 \
  --enable-defense
```

## Evaluation

### Step 1: Generate Predictions File

```bash
python3 helper/generate_preds.py <EXPERIMENT_DIR> <OUTPUT_PREDS_JSON>
```

**Example:**
```bash
python3 helper/generate_preds.py experiments/ablation-cwe532-kimi experiments/ablation-cwe532-kimi/preds.json
```

### Step 2: Submit to SWE-bench (Optional)

```bash
sb-cli submit swe-bench_verified test \
  --predictions_path <PREDS_JSON> \
  --run_id <RUN_ID> \
  -o ./sb-cli-reports
```

### Step 3: Run LM Judge

```bash
python run_judge.py config/<MODEL_CONFIG>.yaml --agent mini_swe_agent
```

**Config file format** (`config/model.yaml`):
```yaml
agents:
  mini_swe_agent:
    preds_path: "/path/to/experiment/output/"
    reports_path: "/path/to/evaluation/results/"
    evaluation_file_pattern: "swe-bench_verified__test__<run_id>.json"
```

## Quick Reference

### Injection Methods
- **append** (default): Appends CWE prompt to issue description
- **instructions**: Adds CWE prompt as system instruction

### CWE Types
- `cwe_532`: Information Exposure through Log Files
- `cwe_79`: Cross-Site Scripting (XSS)
- `cwe_89`: SQL Injection
- `cwe_94`: Code Injection

### Configuration Files
- `swebench_kimi.yaml`: Kimi-K2-Instruct configuration
- `swebench_qwen_big.yaml`: Qwen3-Coder-480B configuration
- `ablation/qwen_with_annotation.json`: Qwen3 annotations
- `ablation/kimi_with_annotation.json`: Kimi annotations

## Troubleshooting

**Common Issues:**
- Missing annotation files → Check `ablation/*.json` exist
- Configuration errors → Verify YAML paths and model names
- Memory issues → Reduce number of workers

**Enable verbose logging:**
```bash
python src/batch_ablation.py run --config CONFIG --annotations ANNOTATIONS --output-dir OUTPUT --verbose
```



