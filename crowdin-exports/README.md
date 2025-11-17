# Crowdin Exports Folder

This folder contains files exported from Crowdin using the "Export to XLIFF" option.

## File Format

**Format:** XLIFF (XML Localization Interchange File Format) version 1.2

**Extension:** `.xliff`

**Naming Convention:** `SemanticDomains_<language-code>.xliff` (with optional numbering or timestamp)

**Namespace:** Uses the OASIS XLIFF 1.2 namespace (`urn:oasis:names:tc:xliff:document:1.2`)

## Source

Files in this folder are obtained from Crowdin by:

1. Navigating to the translation project
2. Selecting "Export to XLIFF" option
3. Downloading the exported file for the desired language

## Destination

These files may be used for:

- Quality assurance and translation review
- Identifying untranslated or improperly translated content
- Analysis of translation completion status

## Contents

The XLIFF files contain:

- Trans-unit elements with translation units
- Source and target text elements
- Translation state attributes (`approved`, `translate`, `state`)
- Resource names (`resname`) for identifying content types
- Structural metadata for Semantic Domain organization
