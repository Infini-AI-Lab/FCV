import argparse
import json

def get_parser():

    parser = argparse.ArgumentParser()
    parser.add_argument('--cwe_type', type=str, default='cwe_532')
    parser.add_argument('--model', type=str, default='')
    parser.add_argument('--output_dir', type=str, default='')
    parser.add_argument('--result_file', type=str, default='')
    parser.add_argument('--num_runs', type=int, default=1)
    return parser

def run_agent(args):

    '''
    python run_simple.py --cwe_type cwe_79 --model qwen3-480b --result_file swe-bench_verified__test__qwen-480b-200.json --output_dir cwe79_qwen-480b-a35b-instruct --num_runs 4

    python run_simple.py --cwe_type cwe_79 --model qwen3-480b --result_file swe-bench_verified__test__qwen-480b-200.json --output_dir cwe79_qwen-480b-a35b-instruct --num_runs 4

    python run_simple.py --cwe_type cwe_532 --model kimi-k-instruct --result_file kimi-pass1/preds.json --output_dir cwe532_kimi-k-instruct --num_runs 4

    '''

    import subprocess
    import os

    with open(args.result_file, 'r') as f:
        resolved_ids = json.load(f)['resolved_ids']

    print(f"Running agent for {args.cwe_type} with {len(resolved_ids)} resolved instances")
    print(resolved_ids)


    regex_resolved = '|'.join(resolved_ids)
    regex_resolved = '(' + regex_resolved + ')'
    
    # Set environment variable
    env = os.environ.copy()
    env['CWE_TYPE'] = args.cwe_type
    
    # Run the command
    for i in range(1, args.num_runs + 1):
        cmd = [
            'sweagent', 'run-batch',
            '--instances.type', 'swe_bench',
            '--instances.subset', 'verified', 
            '--instances.split', 'test',
            '--instances.filter', regex_resolved,
            '--num_workers', '32',
            '--config', f'model_configs/{args.model}.yaml',
            '--output_dir', f'{args.output_dir}/run_{i}'
        ]
        result = subprocess.run(cmd, env=env, check=True)
    
    print(f"Command completed with return code: {result.returncode}")



if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    run_agent(args)