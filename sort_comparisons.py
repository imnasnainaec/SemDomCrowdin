#!/usr/bin/env python3
"""
Interactively sort comparison results into user-defined groups.

Usage:
    python sort_comparisons.py <input_file> <col1> <col2> [output_file]
    
    col1, col2: 1-based column indices to display (e.g., 3 4 for columns 3 and 4)
    
    Users can assign multiple groups per row by typing multiple characters.
"""

import argparse
import sys
import os


def read_tsv_file(input_file):
    """Read TSV file and return header and data rows."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("Error: Input file is empty.", file=sys.stderr)
            sys.exit(1)
        
        header = lines[0].strip().split('\t')
        data = [line.strip().split('\t') for line in lines[1:] if line.strip()]
        
        return header, data
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def display_row(row, col1_idx, col2_idx, header):
    """Display the full row and highlight the specified columns."""
    print("\n" + "=" * 80)
    print("Full row data:")
    for i, (col_name, value) in enumerate(zip(header, row), 1):
        marker = " <--" if i in [col1_idx + 1, col2_idx + 1] else ""
        print(f"  {i}. {col_name}: {value}{marker}")
    print("=" * 80)


def get_user_choice(group_chars):
    """
    Prompt user to select groups using character keys.
    
    Returns: (list of group names, should_end_early)
    """
    print("\nAvailable groups:")
    print("  ` Create new group")
    for char, group_name in group_chars.items():
        if char != '`':
            print(f"  {char} {group_name}")
    
    while True:
        try:
            choice = input("\nEnter character(s) for group(s) (or Enter to skip/end): ").strip()
            
            # Handle empty input (potential early end)
            if not choice:
                confirm = input("Press Enter again to end early and save partial results, or type something to continue: ").strip()
                if not confirm:
                    return None, True  # Signal early end
                else:
                    continue
            
            # Handle backtick for new group
            if '`' in choice:
                new_group = input("Enter name for new group: ").strip()
                if not new_group:
                    print("Group name cannot be empty. Try again.")
                    continue
                
                # Find next available character
                available_chars = ['e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\']
                next_char = None
                for c in available_chars:
                    if c not in group_chars:
                        next_char = c
                        break
                
                if next_char is None:
                    print("No more character slots available for new groups.")
                    continue
                
                group_chars[next_char] = new_group
                print(f"New group '{new_group}' assigned to character '{next_char}'")
                
                # Replace backtick with the new character in choice
                choice = choice.replace('`', next_char)
            
            # Validate all characters
            invalid_chars = [c for c in choice if c not in group_chars]
            if invalid_chars:
                print(f"Invalid characters: {', '.join(invalid_chars)}")
                print("Please use only the characters shown above.")
                continue
            
            # Get group names for selected characters
            selected_groups = [group_chars[c] for c in choice]
            return selected_groups, False
            
        except EOFError:
            print("\nOperation cancelled by user.")
            sys.exit(0)


def sort_comparisons(input_file, col1, col2, output_file=None):
    """
    Interactively sort comparison file rows into groups.
    
    Args:
        input_file: Path to input TSV file from xlf-comparisons
        col1: First column index (1-based) to display
        col2: Second column index (1-based) to display
        output_file: Optional output file path
    """
    # Read input file
    header, data = read_tsv_file(input_file)
    
    # Validate column indices
    num_cols = len(header)
    if col1 < 1 or col1 > num_cols or col2 < 1 or col2 > num_cols:
        print(f"Error: Column indices must be between 1 and {num_cols}.", file=sys.stderr)
        sys.exit(1)
    
    # Convert to 0-based indices
    col1_idx = col1 - 1
    col2_idx = col2 - 1
    
    # Set default output file if not specified
    if output_file is None:
        input_basename = os.path.splitext(os.path.basename(input_file))[0]
        output_dir = 'sorted-comparisons'
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f'{input_basename}_sorted.tsv')
    
    print(f"Input file: {input_file}")
    print(f"Displaying columns: {header[col1_idx]} and {header[col2_idx]}")
    print(f"Total rows to sort: {len(data)}")
    
    # Initialize default groups with character mappings
    group_chars = {
        '1': 'untranslated',
        '2': 'wrong',
        '3': 'misc',
        '4': 'typo',
        '5': 'article/preposition',
        '6': 'add word',
        '7': 'remove word',
        '8': 'change word',
        '9': 'neuter',
        '0': '-se',
        '-': 'PT->BR',
        '=': 'count',
        'q': 'infinitive',
        'w': 'other'
    }
    
    # Track group membership for each row (row_index -> set of group names)
    row_groups = {}
    
    # Process each row
    rows_processed = 0
    for i, row in enumerate(data):
        print(f"\n\n{'#' * 80}")
        print(f"Row {i + 1} of {len(data)}")
        
        # Display the full row
        display_row(row, col1_idx, col2_idx, header)
        
        # Get user's choice
        selected_groups, should_end = get_user_choice(group_chars)
        
        if should_end:
            print("\nEnding early. Saving partial results...")
            rows_processed = i
            data = data[:i]  # Only keep processed rows
            break
        
        # Add row to selected groups
        row_groups[i] = set(selected_groups) if selected_groups else set()
        rows_processed = i + 1
        
        if selected_groups:
            print(f"\n✓ Added to groups: {', '.join(selected_groups)}")
        else:
            print(f"\n✓ No groups selected for this row")
    
    # Get list of all groups that were actually used
    all_groups = sorted(set(group_chars.values()))
    used_groups = set()
    for groups_set in row_groups.values():
        used_groups.update(groups_set)
    used_groups = sorted(used_groups)
    
    # Write output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header with group columns
            f.write('\t'.join(header + used_groups) + '\n')
            
            # Write data with group membership columns
            for i, row in enumerate(data):
                groups_in_row = row_groups.get(i, set())
                group_values = ['1' if group in groups_in_row else '0' for group in used_groups]
                f.write('\t'.join(row + group_values) + '\n')
        
        print(f"\n\n{'=' * 80}")
        print(f"✓ Sorting complete!")
        print(f"✓ Processed {rows_processed} of {len(data) if rows_processed == len(data) else len(data)} rows")
        print(f"✓ Output written to: {output_file}")
        print(f"✓ Groups used: {len(used_groups)}")
        for group_name in used_groups:
            count = sum(1 for groups_set in row_groups.values() if group_name in groups_set)
            print(f"  - {group_name}: {count} rows")
    
    except Exception as e:
        print(f"\nError writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Interactively sort comparison results into user-defined groups.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sort names comparison, showing columns 3 and 4 (Content Before/After)
  python sort_comparisons.py xlf-comparisons/file_names.tsv 3 4
  
  # Sort descriptions comparison with custom output
  python sort_comparisons.py xlf-comparisons/file_descriptions.tsv 4 5 sorted_output.tsv

Character Keys:
  ` - Create new group (assigns to next available: e,r,t,y,u,i,o,p,[,],\\)
  1 - untranslated          2 - wrong              3 - misc
  4 - typo                  5 - article/preposition 6 - add word
  7 - remove word           8 - change word         9 - neuter
  0 - -se                   - - PT->BR              = - count
  q - infinitive            w - other
  
  Multiple characters can be entered to assign to multiple groups (e.g., "14" or "2q")
  Press Enter twice to end early and save partial results
        """
    )
    
    parser.add_argument('input_file', help='Input TSV file from xlf-comparisons/')
    parser.add_argument('col1', type=int, help='First column index to display (1-based)')
    parser.add_argument('col2', type=int, help='Second column index to display (1-based)')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Output file path (optional, defaults to sorted-comparisons/<input>_sorted.tsv)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Sort comparisons
    sort_comparisons(args.input_file, args.col1, args.col2, args.output_file)


if __name__ == '__main__':
    main()
