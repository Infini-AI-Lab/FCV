#!/usr/bin/env python3
"""
Extract instances that passed functional tests for ablation study.

This script analyzes SWE-bench evaluation results and trajectory data to identify 
instances that passed functional tests, then prepares them for manual annotation 
of toxic instruction injection points.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class InstanceInfo:
    """Information about a SWE-bench instance for ablation study."""
    instance_id: str
    trajectory_path: str
    total_steps: int
    injection_step: int = -1  # -1 means not annotated yet
    notes: str = ""


def load_evaluation_results(report_path: Path) -> Dict[str, Any]:
    """Load SWE-bench evaluation results."""
    with open(report_path, 'r') as f:
        return json.load(f)


def find_trajectory_file(trajectory_dir: Path, instance_id: str) -> Path | None:
    """Find trajectory file for a specific instance."""
    instance_dir = trajectory_dir / instance_id
    if not instance_dir.exists():
        return None
    
    # Look for .traj.json file
    traj_files = list(instance_dir.glob("*.traj.json"))
    if traj_files:
        return traj_files[0]
    
    # Fallback to trajectory.json
    traj_file = instance_dir / "trajectory.json"
    if traj_file.exists():
        return traj_file
    
    return None


def count_trajectory_steps(traj_path: Path) -> int:
    """Count the number of steps in a trajectory."""
    try:
        with open(traj_path, 'r') as f:
            traj_data = json.load(f)
        
        # Handle different trajectory formats
        if isinstance(traj_data, dict):
            # Check for 'messages' array format (mini-swe-agent format)
            if 'messages' in traj_data:
                messages = traj_data['messages']
                if isinstance(messages, list):
                    # Filter out system messages and count assistant/user pairs
                    non_system_messages = [msg for msg in messages if msg.get('role') != 'system']
                    return len(non_system_messages)
                return 0
            # Check for traditional trajectory formats
            elif 'trajectory' in traj_data:
                return len(traj_data['trajectory'])
            elif 'history' in traj_data:
                return len(traj_data['history'])
            else:
                # Count top-level keys that might be steps
                step_keys = [k for k in traj_data.keys() if k.isdigit()]
                return len(step_keys)
        elif isinstance(traj_data, list):
            return len(traj_data)
        else:
            return 0
    except Exception as e:
        print(f"Warning: Failed to count steps in {traj_path}: {e}")
        return 0


def extract_passed_instances(
    report_path: Path, 
    trajectory_dir: Path, 
    output_path: Path
) -> None:
    """Extract instances that passed functional tests."""
    
    # Load evaluation results
    eval_results = load_evaluation_results(report_path)
    
    # Get resolved (passed) instance IDs
    resolved_ids = eval_results.get('resolved_ids', [])
    
    print(f"Found {len(resolved_ids)} resolved instances")
    
    # Process each resolved instance
    instances_info = []
    
    for instance_id in resolved_ids:
        # Find trajectory file
        traj_path = find_trajectory_file(trajectory_dir, instance_id)
        
        if traj_path is None:
            print(f"Warning: No trajectory found for {instance_id}")
            continue
        
        # Count trajectory steps
        step_count = count_trajectory_steps(traj_path)
        
        if step_count == 0:
            print(f"Warning: No steps found in trajectory for {instance_id}")
            continue
        
        # Create instance info
        instance_info = InstanceInfo(
            instance_id=instance_id,
            trajectory_path=str(traj_path),
            total_steps=step_count,
            injection_step=-1,  # To be annotated manually
            notes=""
        )
        
        instances_info.append(instance_info)
    
    print(f"Successfully processed {len(instances_info)} instances")
    
    # Convert to JSON-serializable format
    output_data = {
        "metadata": {
            "total_instances": len(instances_info),
            "report_path": str(report_path),
            "trajectory_dir": str(trajectory_dir),
            "annotation_instructions": {
                "injection_step": "Set to the step number where toxic instruction should be injected (before patch generation). Use -1 if not annotated.",
                "notes": "Additional notes about the instance or injection point"
            }
        },
        "instances": [
            {
                "instance_id": inst.instance_id,
                "trajectory_path": inst.trajectory_path,
                "total_steps": inst.total_steps,
                "injection_step": inst.injection_step,
                "notes": inst.notes
            }
            for inst in instances_info
        ]
    }
    
    # Save to output file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved instance information to {output_path}")
    print(f"Ready for manual annotation of injection points.")


def main():
    parser = argparse.ArgumentParser(
        description="Extract passed instances for ablation study"
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        required=True,
        help="Path to SWE-bench evaluation report JSON file"
    )
    parser.add_argument(
        "--trajectory-dir", 
        type=Path,
        required=True,
        help="Path to directory containing trajectory files"
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path to output JSON file for annotation"
    )
    
    args = parser.parse_args()
    
    # Validate input paths
    if not args.report_path.exists():
        raise FileNotFoundError(f"Report file not found: {args.report_path}")
    
    if not args.trajectory_dir.exists():
        raise FileNotFoundError(f"Trajectory directory not found: {args.trajectory_dir}")
    
    # Create output directory if needed
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract instances
    extract_passed_instances(args.report_path, args.trajectory_dir, args.output_path)


if __name__ == "__main__":
    main()
