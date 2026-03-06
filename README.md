# osf-scraper

A Python package for scraping preregistration data from the [Open Science Framework (OSF)](https://osf.io).

## Installation

```bash
pip install -e .
```

For development (testing, linting):

```bash
pip install -e ".[dev]"
```

## Configuration

Authenticated requests enjoy higher rate limits. Set your OSF API token via an
environment variable:

```bash
export OSF_API_TOKEN=your_token_here
```

Or create a `.env` file in the project root:

```
OSF_API_TOKEN=your_token_here
```

Get your token at: <https://osf.io/settings/tokens>

---

## CLI Commands

After installation the following commands are available on your `PATH`:

### `osf-discover` — Discover preregistration IDs

```bash
# Discover all preregistration IDs
osf-discover

# Limit results
osf-discover --max-results 1000

# Include all registrations (not just preregistrations)
osf-discover --no-filter

# Use a specific API token
osf-discover --token YOUR_TOKEN

# Specify output file
osf-discover --output data/osf_ids.txt
```

### `osf-scrape` — Scrape registration data

```bash
# Scrape from a file of IDs
osf-scrape --file data/osf_ids.txt

# Specify output file
osf-scrape --file data/osf_ids.txt --output data/raw/preregistrations.jsonl

# Resume a previous run
osf-scrape --file data/osf_ids.txt --resume
```

### `osf-remaining` — Compute remaining unprocessed IDs

```bash
osf-remaining

# With custom paths
osf-remaining --all-ids data/osf_ids.txt \
              --successful-ids data/raw/successful_ids.txt \
              --output data/osf_ids_remaining.txt
```

### `osf-process` — Flatten raw JSONL into normalised data

```bash
osf-process

# With custom paths
osf-process --input data/raw/preregistrations.jsonl \
            --output data/processed/preregistrations.jsonl
```

### `osf-analyse` — Extract column names from processed data

```bash
osf-analyse

# With custom paths
osf-analyse --input data/processed/preregistrations.jsonl \
            --output data/analysed/columns.json
```

---

## Typical Workflow

```bash
# 1. Discover IDs
osf-discover --output data/osf_ids.txt

# 2. Scrape registration data
osf-scrape --file data/osf_ids.txt

# 3. If interrupted, compute remaining IDs and resume
osf-remaining
osf-scrape --file data/osf_ids_remaining.txt --resume

# 4. Flatten to normalised DataFrame
osf-process

# 5. Analyse columns
osf-analyse
```

---

## Python API

You can also use the package programmatically:

```python
from osf_scraper import OSFIDScraper

scraper = OSFIDScraper(api_token="your_token")
ids = scraper.discover_preregistration_ids(max_results=100)
scraper.save_ids(ids, "data/osf_ids.txt")
```

```python
from osf_scraper import process_registrations

process_registrations("data/raw/preregistrations.jsonl",
                      "data/processed/preregistrations.jsonl")
```

---

## Running Tests

```bash
pytest
```

---

## Project Structure

```
osf-scraper/
├── src/
│   └── osf_scraper/
│       ├── __init__.py        # Package exports
│       ├── cli.py             # CLI entry points
│       ├── discovery.py       # OSF ID discovery (OSFIDScraper)
│       ├── scraper.py         # Async batch scraper (TokenBucket, fetch logic)
│       ├── processing.py      # JSONL flattening & analysis
│       └── utils.py           # Remaining-IDs computation
├── tests/
│   ├── test_id_scraper.py
│   ├── test_token_bucket.py
│   └── test_process_registrations.py
├── data/                      # Data directory (not tracked)
├── pyproject.toml             # Package metadata, deps, entry points
└── README.md
```

## Requirements

- Python 3.10+
- Dependencies managed via `pyproject.toml` — install with `pip install -e .`

## License

MIT — see [LICENSE](LICENSE) for details.
