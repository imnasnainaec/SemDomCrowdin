#!/usr/bin/env python3
"""
Compare two XLF files and identify translations that have changed.

Usage:
    python compare_xlf.py -n <file1> <file2> [output_file]     # Compare _Name entries (content only)
    python compare_xlf.py -n -s <file1> <file2> [output_file]  # Compare _Name entries (with state)
    python compare_xlf.py -d <file1> <file2> [output_file]     # Compare _Desc_0 entries (content only)
    python compare_xlf.py -d -s <file1> <file2> [output_file]  # Compare _Desc_0 entries (with state)
"""

import argparse
import xml.etree.ElementTree as ET
import sys
import os


def extract_text(element):
    """Extract text content from an XML element."""
    if element is None:
        return ""
    return ''.join(element.itertext()).strip()


def parse_xlf_file(input_file):
    """
    Parse XLF file and extract relevant data for each semantic domain.
    
    Returns a tuple: (dictionary with group IDs as keys, list of group IDs in order)
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
    
    # Filter to find semantic domain groups (those with guid child)
    target_groups = []
    for group in all_groups:
        has_guid = False
        for child in group:
            if 'guid' in child.tag:
                has_guid = True
                break
        if has_guid:
            target_groups.append(group)
    
    # Extract data from each group
    data = {}
    group_order = []  # Preserve the order of groups
    
    for group in target_groups:
        group_id = group.get('id', '')
        group_order.append(group_id)  # Track order
        
        # Get all child elements
        children = list(group)
        
        # Find trans-units (excluding _SubPos groups)
        trans_units = []
        for child in children:
            child_id = child.get('id', '')
            # Skip _SubPos groups
            if child.tag.endswith('group') and '_SubPos' in child_id:
                continue
            
            # If it's a trans-unit, add it directly
            if child.tag.endswith('trans-unit'):
                trans_units.append(child)
            # If it's another group (like _Desc or _Qs), search within it
            elif child.tag.endswith('group'):
                if use_ns:
                    trans_units.extend(child.findall('.//xliff:trans-unit', namespaces))
                else:
                    trans_units.extend(child.findall('.//trans-unit'))
        
        # Extract relevant data
        group_data = {
            'abbr': '',
            'name_source': '',
            'name_target': '',
            'name_target_state': '',
            'desc_source': '',
            'desc_target': '',
            'desc_target_state': ''
        }
        
        for trans_unit in trans_units:
            unit_id = trans_unit.get('id', '')
            
            if use_ns:
                source_elem = trans_unit.find('xliff:source', namespaces)
                target_elem = trans_unit.find('xliff:target', namespaces)
            else:
                source_elem = trans_unit.find('source')
                target_elem = trans_unit.find('target')
            
            # Extract _Abbr
            if unit_id.endswith('_Abbr'):
                group_data['abbr'] = extract_text(source_elem)
            
            # Extract _Name
            elif unit_id.endswith('_Name'):
                group_data['name_source'] = extract_text(source_elem)
                target_state = target_elem.get('state', '') if target_elem is not None else ''
                group_data['name_target_state'] = target_state
                # Use empty string if state is "needs-translation"
                if target_state == 'needs-translation':
                    group_data['name_target'] = ''
                else:
                    group_data['name_target'] = extract_text(target_elem)
            
            # Extract _Desc_0
            elif unit_id.endswith('_Desc_0'):
                group_data['desc_source'] = extract_text(source_elem)
                target_state = target_elem.get('state', '') if target_elem is not None else ''
                group_data['desc_target_state'] = target_state
                # Use empty string if state is "needs-translation"
                if target_state == 'needs-translation':
                    group_data['desc_target'] = ''
                else:
                    group_data['desc_target'] = extract_text(target_elem)
        
        data[group_id] = group_data
    
    return data, group_order


def compare_files(file1, file2, compare_type, output_file=None, include_state=False):
    """
    Compare two XLF files and identify changes in translations.
    
    Args:
        file1: Path to the first (older) XLF file
        file2: Path to the second (newer) XLF file
        compare_type: Either 'name' or 'description'
        output_file: Optional output file path
        include_state: Whether to check and output state information
    """
    print(f"Parsing {file1}...")
    data1, order1 = parse_xlf_file(file1)
    
    print(f"Parsing {file2}...")
    data2, order2 = parse_xlf_file(file2)
    
    # Set default output file if not specified
    if output_file is None:
        file1_basename = os.path.splitext(os.path.basename(file1))[0]
        file2_basename = os.path.splitext(os.path.basename(file2))[0]
        output_dir = 'xlf-comparisons'
        os.makedirs(output_dir, exist_ok=True)
        
        suffix = '_names' if compare_type == 'name' else '_descriptions'
        output_file = os.path.join(output_dir, f'{file1_basename}_vs_{file2_basename}{suffix}.tsv')
    
    # Find changes
    changes = []
    
    # Get all group IDs that appear in both files, preserving order from file2
    common_groups = set(data1.keys()) & set(data2.keys())
    
    # Iterate in the order they appear in file2
    for group_id in order2:
        if group_id not in common_groups:
            continue
        d1 = data1[group_id]
        d2 = data2[group_id]
        
        if compare_type == 'name':
            # Check if _Name target content has changed (and optionally state)
            content_changed = d1['name_target'] != d2['name_target']
            state_changed = d1['name_target_state'] != d2['name_target_state'] if include_state else False
            
            if content_changed or state_changed:
                change_data = {
                    'abbr': d2['abbr'],
                    'name_source': d2['name_source'],
                    'content_before': d1['name_target'],
                    'content_after': d2['name_target']
                }
                if include_state:
                    change_data['state_before'] = d1['name_target_state']
                    change_data['state_after'] = d2['name_target_state']
                changes.append(change_data)
        
        elif compare_type == 'description':
            # Check if _Desc_0 target content has changed (and optionally state)
            content_changed = d1['desc_target'] != d2['desc_target']
            state_changed = d1['desc_target_state'] != d2['desc_target_state'] if include_state else False
            
            if content_changed or state_changed:
                change_data = {
                    'abbr': d2['abbr'],
                    'name_source': d2['name_source'],
                    'desc_source': d2['desc_source'],
                    'content_before': d1['desc_target'],
                    'content_after': d2['desc_target']
                }
                if include_state:
                    change_data['state_before'] = d1['desc_target_state']
                    change_data['state_after'] = d2['desc_target_state']
                changes.append(change_data)
    
    # Write results to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            if compare_type == 'name':
                # Write header
                if include_state:
                    f.write("Abbr\tName Source\tState Before\tState After\tContent Before\tContent After\n")
                else:
                    f.write("Abbr\tName Source\tContent Before\tContent After\n")
                
                # Write data
                for change in changes:
                    if include_state:
                        f.write(f"{change['abbr']}\t{change['name_source']}\t"
                               f"{change['state_before']}\t{change['state_after']}\t"
                               f"{change['content_before']}\t{change['content_after']}\n")
                    else:
                        f.write(f"{change['abbr']}\t{change['name_source']}\t"
                               f"{change['content_before']}\t{change['content_after']}\n")
            
            elif compare_type == 'description':
                # Write header
                if include_state:
                    f.write("Abbr\tName Source\tDesc Source\tState Before\tState After\tContent Before\tContent After\n")
                else:
                    f.write("Abbr\tName Source\tDesc Source\tContent Before\tContent After\n")
                
                # Write data
                for change in changes:
                    if include_state:
                        f.write(f"{change['abbr']}\t{change['name_source']}\t{change['desc_source']}\t"
                               f"{change['state_before']}\t{change['state_after']}\t"
                               f"{change['content_before']}\t{change['content_after']}\n")
                    else:
                        f.write(f"{change['abbr']}\t{change['name_source']}\t{change['desc_source']}\t"
                               f"{change['content_before']}\t{change['content_after']}\n")
        
        print(f"\nFound {len(changes)} changed entries")
        print(f"Results written to '{output_file}'")
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Compare two XLF files and identify translations that have changed.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_xlf.py -n crowdin-downloads/file1.xlf crowdin-downloads/file2.xlf
  python compare_xlf.py -n -s crowdin-downloads/file1.xlf crowdin-downloads/file2.xlf
  python compare_xlf.py -d crowdin-downloads/old.xlf crowdin-downloads/new.xlf output.tsv
        """
    )
    
    # Create mutually exclusive group for comparison type
    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument('-n', '--names', action='store_true',
                           help='Compare _Name entries')
    type_group.add_argument('-d', '--descriptions', action='store_true',
                           help='Compare _Desc_0 entries')
    
    parser.add_argument('-s', '--include-state', action='store_true',
                       help='Include target state columns in output (checks for state changes)')
    
    parser.add_argument('file1', help='First (older) XLF file path')
    parser.add_argument('file2', help='Second (newer) XLF file path')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Output file path (optional, defaults to xlf-comparisons/<file1>_vs_<file2>_<type>.tsv)')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not os.path.exists(args.file1):
        print(f"Error: Input file '{args.file1}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.file2):
        print(f"Error: Input file '{args.file2}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Determine comparison type
    compare_type = 'name' if args.names else 'description'
    
    # Compare files
    compare_files(args.file1, args.file2, compare_type, args.output_file, args.include_state)


if __name__ == '__main__':
    main()
