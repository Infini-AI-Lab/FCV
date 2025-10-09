# SWE-agent

We implemented the CWE-Injections directly in the source code. See details in ```sweagent/run/batch_instances.py```, in the method ```get_cwe_injection(cls)```. 

## Basic Commands

1. Install dependencies:
```bash
conda create -n sweagent python=3.11
pip install -e .
```

2. Use our script to run CWEs

```bash
python run_simple.py --cwe_type $CWE_TYPE --model $MODEL --result_file $RESULT_FILE --output_dir $OUTPUT_DIR --num_runs $NUM_RUNS 
```
The results file is the output file by swebench harness that contains the ids that are resolved from round 1. 

3. Evaluation

For SWE-agent, you can either use the swebench evaluation harness yourself, or you can specify in the yaml file. For example, you can specify:
```yaml
instances:
  type: swe_bench
  subset: verified
  split: test
  evaluate: true ## This will run swebench harness after instance is run
  deployment:
    type: docker
    docker_args:
      - '--memory=10g'
```




