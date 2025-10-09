#!/usr/bin/env python3
"""
LM Vulnerability Judge - Main executable script
Analyzes code patches for security vulnerabilities using LLM judges.
"""

import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lm_vulnerability_judge.core.judge import VulnerabilityJudge


def main():
    """Main entry point for the vulnerability judge system."""
    
    parser = argparse.ArgumentParser(
        description="Analyze code patches for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use Qwen judge
  python run_judge.py config/qwen-480.yaml --agent mini_swe_agent --limit 10
  
  # Use Kimi K2 judge  
  python run_judge.py config/kimi-k2.yaml --agent mini_swe_agent --limit 5
  
  # Use multi-judge configuration
  python run_judge.py config/multi-judge.yaml --agent swe_agent
        """
    )
    
    parser.add_argument(
        'config_path', 
        help='Path to the configuration YAML file'
    )
    
    parser.add_argument(
        '--agent', 
        default='mini_swe_agent',
        choices=['mini_swe_agent', 'swe_agent', 'openhands'],
        help='Agent name to analyze (default: mini_swe_agent)'
    )
    
    parser.add_argument(
        '--limit', 
        type=int,
        help='Limit the number of patches to analyze (for testing)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--preds-path',
        help='Override preds_path from config file'
    )
    
    parser.add_argument(
        '--reports-path', 
        help='Override reports_path from config file'
    )

    parser.add_argument(
        '--agent-path',
        help='Override agent_path from config file'
    )

    parser.add_argument(
        '--cwe-type',
        help='Override cwe_type from config file'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=30,
        help='Number of parallel workers for API calls (default: 30)'
    )
    
    # Failed pairs retry functionality
    parser.add_argument(
        '--skip-failed',
        help='Path to vulnerability report to extract failed pairs from for skipping'
    )
    
    parser.add_argument(
        '--failed-pairs',
        help='Path to JSON file containing failed pairs to skip'
    )
    
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Run without skipping any pairs (overrides skip-failed and failed-pairs)'
    )
    
    parser.add_argument(
        '--only-failed',
        action='store_true',
        help='Only retry previously failed API calls (requires --skip-failed or --failed-pairs)'
    )
    
    args = parser.parse_args()
    
    if not Path(args.config_path).exists():
        print(f"Error: Config file not found: {args.config_path}")
        sys.exit(1)
    
    try:
        # Initialize the judge system
        print("Initializing LM Vulnerability Judge...")
        judge = VulnerabilityJudge(args.config_path, args)
        
        # Collect failed pairs if requested
        failed_pairs = None
        if not args.no_skip:
            if args.failed_pairs:
                # Load failed pairs from JSON file
                from utils.retry_utils import load_failed_pairs
                failed_pairs = load_failed_pairs(args.failed_pairs)
                print(f"📁 Loaded {len(failed_pairs)} failed pairs from {args.failed_pairs}")
            elif args.skip_failed:
                # Collect failed pairs from vulnerability report
                from utils.retry_utils import collect_failed_pairs_from_report
                failed_pairs = collect_failed_pairs_from_report(args.skip_failed)
                print(f"📊 Collected {len(failed_pairs)} failed pairs from {args.skip_failed}")
                
                # If only-failed is used, also collect missing CWEs
                if args.only_failed:
                    from utils.missing_cwe_utils import detect_missing_cwes_as_failed_pairs
                    from lm_vulnerability_judge.judges.base import BaseJudge
                    
                    # Get configured CWE range from the judge's configuration
                    all_cwe_ids = BaseJudge.get_all_cwe_ids()
                    
                    # Get CWE range from config (dynamically from loaded config)
                    cwe_start = judge.config.get('cwe_start_index', 0)
                    cwe_end = judge.config.get('cwe_end_index', 100)
                    
                    # Ensure valid range
                    if cwe_end > len(all_cwe_ids):
                        cwe_end = len(all_cwe_ids)
                    if cwe_start < 0:
                        cwe_start = 0
                    
                    configured_cwes = all_cwe_ids[cwe_start:cwe_end]
                    print(f"📊 Using CWE range: {cwe_start}-{cwe_end} ({len(configured_cwes)} CWEs)")
                    
                    missing_pairs = detect_missing_cwes_as_failed_pairs(args.skip_failed, configured_cwes)
                    print(f"📊 Collected {len(missing_pairs)} missing CWE pairs")
                    
                    # Combine failed pairs and missing pairs
                    failed_pairs = failed_pairs.union(missing_pairs)
                    print(f"📊 Total pairs to retry: {len(failed_pairs)} (failed + missing)")
            
            if failed_pairs:
                # Show summary of failed pairs
                by_cwe = {}
                for instance_id, cwe_id in failed_pairs:
                    by_cwe[cwe_id] = by_cwe.get(cwe_id, 0) + 1
                
                if args.only_failed:
                    print(f"🔄 Will retry failed CWEs: {dict(by_cwe)}")
                else:
                    print(f"📋 Will skip failed CWEs: {dict(by_cwe)}")
        
        # Run analysis using the new unified method
        if args.only_failed:
            print(f"Retrying failed API calls for {args.agent}...")
        else:
            print(f"Analyzing {args.agent} outputs...")
        
        responses = judge.analyze_agent_outputs(
            agent_name=args.agent, 
            limit=args.limit,
            failed_pairs=failed_pairs,
            only_failed=args.only_failed
        )
        
        if not responses:
            print("No analysis responses generated. Exiting.")
            sys.exit(0)
        
        # Generate reports
        print("Generating reports...")
        # Get agent configuration for report generation
        agent_config = judge.config['agents'][args.agent].copy()
        agent_config['name'] = args.agent
        reports = judge.generate_reports(responses, agent_config=agent_config)
        
        print("\\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        
        for report_type, path in reports.items():
            print(f"{report_type.upper()} report: {path}")
        
        # Print summary
        total_patches = len(responses)
        vulnerable_patches = sum(1 for r in responses if r.verdict == 'vulnerable')
        
        print(f"\\nSummary for {args.agent}:")
        print(f"Total resolved patches analyzed: {total_patches}")
        print(f"Patches with vulnerabilities: {vulnerable_patches}")
        if total_patches > 0:
            print(f"Vulnerability rate: {vulnerable_patches/total_patches:.1%}")
        
        # Vulnerability breakdown
        # Count each CWE ID only once per response, even if multiple vulnerabilities of same type exist
        vuln_counts = {}
        for response in responses:
            found_cwe_ids = set()  # Use set to avoid counting same CWE ID multiple times per response
            for vuln in response.vulnerabilities:
                if vuln.found:
                    found_cwe_ids.add(vuln.cwe_id)
            
            # Count each unique CWE ID found in this response
            for cwe_id in found_cwe_ids:
                vuln_counts[cwe_id] = vuln_counts.get(cwe_id, 0) + 1
        
        if vuln_counts:
            print("\\nVulnerability breakdown:")
            for cwe_id, count in sorted(vuln_counts.items()):
                print(f"  {cwe_id}: {count} patches")
        
    except KeyboardInterrupt:
        print("\\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
