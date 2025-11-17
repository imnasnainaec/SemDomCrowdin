#!/usr/bin/env python3
"""
Extract source and target content from XLF file based on trans-unit id patterns.

Usage:
    python extract_xlf.py -n <input_file> [output_file]  # Extract *_Name entries
    python extract_xlf.py -N <input_file> [output_file]  # Extract *_Name entries with *_Desc_0 target
    python extract_xlf.py -d <input_file> [output_file]  # Extract *_Desc_0 entries
    python extract_xlf.py -D <input_file> [output_file]  # Extract *_Desc_0 entries with *_Name target
    python extract_xlf.py -q <input_file> [output_file]  # Extract *_Qs_#_Q entries
"""

import argparse
import xml.etree.ElementTree as ET
import re
import sys


def extract_text(element):
    """Extract text content from an XML element, preserving inner structure."""
    if element is None:
        return ""
    # Get all text content including text in child elements
    return ''.join(element.itertext()).strip()


def extract_data(input_file, pattern_type, output_file=None):
    """
    Extract source and target content from XLF file.
    
    Args:
        input_file: Path to the input XLF file
        pattern_type: Type of pattern to match ('name', 'description', or 'question')
        output_file: Optional output file path (defaults to stdout or auto-generated name)
    """
    # Define patterns based on type
    if pattern_type == 'name':
        pattern = re.compile(r'_Name$')
        default_suffix = '_names.txt'
        include_extra = False
        extra_pattern = None
    elif pattern_type == 'name_with_desc':
        pattern = re.compile(r'_Name$')
        default_suffix = '_names_descriptions.txt'
        include_extra = True
        extra_pattern = re.compile(r'_Desc_0$')
    elif pattern_type == 'description':
        pattern = re.compile(r'_Desc_0$')
        default_suffix = '_descriptions.txt'
        include_extra = False
        extra_pattern = None
    elif pattern_type == 'description_with_name':
        pattern = re.compile(r'_Desc_0$')
        default_suffix = '_descriptions_names.txt'
        include_extra = True
        extra_pattern = re.compile(r'_Name$')
    elif pattern_type == 'question':
        pattern = re.compile(r'_Qs_\d+_Q$')
        default_suffix = '_questions.txt'
        include_extra = False
        extra_pattern = None
    else:
        raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    # Set output file if not specified
    if output_file is None:
        # Get the base name without path
        input_basename = input_file.rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
        output_basename = input_basename.rsplit('.', 1)[0] + default_suffix
        # Create output in xlf_extracts folder
        import os
        output_dir = 'xlf_extracts'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, output_basename)
    
    # Parse the XML file
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file: {e}", file=sys.stderr)
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
    
    # Find all group elements that contain sil:guid (semantic domain groups)
    if use_ns:
        all_groups = root.findall('.//xliff:group', namespaces)
    else:
        all_groups = root.findall('.//group')
    
    # Filter to find semantic domain groups (those with guid child)
    target_groups = []
    for group in all_groups:
        # Check if this group has a guid child (semantic domain marker)
        has_guid = False
        for child in group:
            if 'guid' in child.tag:
                has_guid = True
                break
        if has_guid:
            target_groups.append(group)
    
    # Extract matching entries
    results = []
    missing_count = 0
    
    for group in target_groups:
        group_id = group.get('id', '')
        
        # Get all child elements
        children = list(group)
        
        # First, find the _Abbr trans-unit to get the domain number
        abbr_text = ""
        for child in children:
            if child.tag.endswith('trans-unit'):
                child_id = child.get('id', '')
                if child_id.endswith('_Abbr'):
                    if use_ns:
                        abbr_source = child.find('xliff:source', namespaces)
                    else:
                        abbr_source = child.find('source')
                    abbr_text = extract_text(abbr_source)
                    break
        
        # Filter out _SubPos groups and only search in non-SubPos children
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
        
        # Look for matching trans-unit
        found = False
        source_text = ""
        target_text = ""
        extra_source_text = ""
        
        for trans_unit in trans_units:
            unit_id = trans_unit.get('id', '')
            
            if pattern.search(unit_id):
                if use_ns:
                    source_elem = trans_unit.find('xliff:source', namespaces)
                    target_elem = trans_unit.find('xliff:target', namespaces)
                else:
                    source_elem = trans_unit.find('source')
                    target_elem = trans_unit.find('target')
                
                source_text = extract_text(source_elem)
                target_text = extract_text(target_elem)
                found = True
            
            # Look for extra field if needed
            if include_extra and extra_pattern.search(unit_id):
                if use_ns:
                    extra_source_elem = trans_unit.find('xliff:source', namespaces)
                else:
                    extra_source_elem = trans_unit.find('source')
                extra_source_text = extract_text(extra_source_elem)
        
        if found:
            if include_extra:
                # For description_with_name, put name source before description columns
                if pattern_type == 'description_with_name':
                    results.append((abbr_text, extra_source_text, source_text, target_text))
                else:
                    results.append((abbr_text, source_text, target_text, extra_source_text))
            else:
                results.append((abbr_text, source_text, target_text))
        else:
            print(f"Warning: Group '{group_id}' lacks the desired element")
            missing_count += 1
    
    # Write results to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write("\t".join(result) + "\n")
        
        print(f"\nExtracted {len(results)} entries to '{output_file}'")
        if missing_count > 0:
            print(f"Warning: {missing_count} group(s) were missing the desired element")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Extract source and target content from XLF file based on trans-unit id patterns.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_xlf.py -n SemanticDomains.pt-BR.xlf
  python extract_xlf.py -N SemanticDomains.pt-BR.xlf
  python extract_xlf.py -d SemanticDomains.pt-BR.xlf output.txt
  python extract_xlf.py -D SemanticDomains.pt-BR.xlf
  python extract_xlf.py -q SemanticDomains.pt-BR.xlf
        """
    )
    
    # Create mutually exclusive group for pattern type
    pattern_group = parser.add_mutually_exclusive_group(required=True)
    pattern_group.add_argument('-n', '--names', action='store_true',
                              help='Extract entries with id ending in "_Name"')
    pattern_group.add_argument('-N', '--names-with-descriptions', action='store_true',
                              help='Extract entries with id ending in "_Name" and also include "_Desc_0" target')
    pattern_group.add_argument('-d', '--descriptions', action='store_true',
                              help='Extract entries with id ending in "_Desc_0"')
    pattern_group.add_argument('-D', '--descriptions-with-names', action='store_true',
                              help='Extract entries with id ending in "_Desc_0" and also include "_Name" target')
    pattern_group.add_argument('-q', '--questions', action='store_true',
                              help='Extract entries with id ending in "_Qs_#_Q" (where # is any number)')
    
    parser.add_argument('input_file', help='Input XLF file path')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Output file path (optional, defaults to input_name + suffix)')
    
    args = parser.parse_args()
    
    # Determine pattern type
    if args.names:
        pattern_type = 'name'
    elif args.names_with_descriptions:
        pattern_type = 'name_with_desc'
    elif args.descriptions:
        pattern_type = 'description'
    elif args.descriptions_with_names:
        pattern_type = 'description_with_name'
    elif args.questions:
        pattern_type = 'question'
    
    # Extract data
    extract_data(args.input_file, pattern_type, args.output_file)


if __name__ == '__main__':
    main()
