#!/usr/bin/env python3
"""
Extract resolved_ids from report.json and format them for use with --eval-ids
"""
import json
import sys

def extract_resolved_ids(report_file):
    """Extract resolved_ids from report.json file"""
    try:
        with open(report_file, 'r') as f:
            data = json.load(f)
        
        resolved_ids = data.get('resolved_ids', [])
        
        if not resolved_ids:
            print("No resolved_ids found in the report file", file=sys.stderr)
            return None
            
        # Format as comma-separated string for --eval-ids
        ids_string = ','.join(resolved_ids)
        
        print(f"Found {len(resolved_ids)} resolved instances:")
        for rid in resolved_ids:
            print(f"  - {rid}")
        
        print("\nFormatted for --eval-ids:")
        print(f'"{ids_string}"')
        
        return ids_string
        
    except FileNotFoundError:
        print(f"Report file not found: {report_file}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_resolved_ids.py <report.json>")
        sys.exit(1)
    
    report_file = sys.argv[1]
    extract_resolved_ids(report_file)
