# Semantic Domains Crowdin Tools

A collection of scripts for working with Crowdin translation of Semantic Domain files.

## Scripts

- `extract_xlf.py` - Extract content from XLF files based on trans-unit ID patterns
- `find_identical_translations.py` - Analyze XLIFF files to find identical source/target translations

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

## Data Folders

Each subfolder contains specific types of Crowdin files. See individual folder READMEs for details:

- [`crowdin-downloads/README.md`](crowdin-downloads/README.md) - Files from Crowdin's "Download" option
- [`crowdin-exports/README.md`](crowdin-exports/README.md) - Files from Crowdin's "Export to XLIFF" option
- [`xlf_extracts/README.md`](xlf_extracts/README.md) - Extracted content from XLF files (tab-separated text)
- [`identical-translations/README.md`](identical-translations/README.md) - Translation analysis output files

## License

MIT License - See [LICENSE](LICENSE) file for details.
