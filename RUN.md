# 🏃 How to Run

## Prerequisites

- Python 3.9+
- `pip install scikit-learn`

## Quick Start

```bash
# Install dependency
pip install -r requirements.txt

# Run the ranker
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

## Arguments

| Flag | Description |
|------|-------------|
| `--candidates` | Path to `candidates.jsonl` or `candidates.jsonl.gz` |
| `--out` | Path to output CSV file |

## Examples

```bash
# With raw JSONL
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv

# With gzipped JSONL
python rank.py --candidates ./data/candidates.jsonl.gz --out ./submission.csv
```

## Expected Output

```
======================================================================
  INDIA RUNS — AI Resume Ranker v3 (Team Antigravity × Sneh)
======================================================================

  Candidates: ./candidates.jsonl
  ✓ Loaded job description from: ./job_description.docx

  [1/4] Filtering candidates...
        Total: 100,000 | Honeypots: 127 | Disqualified: 74,082 | Qualified: 25,791
  [2/4] Computing TF-IDF similarity...
  [3/4] Scoring candidates (10 axes + behavioral multiplier)...
  [4/4] Writing top 100 to ./submission.csv...

  ✅ Done! Ranked 25,791 candidates. Top score: 1.3231
======================================================================
```

## Notes

- **Runtime**: ~16 seconds on a standard CPU (no GPU needed)
- **Offline**: Zero network calls — runs fully air-gapped
- **JD Auto-Discovery**: Automatically finds `job_description.docx` next to the candidates file
- **Format**: Output CSV has columns: `candidate_id, rank, score, reasoning`
