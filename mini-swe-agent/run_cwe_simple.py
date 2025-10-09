#!/usr/bin/env python3
"""
Simple CWE Pipeline - run agent or LM-only tests and evaluation
"""

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
from datasets import Dataset, DatasetDict

# CWE config loader removed - using hardcoded templates in default.py

CONFIG_MAP = {
    "Qwen/Qwen3-Coder-480B-A35B-Instruct": "model_configs/qwen.yaml",
    "claude-sonnet-4-20250514": "model_configs/claude.yaml",
    "gpt-5-mini": "model_configs/gpt.yaml",
    "moonshotai/Kimi-K2-Instruct": "model_configs/kimi.yaml",
}

OUTPUT_PATH = os.getenv("OUTPUT_PATH", "results")


def load_resolved_ids_from_results_file(results_file_path):
    """Load resolved_ids from a results JSON file."""
    try:
        with open(results_file_path, 'r') as f:
            data = json.load(f)
            resolved_ids = data.get('resolved_ids', [])
            print(f"📄 Loaded {len(resolved_ids)} resolved instances from {results_file_path}")
            return resolved_ids
    except Exception as e:
        print(f"❌ Error loading results file {results_file_path}: {e}")
        return []

def run_agent_tests(cwe_type, num_runs, workers=16, instances=None, model="openai/Qwen3-Coder-30B-A3B-Instruct", results_file=None):
    """Run mini-swe-agent tests with CWE injection."""
    print(f"Running agent {cwe_type} tests with {num_runs} runs...")
    
    # Validate CWE type
    valid_cwe_types = ['cwe_538', 'cwe_79', 'cwe_89', 'cwe_94']
    if cwe_type not in valid_cwe_types:
        print(f"Error: Invalid CWE type {cwe_type}. Valid types: {valid_cwe_types}")
        return None
    
    # Load instances from results file if provided
    if results_file and not instances:
        resolved_ids = load_resolved_ids_from_results_file(results_file)
        if resolved_ids:
            instances = "|".join(resolved_ids)
            instances = '(' + instances + ')'
            print(f"🎯 Using {len(resolved_ids)} resolved instances from results file")
        else:
            print("⚠️ No resolved instances found in results file, running on all instances")
    
    # Set environment variables for CWE injection
    os.environ['CWE_TYPE'] = cwe_type
    print(f"Set environment variable: CWE_TYPE={cwe_type}")
    
    # Set Anthropic API key if using Claude model
    if "claude" in model.lower():
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            os.environ['ANTHROPIC_API_KEYS'] = anthropic_key
            print(f"Set environment variable: ANTHROPIC_API_KEYS={anthropic_key[:20]}...")
    
    # Create output directory with agent prefix and model name
    model_name = model.replace("openai/", "").replace("/", "_").replace("-", "_")
    output_dir = f"{OUTPUT_PATH}/agent_{cwe_type}_{model_name}_results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created agent results directory: {output_dir}")
    
    # Run tests
    for i in range(1, num_runs + 1):
        print(f"Agent Run {i}/{num_runs}")
    
        cmd = [
            "mini-extra", "swebench",
            "--config", CONFIG_MAP[model],
            "--subset", "verified",
            "--split", "test",
            "--workers", str(workers),
            "-o", f"{output_dir}/run_{i}"
        ]
        if instances is not None:
            cmd.extend(["--filter", instances])
        
        print("Running command: ", " ".join(cmd))
        result = subprocess.run(cmd, env=os.environ.copy())
        if result.returncode != 0:
            print(f"Agent Run {i} failed")
        else:
            print(f"Agent Run {i} completed")
    
    return output_dir

def main():
    parser = argparse.ArgumentParser(description="Simple CWE Pipeline - Agent tests")
    parser.add_argument("--cwe_type", default="cwe_538", help="CWE type")
    parser.add_argument("--runs", type=int, default=16, help="Number of runs")
    parser.add_argument("--workers", type=int, default=16, help="Number of workers")
    parser.add_argument("--instances", help="Instance filter (optional, if not specified uses full dataset)")
    parser.add_argument("--model", default="Qwen3-Coder-30B-A3B-Instruct", help="Model name (e.g., openai/model)")
    parser.add_argument("--results-file", help="Results file with resolved instance IDs to filter instances")
    args = parser.parse_args()
    
    
    results_dir = run_agent_tests(args.cwe_type, args.runs, args.workers, args.instances, args.model, args.results_file)

    print(f"Results directory: {results_dir}")


if __name__ == "__main__":
    main()
