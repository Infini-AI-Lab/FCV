# mini-SWE-agent

We implemented the CWE-Injections directly in the source code. See details in ```src/minisweagent/agents/default.py```.

## Basic Commands

1. Install dependencies:
```bash
conda create -n minisweagent python=3.11
pip install -e .
```

2. Use our script to run CWEs

```bash
python run_cwe_simple.py --cwe_type CWE_TYPE --runs 1 --workers NUM_WORKERS --model MODEL --results-file YOUR_RESULTS_FILE
```
The results file is the output file by swebench harness that contains the ids that are resolved from round 1. 

## Ablation Study



