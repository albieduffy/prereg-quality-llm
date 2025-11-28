# Preregistration Quality LLM Evaluation

A Python repository for evaluating preregistration quality using LLM scoring and human scoring. This project implements a complete pipeline from OSF data ingestion through LLM evaluation to statistical analysis.

## Repository Structure

```
prereg-quality-llm/
├── config/          # Configuration files (rubric, schema, model config)
├── data/            # Data directories (raw, processed, scores, merged)
├── src/             # Source code modules
└── scripts/         # Runnable pipeline scripts
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Configure model settings:**
   Edit `config/model_config.yaml` to adjust model parameters if needed.

## Usage

### 1. Fetch Preregistrations from OSF

Fetch preregistrations using OSF IDs:

```bash
python scripts/fetch_osf.py --ids abc12 def34 ghi56 --output data/raw
```

Or from a file (one OSF ID per line):

```bash
python scripts/fetch_osf.py --file osf_ids.txt --output data/raw
```

Optional: Set `OSF_API_TOKEN` environment variable for authenticated requests.

### 2. Clean Preregistration Text

Clean the raw OSF JSON files:

```bash
python scripts/clean_text.py \
    --input data/raw \
    --output data/processed
```

### 3. Score Preregistrations with LLM

Score all cleaned preregistrations:

```bash
python scripts/score_llm.py \
    --input data/processed \
    --output data/scores_llm \
    --config config/model_config.yaml
```

This will:
- Load the rubric and schema from config
- Send each preregistration to the LLM for scoring
- Validate responses against the JSON schema
- Save scores to `data/scores_llm/`

### 4. Validate LLM Scores

Validate all score JSON files against the schema:

```bash
python scripts/validate_scores.py \
    --input data/scores_llm \
    --schema config/schema.json
```

### 5. Merge Datasets

Merge preregistration metadata, LLM scores, and human scores:

```bash
python scripts/merge_all.py \
    --raw data/raw \
    --llm-scores data/scores_llm \
    --human-scores data/scores_human \
    --output data/merged/analysis_dataset.csv
```

**Note:** Human scores should be in CSV format with an `osf_id` column matching the OSF IDs in your dataset.

### 6. Run Statistical Analysis

Run regression models on the merged dataset:

```bash
python scripts/run_analysis.py \
    --input data/merged/analysis_dataset.csv \
    --output data/merged/analysis_results \
    --publication \
    --time-to-pub \
    --citations
```

The script will automatically detect which outcome variables are available and run the appropriate models:
- **Logistic regression** for publication outcome (binary)
- **Cox survival model** for time-to-publication
- **Negative binomial regression** for citation counts

## Configuration

### Rubric (`config/rubric.json`)

Defines the scoring criteria and scale for each dimension:
- Hypothesis clarity (1-5)
- Method specificity (1-5)
- Analysis detail (1-5)
- Power analysis (0-1)
- Completeness (1-5)

### Schema (`config/schema.json`)

JSON Schema defining the expected structure of LLM score outputs. Ensures consistency and enables validation.

### Model Config (`config/model_config.yaml`)

Configuration for the LLM scorer:
- Model name (default: gpt-4o)
- Temperature (default: 0 for deterministic outputs)
- Max tokens
- Paths to schema and rubric files

## Module Overview

### `src/osf/`
- **fetch_osf.py**: OSF API integration for fetching preregistration data

### `src/cleaning/`
- **clean_text.py**: Text cleaning utilities (HTML stripping, Unicode normalization)

### `src/scoring/`
- **build_prompt.py**: Prompt construction from rubric
- **llm_scorer.py**: LLM scoring implementation using OpenAI API

### `src/validation/`
- **validate_json.py**: JSON schema validation utilities

### `src/merge/`
- **merge_datasets.py**: Dataset merging utilities

### `src/analysis/`
- **models.py**: Statistical models (logistic, Cox, negative binomial)

### `src/utils/`
- **io.py**: I/O utilities for JSON, text, and table files
- **logging.py**: Centralized logging configuration

## Data Flow

1. **Raw data**: OSF JSON files → `data/raw/`
2. **Processed data**: Cleaned text files → `data/processed/`
3. **LLM scores**: Score JSON files → `data/scores_llm/`
4. **Human scores**: CSV/JSON files → `data/scores_human/`
5. **Merged dataset**: Final analysis dataset → `data/merged/`
6. **Analysis results**: Model summaries → `data/merged/analysis_results/`

## Requirements

- Python 3.8+
- OpenAI API key
- See `requirements.txt` for full dependency list

## License

[Add your license here]

