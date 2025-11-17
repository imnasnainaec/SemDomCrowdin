#!/usr/bin/env python3
"""
Count trans-units within XLF file _Poss groups by target state.

Usage:
    python count_in_xlf.py <input_file>
"""

import argparse
import xml.etree.ElementTree as ET
import sys
import os
from collections import defaultdict


def extract_text(element):
    """Extract text content from an XML element."""
    if element is None:
        return ""
    return ''.join(element.itertext()).strip()


def count_in_xlf(input_file):
    """
    Count _Name and _Desc_0 trans-units within _Poss groups by target state.
    Results are broken down by each immediate child of a _Poss group.
    
    Args:
        input_file: Path to the input XLF file from crowdin-downloads/
    """
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    # Define namespace (if present)
    namespaces = {'xliff': 'http://www.w3.org/2001/xliff'}
    # Check if namespace is used
    if root.tag.startswith('{'):
        ns_uri = root.tag[1:root.tag.index('}')]
        namespaces['xliff'] = ns_uri
        use_ns = True
    else:
        use_ns = False
    
    # Find all group elements
    if use_ns:
        all_groups = root.findall('.//xliff:group', namespaces)
    else:
        all_groups = root.findall('.//group')
    
    # Find the _Poss group
    poss_group = None
    for group in all_groups:
        if '_Poss' in group.get('id', ''):
            poss_group = group
            break
    
    if poss_group is None:
        print("Error: No _Poss group found in file", file=sys.stderr)
        sys.exit(1)
    
    # Get immediate children of _Poss group
    if use_ns:
        poss_children = poss_group.findall('xliff:group', namespaces)
    else:
        poss_children = poss_group.findall('group')
    
    # Structure: {poss_child_id: {'name': {state: count}, 'desc': {state: count}}}
    poss_data = defaultdict(lambda: {'name': defaultdict(int), 'desc': defaultdict(int)})
    
    # Process each immediate child of the _Poss group
    for child_group in poss_children:
        child_id = child_group.get('id', '')
        
        # Find all trans-units in this child group
        if use_ns:
            trans_units = child_group.findall('.//xliff:trans-unit', namespaces)
        else:
            trans_units = child_group.findall('.//trans-unit')
        
        for trans_unit in trans_units:
            unit_id = trans_unit.get('id', '')
            
            # Get target element and its state
            if use_ns:
                target_elem = trans_unit.find('xliff:target', namespaces)
            else:
                target_elem = trans_unit.find('target')
            
            target_state = target_elem.get('state', '(no state)') if target_elem is not None else '(no target)'
            
            # Count _Name trans-units
            if unit_id.endswith('_Name'):
                poss_data[child_id]['name'][target_state] += 1
            
            # Count _Desc_0 trans-units
            elif unit_id.endswith('_Desc_0'):
                poss_data[child_id]['desc'][target_state] += 1
    
    # Display results
    print(f"Input file: {input_file}")
    print(f"Found {len(poss_data)} _Poss child group(s)\n")
    
    # Sort poss_child_ids naturally
    def natural_sort_key(s):
        """Sort key that handles numbers naturally"""
        import re
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', s)]
    
    sorted_poss_ids = sorted(poss_data.keys(), key=natural_sort_key)
    
    for poss_id in sorted_poss_ids:
        data = poss_data[poss_id]
        name_counts = data['name']
        desc_counts = data['desc']
        
        print("=" * 80)
        print(f"{poss_id}")
        print("=" * 80)
        
        # Display _Name counts
        if name_counts:
            total_name = sum(name_counts.values())
            print(f"_Name trans-units ({total_name} total):")
            print("-" * 80)
            for state in sorted(name_counts.keys()):
                count = name_counts[state]
                percentage = (count / total_name * 100) if total_name > 0 else 0
                print(f"  {state:30s}: {count:4d} ({percentage:5.1f}%)")
        
        # Display _Desc_0 counts
        if desc_counts:
            total_desc = sum(desc_counts.values())
            if name_counts:
                print()  # Add spacing between _Name and _Desc_0
            print(f"_Desc_0 trans-units ({total_desc} total):")
            print("-" * 80)
            for state in sorted(desc_counts.keys()):
                count = desc_counts[state]
                percentage = (count / total_desc * 100) if total_desc > 0 else 0
                print(f"  {state:30s}: {count:4d} ({percentage:5.1f}%)")
        
        if not name_counts and not desc_counts:
            print("  No _Name or _Desc_0 trans-units found")
        
        print()  # Blank line between groups
    
    # Calculate and display totals across all children
    print("=" * 80)
    print("TOTALS ACROSS ALL CHILDREN")
    print("=" * 80)
    
    total_name_counts = defaultdict(int)
    total_desc_counts = defaultdict(int)
    
    for data in poss_data.values():
        for state, count in data['name'].items():
            total_name_counts[state] += count
        for state, count in data['desc'].items():
            total_desc_counts[state] += count
    
    # Display _Name totals
    if total_name_counts:
        grand_total_name = sum(total_name_counts.values())
        print(f"_Name trans-units ({grand_total_name} total):")
        print("-" * 80)
        for state in sorted(total_name_counts.keys()):
            count = total_name_counts[state]
            percentage = (count / grand_total_name * 100) if grand_total_name > 0 else 0
            print(f"  {state:30s}: {count:4d} ({percentage:5.1f}%)")
    
    # Display _Desc_0 totals
    if total_desc_counts:
        grand_total_desc = sum(total_desc_counts.values())
        if total_name_counts:
            print()  # Add spacing between _Name and _Desc_0
        print(f"_Desc_0 trans-units ({grand_total_desc} total):")
        print("-" * 80)
        for state in sorted(total_desc_counts.keys()):
            count = total_desc_counts[state]
            percentage = (count / grand_total_desc * 100) if grand_total_desc > 0 else 0
            print(f"  {state:30s}: {count:4d} ({percentage:5.1f}%)")
    
    if total_name_counts or total_desc_counts:
        print()
        print("=" * 80)
        grand_total_all = sum(total_name_counts.values()) + sum(total_desc_counts.values())
        print(f"Grand Total: {grand_total_all} trans-units across all children")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Count _Name and _Desc_0 trans-units within _Poss groups by target state, broken down by each immediate child.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python count_in_xlf.py crowdin-downloads/SemanticDomains.pt-BR.xlf
  
Output is organized by each immediate _Poss child (e.g., 1_Poss_1, 1_Poss_2, etc.)
        """
    )
    
    parser.add_argument('input_file', help='Input XLF file path from crowdin-downloads/')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Count trans-units
    count_in_xlf(args.input_file)


if __name__ == '__main__':
    main()
