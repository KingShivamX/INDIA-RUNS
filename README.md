<div align="center">

# 🏆 INDIA RUNS — AI Resume Ranker v3

### Redrob Intelligent Candidate Discovery & Ranking Challenge

**Team spart**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-orange?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Offline](https://img.shields.io/badge/Runs-100%25%20Offline-green)](.)
[![Runtime](https://img.shields.io/badge/Runtime-~16s%20on%20CPU-brightgreen)](.)
[![Honeypots](https://img.shields.io/badge/Honeypot%20Rate-0%25-red)](.)

---

*A high-performance, fully-offline candidate ranking engine that processes*
*100,000 candidate profiles in ~16 seconds on a single CPU core.*

</div>

---

## 🎯 Why We Win

Most teams will submit a basic keyword matcher or a black-box LLM call. We built a **surgical, multi-axis scoring engine** that treats resume ranking like a real production ML system — with domain-specific heuristics, fraud detection, and behavioral intelligence.

| Feature | Us | Typical Team |
|---|---|---|
| Honeypot Detection | **3-layer** (temporal + duration + skill fraud) | Basic or none |
| Scoring Axes | **10 weighted axes** | 2–3 simple rules |
| Behavioral Signals | **10 platform signals** used | Ignored |
| JD Matching | **TF-IDF cosine similarity** | Keyword overlap |
| Career Analysis | **Trajectory + Stability + Domain depth** | Not considered |
| Education Scoring | **Tier-1/Tier-2 Indian college** mapping | Ignored |
| Company Intelligence | **100+ companies** classified | Small hardcoded list |
| Runtime | **~16 seconds** | Minutes to hours |
| Dependencies | **1 (scikit-learn)** | Heavy ML stacks |
| Network Required | **No (fully offline)** | Often yes |

---

## 🏗️ Architecture

```
candidates.jsonl (100K profiles)
        │
        ▼
┌──────────────────────┐
│  LAYER 1: FILTERING  │
├──────────────────────┤
│ • Honeypot Detection │ ──→ 127 caught (3 detection layers)
│ • Disqualification   │ ──→ 74,082 filtered (6 rules)
└──────────────────────┘
        │ 25,791 qualified
        ▼
┌──────────────────────┐
│  LAYER 2: SCORING    │
├──────────────────────┤
│ 10 weighted axes:    │
│ • Title Match    25% │
│ • Skills Match   15% │
│ • Experience     12% │
│ • Product Co.    12% │
│ • Location       10% │
│ • TF-IDF JD       8% │
│ • Education        5% │
│ • Trajectory       5% │
│ • Stability        5% │
│ • Domain Depth     3% │
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  LAYER 3: BEHAVIORAL │
│     MULTIPLIER       │
├──────────────────────┤
│ 10 signals (0.5x-1.4x) │
│ • Recruiter response │
│ • Activity recency   │
│ • Open-to-work flag  │
│ • Interview rate     │
│ • GitHub activity    │
│ • Offer acceptance   │
│ • Recruiter saves    │
│ • Profile complete   │
│ • Email verified     │
│ • LinkedIn connected │
└──────────────────────┘
        │
        ▼
   submission.csv (Top 100)
```

---

## 🔬 Deep Dive: What Makes Us Different

### 1. 3-Layer Honeypot Detection

We don't just match keywords — we cross-reference **real-world company founding dates** against candidate start dates, validate tenure durations against company lifespans, and detect impossible skill proficiency claims.

```
Layer 1: "Worked at Krutrim since 2019" → Krutrim founded 2023 → HONEYPOT
Layer 2: "15 years at CRED" → CRED is 8 years old → HONEYPOT
Layer 3: "Expert in 5 skills with 0 months usage" → HONEYPOT
```

**Result: 127 honeypots caught, 0% honeypot rate in top 100.**

### 2. Career Trajectory Scoring *(Unique to us)*

We analyze the **direction of career progression** across job history — not just the current title. A candidate who grew from Junior Engineer → ML Engineer → Senior ML Engineer scores higher than someone who stayed flat or moved laterally.

### 3. Job Stability Scoring *(Unique to us)*

Serial job-hoppers (multiple stints < 12 months) get penalized. Candidates with average tenures of 24+ months score highest. This is a real hiring signal that most teams ignore.

### 4. AI/ML Domain Depth *(Unique to us)*

We measure what **fraction of a candidate's career** was spent in AI/ML-specific roles vs. generic software engineering. A 7-year veteran with 5 years in ML roles scores higher than one with 6 years in backend + 1 year in ML.

### 5. Zero-Dependency DOCX Parser

Other teams will use `python-docx` and crash in the sandboxed evaluator. We parse the job description using only Python's built-in `zipfile` and `xml.etree.ElementTree` — **zero external dependencies** for document parsing.

### 6. 100+ Company Intelligence Database

We maintain a curated database of 100+ companies classified as product/startup companies — covering Indian unicorns (CRED, Razorpay, Zerodha, Sarvam AI) and global tech giants (Google, Meta, Stripe, Snowflake). This lets us score product-company experience far more accurately than a simple list.

---

## ⚡ Quick Start

```bash
# Install
pip install -r requirements.txt

# Run
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

See [RUN.md](RUN.md) for detailed instructions.

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Total Candidates Processed | 100,000 |
| Honeypots Detected | 127 |
| Disqualified | 74,082 |
| Qualified & Scored | 25,791 |
| Top-100 Output | ✅ Valid |
| Honeypot Rate in Top 100 | **0%** |
| Runtime | **~16 seconds** |
| #1 Ranked | Senior ML Engineer at Zomato, 7.2y exp |

---

## 📁 Project Structure

```
.
├── rank.py                    # Main ranking engine (single file, ~720 lines)
├── requirements.txt           # Dependencies (just scikit-learn)
├── submission_metadata.yaml   # Team info & methodology
├── submission.csv             # Generated output (gitignored)
├── RUN.md                     # How to run
├── README.md                  # This file
└── .gitignore                 # Clean repo config
```

---

## 👥 Team

| Member | Role | GitHub |
|--------|------|--------|
| **Shivam** | AI Lead Engineer | [@KingShivamX](https://github.com/KingShivamX) |
| **Sneh** | ML Engineer | [@sneh913](https://github.com/sneh913) |

---

<div align="center">

*Built with precision for the Redrob Hackathon.*

</div>
