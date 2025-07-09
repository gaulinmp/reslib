# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResLib (Research Library) is a Python library for facilitating academic research in accounting and finance. It provides tools for:
- Dependency tracking in research pipelines
- Data downloading and caching (especially from WRDS)
- Code parsing and automation
- Visualization of research workflows

## Common Development Commands

### Package Installation
```bash
pip install -e .                    # Install in development mode
pip install -r requirements.txt     # Install basic dependencies
pip install -r requirements.dev.txt # Install development dependencies
```

### Documentation
```bash
cd docs/
make html                           # Build HTML documentation
make clean                          # Clean build artifacts
```

### Testing
The project uses doit for task automation. To run tasks:
```bash
doit                               # Run all tasks
doit list                          # List available tasks
```

## Code Architecture

### Core Modules

#### `reslib.automate`
- **Purpose**: Dependency tracking and pipeline automation
- **Key Components**:
  - `DependencyScanner`: Scans code for INPUT/OUTPUT comments to build dependency graphs
  - `code_parser.py`: Parsers for different languages (SAS, Stata, Python, Notebook)
  - `scanner.py`: Main scanning logic for extracting dependencies
- **Dependencies**: networkx, graphviz, pydot (for visualization)

#### `reslib.data`
- **Purpose**: Data downloading, caching, and I/O operations
- **Key Components**:
  - `cache.py`: `DatasetCache` class for disk-based caching with pandas
  - `io.py`: File I/O utilities
  - `sources/wrds/`: WRDS data source implementations (compustat.py, crsp.py, linking.py)
- **Dependencies**: pandas (core requirement)

#### `reslib.config`
- **Purpose**: Configuration management for the library

### Dependency Tracking System

The core innovation is automatic dependency extraction from code comments:

**Input Comments**: Files declare inputs using:
```
/* INPUT_DATASET: filename.dta */
/* INPUT_FILE: script.do */
```

**Output Comments**: Files declare outputs using:
```
/* OUTPUT: output_file.dta */
```

**Ignore Comments**: Files can be excluded using:
```
/* RESLIB_IGNORE: True */
```

The `DependencyScanner` processes these comments to build directed acyclic graphs (DAGs) showing research workflow dependencies.

### Code Parser Architecture

The system supports multiple languages through parser classes:
- `SAS`: Parses `.sas` files with `/* */` comments
- `Stata`: Parses `.do` files with `/* */` comments  
- `Notebook`: Parses `.ipynb` files
- `Python`: Parses `.py` files with `#` comments
- `Manual`: For manually specified dependencies

### Data Caching System

The `DatasetCache` class provides:
- Automatic caching of pandas DataFrames to disk
- Multiple file format support (pickle, parquet, CSV, etc.)
- Configurable cache expiration
- Metadata tracking

## Project Structure

```
reslib/
├── automate/           # Dependency tracking and automation
│   ├── code_parser.py  # Language-specific parsers
│   └── scanner.py      # Main dependency scanning logic
├── data/               # Data handling and caching
│   ├── cache.py        # Dataset caching functionality
│   ├── io.py           # File I/O utilities
│   └── sources/        # Data source implementations
│       └── wrds/       # WRDS-specific data downloaders
└── config.py           # Configuration management
```

## Development Notes

### Comment Parsing
- The system relies on specific comment formats for dependency extraction
- Comments must follow exact patterns (case-insensitive for ignore comments)
- Path separators are normalized (`\\` → `/`)

### Dependencies
- **Core**: pandas (≥0.22.0)
- **Visualization**: networkx, graphviz, pydot
- **Optional**: beautifulsoup4, tqdm (for web scraping features)

### Python Version Support
- Supports Python 3.8, 3.9, 3.10, 3.11, 3.12
- Uses modern type hints and pathlib where applicable

### Configuration
- Uses `dodo.py` for doit task automation
- Sphinx documentation in `docs/` directory
- Development notebooks in `dev_notebooks/`