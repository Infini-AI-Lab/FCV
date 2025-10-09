#!/usr/bin/env python3
"""
Rule-based annotation script for finding injection points in trajectory files.

This script processes the passed_instances_for_annotation.json file and fills in
missing injection_step annotations using a simple rule: find the first sed -i
command (excluding the initial user prompt template).
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_trajectory(traj_path: Path) -> Dict[str, Any]:
    """Load trajectory from JSON file."""
    with open(traj_path, 'r') as f:
        return json.load(f)

def find_first_sed_injection_point(traj: Dict[str, Any]) -> Optional[int]:
    """
    Find the first sed -i command in assistant responses, excluding the initial prompt template.
    
    Returns the message index where the injection should happen (before the sed command).
    """
    messages = traj.get('messages', [])
    
    # Skip the first few messages which typically contain the initial prompt template
    start_idx = 0
    for i, msg in enumerate(messages):
        if msg.get('role') == 'user' and 'Consider the following PR description' in msg.get('content', ''):
            start_idx = i + 1
            break
    
    # Look for first sed -i command in assistant responses after the initial template
    for i in range(start_idx, len(messages)):
        msg = messages[i]
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            # Look for sed -i patterns in bash code blocks
            if re.search(r'```bash.*?sed\s+-i.*?```', content, re.DOTALL):
                return i
    
    return None

def extract_sed_command_context(traj: Dict[str, Any], injection_idx: int) -> str:
    """Extract the context around the sed command for notes."""
    messages = traj.get('messages', [])
    if injection_idx >= len(messages):
        return ""
    
    content = messages[injection_idx].get('content', '')
    
    # Extract THOUGHT section and sed command
    thought_match = re.search(r'THOUGHT:(.*?)```bash', content, re.DOTALL)
    sed_match = re.search(r'```bash(.*?sed.*?)```', content, re.DOTALL)
    
    context_parts = []
    if thought_match:
        thought_text = thought_match.group(1).strip()
        if thought_text:
            context_parts.append(f"THOUGHT: {thought_text}")
    
    if sed_match:
        sed_text = sed_match.group(1).strip()
        context_parts.append(f"```bash\n{sed_text}\n```")
    
    return "\n\n".join(context_parts)

def annotate_instance(instance: Dict[str, Any], trajectory_dir: Path) -> Dict[str, Any]:
    """Annotate a single instance using rule-based approach."""
    instance_copy = instance.copy()
    
    # Skip if already annotated
    if instance.get('injection_step', -1) != -1:
        instance_copy['annotation_method'] = 'human'
        return instance_copy
    
    # Try rule-based annotation
    traj_path = trajectory_dir / instance['instance_id'] / f"{instance['instance_id']}.traj.json"
    
    if not traj_path.exists():
        print(f"Warning: Trajectory file not found: {traj_path}")
        instance_copy['annotation_method'] = 'missing_file'
        return instance_copy
    
    try:
        traj = load_trajectory(traj_path)
        injection_point = find_first_sed_injection_point(traj)
        
        if injection_point is not None:
            instance_copy['injection_step'] = injection_point
            instance_copy['notes'] = extract_sed_command_context(traj, injection_point)
            instance_copy['annotation_method'] = 'rule_based'
            print(f"✅ {instance['instance_id']}: Found injection point at step {injection_point}")
        else:
            instance_copy['annotation_method'] = 'no_sed_found'
            print(f"❌ {instance['instance_id']}: No sed command found")
            
    except Exception as e:
        print(f"⚠️  {instance['instance_id']}: Error processing trajectory: {e}")
        instance_copy['annotation_method'] = 'error'
        
    return instance_copy

def create_annotated_json(input_path: Path, output_path: Path, trajectory_dir: Path) -> None:
    """Create new annotated JSON file with rule-based annotations."""
    
    # Load original annotations
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Process each instance
    annotated_instances = []
    stats = {
        'human': 0,
        'rule_based': 0,
        'no_sed_found': 0,
        'missing_file': 0,
        'error': 0
    }
    
    for instance in data['instances']:
        annotated_instance = annotate_instance(instance, trajectory_dir)
        annotated_instances.append(annotated_instance)
        
        method = annotated_instance.get('annotation_method', 'unknown')
        stats[method] = stats.get(method, 0) + 1
    
    # Update metadata
    new_data = data.copy()
    new_data['instances'] = annotated_instances
    new_data['metadata']['rule_annotation_stats'] = stats
    new_data['metadata']['annotation_methods'] = {
        'human': 'Manually annotated by human',
        'rule_based': 'Automatically found first sed -i command',
        'no_sed_found': 'No sed command found in trajectory',
        'missing_file': 'Trajectory file not found',
        'error': 'Error occurred during processing'
    }
    
    # Save annotated file
    with open(output_path, 'w') as f:
        json.dump(new_data, f, indent=2)
    
    # Print statistics
    print(f"\n📊 Annotation Statistics:")
    for method, count in stats.items():
        print(f"  {method}: {count}")
    
    total_annotated = stats['human'] + stats['rule_based']
    total_instances = len(annotated_instances)
    print(f"\nTotal annotated: {total_annotated}/{total_instances} ({total_annotated/total_instances*100:.1f}%)")
    print(f"Output saved to: {output_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Rule-based annotation for finding injection points in trajectory files"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default="ablation/passed_instances_for_annotation.json",
        help="Input annotation JSON file (default: ablation/passed_instances_for_annotation.json)"
    )
    parser.add_argument(
        "--output", 
        type=Path,
        default="ablation/passed_instances_with_rule_annotation.json",
        help="Output annotation JSON file (default: ablation/passed_instances_with_rule_annotation.json)"
    )
    parser.add_argument(
        "--trajectory-dir",
        type=Path,
        default="experiments/qwen-big-pass1",
        help="Directory containing trajectory files (default: experiments/qwen-big-pass1)"
    )
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    trajectory_dir = args.trajectory_dir
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    if not trajectory_dir.exists():
        print(f"Error: Trajectory directory not found: {trajectory_dir}")
        return
    
    print(f"Processing annotations from: {input_path}")
    print(f"Looking for trajectories in: {trajectory_dir}")
    print(f"Will save results to: {output_path}")
    print("-" * 80)
    
    create_annotated_json(input_path, output_path, trajectory_dir)

if __name__ == "__main__":
    main()
