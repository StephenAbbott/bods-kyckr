# bods-kyckr

Transform [Kyckr](https://www.kyckr.com/) UBO Verify V2 data into [Beneficial Ownership Data Standard (BODS)](https://standard.openownership.org/) v0.4 format.

Part of the [BODS Interoperability Toolkit](https://github.com/StephenAbbott/bods-interoperability-toolkit).

## Overview

This pipeline ingests Kyckr UBO Verify V2 JSON responses and produces BODS v0.4 compliant statements, including:

- **Entity statements** for companies and legal entities
- **Person statements** for individuals (UBOs)
- **Ownership-or-control statements** linking persons to entities, with interest details

## Installation

```bash
pip install .
```

For development (includes pytest and BODS compliance validation):

```bash
pip install ".[dev]"
```

## Usage

### Transform a single JSON file

```bash
bods-kyckr transform input.json -o output.json
```

### Batch process a directory of JSON files

```bash
bods-kyckr batch /path/to/json/files/ -o output.jsonl
```

### Options

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Output file path (default: `output.json` / `output.jsonl`) |
| `--format` | Output format: `json` or `jsonl` |
| `-p`, `--publisher` | Publisher name for BODS metadata |
| `--publication-date` | Publication date in `YYYY-MM-DD` format (defaults to today) |
| `-v`, `--verbose` | Enable verbose logging |

## Project Structure

```
src/bods_kyckr/
├── ingestion/       # JSON reading and data models
├── transform/       # BODS statement generation (entities, persons, relationships, interests, identifiers)
├── output/          # Statement serialisation (JSON/JSONL)
├── utils/           # Country codes, date handling, statement helpers
├── pipeline.py      # Orchestrates ingestion -> transform -> output
└── cli.py           # Click CLI entry point
```

## Testing

```bash
pytest
```

Tests include BODS schema compliance validation via [libcovebods](https://github.com/openownership/lib-cove-bods).

## License

MIT
