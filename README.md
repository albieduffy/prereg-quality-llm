# Preregistration Quality LLM Evaluation

A Python repository for evaluating preregistration quality using LLM scoring and human scoring. This project is being developed in phases.

## Phase 0: OSF ID Discovery

**Current Status:** Phase 0 - Discovering Preregistration IDs

Phase 0 focuses on discovering OSF preregistration IDs from the OSF registrations endpoint. This provides the list of IDs needed for Phase 1.

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Set up OSF API token** (for authenticated requests):
   ```bash
   export OSF_API_TOKEN=your_token_here
   ```
   
   Note: The scraper works without authentication, but authenticated requests may have higher rate limits.

### Usage

#### Discover all preregistration IDs

```bash
python scripts/discover_ids.py
```

This will query the OSF registrations endpoint, filter for preregistrations, and save all discovered IDs to `data/osf_ids.txt`.

#### Limit the number of results

```bash
python scripts/discover_ids.py --max-results 100
```

#### Specify custom output file

```bash
python scripts/discover_ids.py --output data/my_prereg_ids.txt
```

#### Get all registrations (not just preregistrations)

```bash
python scripts/discover_ids.py --no-filter
```

#### Use API token

```bash
python scripts/discover_ids.py --token YOUR_TOKEN
```

Or set the environment variable:
```bash
export OSF_API_TOKEN=your_token_here
python scripts/discover_ids.py
```

### Output

The ID scraper saves discovered OSF IDs to a text file (default: `data/osf_ids.txt`), with one ID per line. This file can then be used as input for Phase 1.

---

## Phase 1: OSF Preregistration Scraper

Phase 1 focuses on gathering full preregistration data from the Open Science Framework (OSF) API using the IDs discovered in Phase 0.

### Usage

#### Fetch specific OSF IDs

```bash
python scripts/scrape_osf.py --ids abc12 def34 ghi56
```

#### Fetch from a file (e.g., from Phase 0)

```bash
python scripts/scrape_osf.py --file data/osf_ids.txt
```

#### Specify output directory

```bash
python scripts/scrape_osf.py --ids abc12 --output data/raw
```

#### Use API token

```bash
python scripts/scrape_osf.py --ids abc12 --token YOUR_TOKEN
```

Or set the environment variable:
```bash
export OSF_API_TOKEN=your_token_here
python scripts/scrape_osf.py --ids abc12
```

### Output

The scraper saves each preregistration as a JSON file in the output directory (default: `data/raw/`). Each file contains:

- `osf_id`: The OSF registration ID
- `metadata`: Full registration metadata from OSF API
- `full_text`: Extracted text content from associated files
- `files_info`: Information about files associated with the registration

### Typical Workflow

1. **Phase 0:** Discover preregistration IDs
   ```bash
   python scripts/discover_ids.py --output data/osf_ids.txt
   ```

2. **Phase 1:** Scrape preregistration data using discovered IDs
   ```bash
   python scripts/scrape_osf.py --file data/osf_ids.txt --output data/raw
   ```

---

## Project Structure

```
prereg-quality-llm/
├── src/
│   └── osf/
│       ├── __init__.py
│       ├── id_scraper.py    # Phase 0: ID discovery
│       └── scraper.py       # Phase 1: Preregistration scraper
├── scripts/
│   ├── discover_ids.py      # Phase 0 CLI script
│   └── scrape_osf.py        # Phase 1 CLI script
├── data/
│   ├── osf_ids.txt          # Phase 0 output (discovered IDs)
│   └── raw/                 # Phase 1 output (scraped data)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Future Phases

- **Phase 2:** Text cleaning and preprocessing
- **Phase 3:** LLM-based quality scoring
- **Phase 4:** Human scoring integration
- **Phase 5:** Statistical analysis and evaluation

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

[Add your license here]
