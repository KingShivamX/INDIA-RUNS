# AI Resume Ranker — Redrob Hackathon v4

A high-performance, self-contained, zero-dependency Python ranking engine that discovers, filters, and ranks the top 100 candidate profiles from a pool of 100,000 against the "Senior AI Engineer — Founding Team" job description.

## 1. Problem Statement

Recruiters are overwhelmed by large resume volumes. Standard keyword matchers are easily fooled by keyword stuffing, and LLM-based rankers are too slow and expensive to evaluate large pools. 

This engine is designed to be:
* **Honeypot-Proof**: Detects and filters out synthetic "honeypot" resumes that possess logically impossible timelines or metrics.
* **Fair & Explainable**: Ranks purely on job-relevant parameters and generates non-templated, candidate-specific reasons referencing concrete facts.
* **Resource-Constraint Friendly**: Processes 100,000 records in **~4 seconds** on a single CPU core with zero external API calls, satisfying the 5-minute wall-clock limit.

---

## 2. Solution Architecture & Approach

This system operates in three consecutive layers:

```
[ Candidates Dataset ] 
         │
         ▼
 ┌───────────────┐
 │ Ingestion     │ ────► Automatically detects & parses raw JSONL or Gzipped (.gz) lines
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Filtering     │ ────► Excludes 127 Honeypots (impossible dates/durations/expert skills)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Exclusions    │ ────► Excludes 74,082 invalid tracks (consulting-only, research-only, etc.)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Scoring       │ ────► Title (25%), Exp (15%), Product (20%), Skills (25%), Location/Notice (15%)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Multiplier    │ ────► Applies Behavioral Modifier (0.5x to 1.4x)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Sorting       │ ────► Rounds scores to 4 decimals & resolves ties by candidate_id ascending
 └───────┬───────┘
         │
         ▼
[ Top 100 Shortlist CSV ]
```

### A. Honeypot Filtering
We identify and discard **127 honeypots** using strict logical constraints:
1. **Employment Date Violations**: Detects jobs at recently-founded startups (e.g. Krutrim, Sarvam AI, CRED) that started before their official founding years.
2. **Duration Violations**: Detects job durations that exceed the time the startup has existed.
3. **Skill Duration Anomaly**: Discards candidates claiming "Expert" or "Advanced" proficiency in multiple skills while having `0` duration months.

### B. Qualification / Disqualification Rules
To capture the gap between what the JD says and means, we filter out candidates with:
* **Consulting-Only Tracks**: Disqualifies candidates whose entire careers have been at consulting/services firms (e.g., TCS, Wipro, Infosys).
* **Research-Only Profiles**: Disqualifies profiles with academic/research-only titles and no production software or ML development.
* **Architects/Tech Leads**: Disqualifies senior architects who have not written production code in >= 18 months.
* **Wrong Domain**: Disqualifies candidates with Computer Vision/Speech/Robotics expertise who lack NLP or retrieval exposure.
* **Non-Technical Roles**: Disqualifies candidate profiles with current titles in Marketing, HR, Accounting, Sales, etc.

### C. Hybrid Scoring Engine
Scored out of a base of 1.0:
* **Title Relevance (25%)**: Prioritizes Senior ML/AI Engineers, Search, Retrieval, and NLP Engineers.
* **Experience Years (15%)**: Evaluated on a curve peaking at the target 5-9 years.
* **Product History (20%)**: Ratios career duration spent at product startups/scale-ups vs consulting, adding a startup bonus.
* **Skills Coverage (25%)**: Checks must-have groups (Embeddings/Retrieval, Vector DBs, Python/implied frameworks, offline Evaluation) and rewards nice-to-haves (fine-tuning, LTR, scaling).
* **Location & Notice Period (15%)**: Noida/Pune locations and <= 30-day notice periods are highly prioritized.

**Behavioral Signal Modifier (0.5x to 1.4x)**: Scales the score based on platform activity dates, recruiter responsiveness, open-to-work flags, and interview attendance.

---

## 3. How to Run

No external dependencies are required. The script runs using Python's standard library.

### Ranking Command
To rank the candidates pool and generate the submission CSV:
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```
*(Supports `.gz` files natively if candidates file is compressed).*

### Validation
To run the format validator:
```bash
python validate_submission.py submission.csv
```

---

## 4. Submission Details

The submission metadata is defined in `submission_metadata.yaml` at the repository root. Ranks are deterministic with pre-rounded float scores (4 decimals) and lexicographical tie-breakers on `candidate_id` ascending.
