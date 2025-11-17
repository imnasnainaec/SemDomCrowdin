# Semantic Domains Crowdin Tools

A collection of scripts for working with Crowdin translation of Semantic Domain files.

## Table of Contents

- [Scripts](#scripts)
- [Script Details](#script-details)
  - [extract_xlf.py](#extract_xlfpy)
  - [find_identical_translations.py](#find_identical_translationspy)
  - [compare_xlf.py](#compare_xlfpy)
  - [sort_comparisons.py](#sort_comparisonspy)
- [Data Folders](#data-folders)
- [License](#license)

## Scripts

- `extract_xlf.py` - Extract content from XLF files based on trans-unit ID patterns
- `find_identical_translations.py` - Analyze XLIFF files to find identical source/target translations
- `compare_xlf.py` - Compare two XLF files to identify translation changes
- `sort_comparisons.py` - Interactively sort comparison results into user-defined groups

## Script Details

### extract_xlf.py

Extracts source and target content from XLF files based on trans-unit ID patterns.

**Purpose:** Parse XLF files downloaded from Crowdin and extract specific types of content (names, descriptions, or questions) into tab-separated text files for analysis or further processing.

**Input:** XLF files from `crowdin-downloads/`

**Output:** Tab-separated text files saved to `xlf_extracts/`

**Usage:**

```bash
# Extract entries with id ending in "_Name"
python extract_xlf.py -n crowdin-downloads/SemanticDomains.pt-BR.xlf

# Extract entries with id ending in "_Name" and include "_Desc_0" target
python extract_xlf.py -N crowdin-downloads/SemanticDomains.pt-BR.xlf

# Extract entries with id ending in "_Desc_0"
python extract_xlf.py -d crowdin-downloads/SemanticDomains.pt-BR.xlf [output.txt]

# Extract entries with id ending in "_Desc_0" and include "_Name" target
python extract_xlf.py -D crowdin-downloads/SemanticDomains.pt-BR.xlf

# Extract entries with id ending in "_Qs_#_Q" (where # is any number)
python extract_xlf.py -q crowdin-downloads/SemanticDomains.pt-BR.xlf
```

**Options:**

- `-n, --names`: Extract name entries only
- `-N, --names-with-descriptions`: Extract names (and corresponding descriptions in English)
- `-d, --descriptions`: Extract description entries only
- `-D, --descriptions-with-names`: Extract descriptions (and corresponding names in English)
- `-q, --questions`: Extract question entries

**Output:** Tab-separated text file with extracted content. If no output file is specified, creates a file with an auto-generated name based on the input file and extraction type.

### find_identical_translations.py

Analyzes XLIFF files to find trans-units where the source and target are identical or contain matching pieces.

**Purpose:** Identify potential translation issues where translated content is identical to the source, which may indicate untranslated content or require review.

**Input:** XLIFF files from `crowdin-exports/`

**Output:** Text files saved to `identical-translations/`

**Usage:**

```bash
# Analyze an XLIFF file (output defaults to identical-translations/)
python find_identical_translations.py crowdin-exports/SemanticDomains_pt-BR.xliff

# Specify a custom output file path
python find_identical_translations.py crowdin-exports/SemanticDomains_pt-BR.xliff custom_output.txt
```

**Analysis Categories:**

The script identifies and categorizes three types of potential issues:

- **Approved (comma-split)**: Approved translations where comma-separated target pieces match source text
- **Approved + translate=no (identical)**: Approved translations with `translate=no` attribute that are identical to source
- **Not approved (identical)**: Non-approved translations that are identical to source

**Output Format:** Text file with categorized results showing matching trans-units, organized by case type. Each entry includes the trans-unit ID, resource name, source text, target text, and matching pieces identified.

### compare_xlf.py

Compares two XLF files to identify translations that have changed between versions.

**Purpose:** Track translation changes over time by comparing XLF files downloaded at different times from Crowdin. Shows both state changes (e.g., "needs-translation" → "translated") and content changes.

**Input:** Two XLF files from `crowdin-downloads/`

**Output:** TSV files saved to `xlf-comparisons/`

**Usage:**

```bash
# Compare _Name content changes only (no state columns)
python compare_xlf.py -n crowdin-downloads/SemanticDomains.pt-BR_old.xlf crowdin-downloads/SemanticDomains.pt-BR_new.xlf

# Compare _Name content AND state changes (includes state columns)
python compare_xlf.py -n -s crowdin-downloads/SemanticDomains.pt-BR_old.xlf crowdin-downloads/SemanticDomains.pt-BR_new.xlf

# Compare _Desc_0 entries between two files
python compare_xlf.py -d crowdin-downloads/file1.xlf crowdin-downloads/file2.xlf

# Specify a custom output file path
python compare_xlf.py -n file1.xlf file2.xlf custom_output.tsv
```

**Options:**

- `-n, --names`: Compare \_Name entries (required, mutually exclusive with -d)
- `-d, --descriptions`: Compare \_Desc_0 entries (required, mutually exclusive with -n)
- `-s, --include-state`: Include target state columns in output (optional)

**Output Format:** Tab-separated values (TSV) file with columns varying by comparison type and options:

**Without `-s` flag (content changes only):**

- **Names comparison**: Abbr | Name Source | Content Before | Content After
- **Descriptions comparison**: Abbr | Name Source | Desc Source | Content Before | Content After

**With `-s` flag (content and state changes):**

- **Names comparison**: Abbr | Name Source | State Before | State After | Content Before | Content After
- **Descriptions comparison**: Abbr | Name Source | Desc Source | State Before | State After | Content Before | Content After

Only entries where the target content has changed (or state has changed when using `-s`) are included in the output.

### sort_comparisons.py

Interactively sorts comparison results into user-defined groups.

**Purpose:** Review translation changes and categorize them into meaningful groups for analysis, reporting, or further action. Useful for organizing changes by type (e.g., "spelling fixes", "new translations", "improvements").

**Input:** TSV files from `xlf-comparisons/`

**Output:** TSV file with original data plus a "Group" column, saved to `sorted-comparisons/`

**Usage:**

```bash
# Sort a names comparison file, showing columns 3 and 4 (Content Before/After)
python sort_comparisons.py xlf-comparisons/file_names.tsv 3 4

# Sort a descriptions comparison with custom output path
python sort_comparisons.py xlf-comparisons/file_descriptions.tsv 4 5 custom_sorted.tsv
```

**Arguments:**

- `input_file`: Path to TSV file from `xlf-comparisons/`
- `col1`: First column index to display (1-based, e.g., 3)
- `col2`: Second column index to display (1-based, e.g., 4)
- `output_file`: Optional output path (defaults to `sorted-comparisons/<input>_sorted.tsv`)

**Interactive Process:**

For each row in the file:

1. Displays the complete row with all columns
2. Highlights the two user-specified columns
3. Shows a numbered list of existing groups
4. User enters a number to add to existing group, or 0 to create a new group
5. Process repeats until all rows are sorted

**Output Format:** Original TSV data with an additional "Group" column at the end. Rows are organized by group in the output file.

## Data Folders

Each subfolder contains specific types of Crowdin files. See individual folder READMEs for details:

- [`crowdin-downloads/README.md`](crowdin-downloads/README.md) - Files from Crowdin's "Download" option
- [`crowdin-exports/README.md`](crowdin-exports/README.md) - Files from Crowdin's "Export to XLIFF" option
- [`xlf_extracts/README.md`](xlf_extracts/README.md) - Extracted content from XLF files (tab-separated text)
- [`xlf-comparisons/README.md`](xlf-comparisons/README.md) - Comparison results between XLF file versions
- [`sorted-comparisons/README.md`](sorted-comparisons/README.md) - Interactively sorted and categorized comparison results
- [`identical-translations/README.md`](identical-translations/README.md) - Translation analysis output files

## License

MIT License - See [LICENSE](LICENSE) file for details.
