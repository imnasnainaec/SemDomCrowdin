#!/usr/bin/env python3
"""
Extract _Name trans-units where comma-separated source and target have different lengths.

Usage:
    python comma_lists.py <input_file> [output_file]
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


def comma_lists(input_file, output_file, include_state=False):
    """
    Extract _Name trans-units where comma-separated source and target have different lengths.
    
    Args:
        input_file: Path to the input XLIFF file from crowdin-exports/
        output_file: Path to the output TSV file
        include_state: Whether to include the target state column in output
    """
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    # Define namespace (if present)
    namespaces = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
    # Check if namespace is used
    if root.tag.startswith('{'):
        ns_uri = root.tag[1:root.tag.index('}')]
        namespaces['xliff'] = ns_uri
        use_ns = True
    else:
        use_ns = False
    
    # Find all trans-unit elements
    if use_ns:
        all_trans_units = root.findall('.//xliff:trans-unit', namespaces)
    else:
        all_trans_units = root.findall('.//trans-unit')
    
    # Track results - separate increased and decreased
    increased_results = []  # Target has more items than source
    decreased_results = []  # Target has fewer items than source
    
    # Process each trans-unit
    for trans_unit in all_trans_units:
        # Use resname for the actual identifier (XLIFF exports) or id (XLF downloads)
        unit_id = trans_unit.get('resname', '') or trans_unit.get('id', '')
        
        # Only process _Name trans-units
        if not unit_id.endswith('_Name'):
            continue
        
        # Get source and target elements
        if use_ns:
            source_elem = trans_unit.find('xliff:source', namespaces)
            target_elem = trans_unit.find('xliff:target', namespaces)
        else:
            source_elem = trans_unit.find('source')
            target_elem = trans_unit.find('target')
        
        # Extract text
        source_text = extract_text(source_elem)
        target_text = extract_text(target_elem)
        
        # Get target state
        target_state = target_elem.get('state', '') if target_elem is not None else ''
        
        # Check if comma-separated lengths differ
        source_parts = [part.strip() for part in source_text.split(',')]
        target_parts = [part.strip() for part in target_text.split(',')]
        
        if len(source_parts) != len(target_parts):
            # Find the corresponding _Abbr trans-unit
            # The _Abbr trans-unit has the same prefix as _Name
            abbr_id = unit_id.replace('_Name', '_Abbr')
            abbr_source = ""
            
            # Search for the _Abbr trans-unit
            for tu in all_trans_units:
                tu_id = tu.get('resname', '') or tu.get('id', '')
                if tu_id == abbr_id:
                    if use_ns:
                        abbr_source_elem = tu.find('xliff:source', namespaces)
                    else:
                        abbr_source_elem = tu.find('source')
                    abbr_source = extract_text(abbr_source_elem)
                    break
            
            result = {
                'abbr_source': abbr_source,
                'name_source': source_text,
                'name_target': target_text,
                'target_state': target_state,
                'source_count': len(source_parts),
                'target_count': len(target_parts)
            }
            
            # Categorize by whether target increased or decreased
            if len(target_parts) > len(source_parts):
                increased_results.append(result)
            else:
                decreased_results.append(result)
    
    # Write results to TSV file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            if include_state:
                f.write('Abbr Source\tName Source\tName Target\tTarget State\n')
            else:
                f.write('Abbr Source\tName Source\tName Target\n')
            
            # Write increased length entries first
            if increased_results:
                f.write('\n### INCREASED LENGTH (target has MORE items than source) ###\n')
                for result in increased_results:
                    if include_state:
                        f.write(f"{result['abbr_source']}\t{result['name_source']}\t"
                               f"{result['name_target']}\t{result['target_state']}\n")
                    else:
                        f.write(f"{result['abbr_source']}\t{result['name_source']}\t"
                               f"{result['name_target']}\n")
            
            # Write decreased length entries second
            if decreased_results:
                f.write('\n### DECREASED LENGTH (target has FEWER items than source) ###\n')
                for result in decreased_results:
                    if include_state:
                        f.write(f"{result['abbr_source']}\t{result['name_source']}\t"
                               f"{result['name_target']}\t{result['target_state']}\n")
                    else:
                        f.write(f"{result['abbr_source']}\t{result['name_source']}\t"
                               f"{result['name_target']}\n")
        
        total_results = len(increased_results) + len(decreased_results)
        print(f"Successfully extracted {total_results} entries to '{output_file}'")
        print(f"  Increased length: {len(increased_results)}")
        print(f"  Decreased length: {len(decreased_results)}")
    
    except Exception as e:
        print(f"Error writing output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Extract _Name trans-units where comma-separated source and target have different lengths.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python comma_lists.py crowdin-exports/SemanticDomains_pt-BR.xliff
  python comma_lists.py -s crowdin-exports/SemanticDomains_pt-BR.xliff
  python comma_lists.py crowdin-exports/SemanticDomains_pt-BR.xliff output.tsv

This script analyzes XLIFF files to find _Name trans-units where the number of
comma-separated items differs between source and target. This may indicate
missing or extra translations in lists.

Output columns:
  - Abbr Source: The source text from the corresponding _Abbr trans-unit
  - Name Source: The source text from the _Name trans-unit
  - Name Target: The target text from the _Name trans-unit
  - Target State: The state attribute of the target element (only with -s flag)
        """
    )
    
    parser.add_argument('input_file', help='Input XLIFF file path from crowdin-exports/')
    parser.add_argument('output_file', nargs='?', help='Output TSV file path (optional)')
    parser.add_argument('-s', '--include-state', action='store_true',
                       help='Include target state column in output')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Generate output filename if not provided
    if args.output_file is None:
        input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
        output_dir = 'different-name-lists'
        os.makedirs(output_dir, exist_ok=True)
        args.output_file = os.path.join(output_dir, f'{input_basename}_comma_lists.tsv')
    
    # Process the file
    comma_lists(args.input_file, args.output_file, args.include_state)


if __name__ == '__main__':
    main()
