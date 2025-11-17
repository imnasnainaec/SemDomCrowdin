#!/usr/bin/env python3
"""
Analyze XLIFF files to find trans-units where source and target are identical or contain matching pieces.

Usage:
    python find_identical_translations.py <input_file> [output_file]
"""

import argparse
import xml.etree.ElementTree as ET
import sys
import os

def find_identical_translations(xliff_file):
    """
    Find <trans-unit> elements where translated="yes" and <source> is identical to <target>
    """
    # Parse the XLIFF file
    tree = ET.parse(xliff_file)
    root = tree.getroot()
    
    # Define the namespace
    ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
    
    # Find all trans-unit elements
    trans_units = root.findall('.//xliff:trans-unit', ns)
    
    results = []
    
    for trans_unit in trans_units:
        # Get attributes
        approved_attr = trans_unit.get('approved')
        translate_attr = trans_unit.get('translate')
        
        # Skip trans-units with resname ending in _Abbr
        resname = trans_unit.get('resname', '')
        if resname.endswith('_Abbr'):
            continue
        
        # Get source and target elements
        source = trans_unit.find('xliff:source', ns)
        target = trans_unit.find('xliff:target', ns)
        
        if source is not None and target is not None:
            # Skip if target has state="needs-translation"
            target_state = target.get('state')
            if target_state == 'needs-translation':
                continue
            
            source_text = source.text if source.text else ''
            target_text = target.text if target.text else ''
            
            # Case 1: approved and no translate=no, do comma-splitting
            if approved_attr == 'yes' and translate_attr != 'no':
                target_pieces = [piece.strip() for piece in target_text.split(',')]
                matching_pieces = [piece for piece in target_pieces if piece and piece in source_text]
                
                if matching_pieces:
                    trans_unit_id = trans_unit.get('id', 'N/A')
                    
                    results.append({
                        'id': trans_unit_id,
                        'resname': resname,
                        'source': source_text,
                        'target': target_text,
                        'matching_pieces': matching_pieces,
                        'type': 'approved (comma-split)'
                    })
            
            # Case 2: approved and translate=no, do identical check
            elif approved_attr == 'yes' and translate_attr == 'no':
                if source_text == target_text:
                    trans_unit_id = trans_unit.get('id', 'N/A')
                    
                    results.append({
                        'id': trans_unit_id,
                        'resname': resname,
                        'source': source_text,
                        'target': target_text,
                        'matching_pieces': [source_text],
                        'type': 'approved + translate=no (identical)'
                    })
            
            # Case 3: not approved and no translate=no, do identical check
            elif approved_attr != 'yes' and translate_attr != 'no':
                if source_text == target_text:
                    trans_unit_id = trans_unit.get('id', 'N/A')
                    
                    results.append({
                        'id': trans_unit_id,
                        'resname': resname,
                        'source': source_text,
                        'target': target_text,
                        'matching_pieces': [source_text],
                        'type': 'not approved (identical)'
                    })
            
            # Case 4: not approved and translate=no, skip
            # (no action needed)
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Analyze XLIFF files to find trans-units where source and target are identical or contain matching pieces.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python find_identical_translations.py crowdin-exports/SemanticDomains_pt-BR.xliff
  python find_identical_translations.py crowdin-exports/SemanticDomains_pt-BR.xliff custom_output.txt
        """
    )
    
    parser.add_argument('input_file', help='Input XLIFF file path (from crowdin-exports/)')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Output file path (optional, defaults to identical-translations/<input_name>_analysis.txt)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Set default output file if not specified
    if args.output_file is None:
        # Get the base name without extension
        input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
        # Create output in identical-translations folder
        output_dir = 'identical-translations'
        os.makedirs(output_dir, exist_ok=True)
        args.output_file = os.path.join(output_dir, f'{input_basename}_analysis.txt')
    
    print(f"Analyzing {args.input_file}...\n")
    
    # Find identical translations
    try:
        results = find_identical_translations(args.input_file)
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Sort results by type
    type_order = {
        'approved (comma-split)': 1,
        'approved + translate=no (identical)': 2,
        'not approved (identical)': 3
    }
    results.sort(key=lambda x: type_order.get(x['type'], 4))
    
    # Write results to file
    if results:
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(f"Found {len(results)} trans-unit(s)\n")
                f.write("=" * 80 + "\n\n")
                
                current_type = None
                for idx, item in enumerate(results, 1):
                    # Add section header when type changes
                    if item['type'] != current_type:
                        current_type = item['type']
                        f.write(f"\n{'=' * 80}\n")
                        f.write(f"CASE: {current_type.upper()}\n")
                        f.write(f"{'=' * 80}\n\n")
                    
                    f.write(f"{idx}. ID: {item['id']}\n")
                    f.write(f"   resname: {item['resname']}\n")
                    f.write(f"   Source: {item['source']}\n")
                    f.write(f"   Target: {item['target']}\n")
                    f.write(f"   Matching pieces: {', '.join(item['matching_pieces'])}\n")
                    f.write("\n")
            
            print(f"Results written to {args.output_file}")
            print(f"Found {len(results)} trans-unit(s)")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("No matching trans-units found.")


if __name__ == '__main__':
    main()
