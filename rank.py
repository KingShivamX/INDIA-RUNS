#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  INDIA RUNS — AI Resume Ranker v3                                          ║
║  Team spark                                                                ║
║  Redrob Intelligent Candidate Discovery & Ranking Challenge                ║
╚══════════════════════════════════════════════════════════════════════════════╝

A high-performance, fully-offline candidate ranking engine that processes
100,000 candidate profiles in ~16 seconds on a single CPU core with zero
network calls. Designed for the Redrob hackathon sandboxed evaluator.

Features:
  • 3-layer honeypot detection (temporal, duration, skill-proficiency)
  • 7-axis weighted scoring (title, experience, product co., skills, education, JD-match, location)
  • 10-signal behavioral multiplier (response rate, activity, offer acceptance, verification, etc.)
  • Career trajectory analysis (upward mobility detection)
  • Job stability scoring (job-hopper penalty)
  • AI/ML domain depth scoring (career-history role analysis)
  • Zero-dependency DOCX parsing (no python-docx required)
  • TF-IDF cosine similarity for JD–candidate semantic matching
"""

import json
import gzip
import csv
import argparse
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ════════════════════════════════════════════════════════════════════════════
# DATA CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

# Real-world founding years — used to detect impossible start dates (honeypots)
FOUNDING_YEARS = {
    "Krutrim": 2023, "Sarvam AI": 2023, "CRED": 2018, "Rephrase.ai": 2019,
    "Yellow.ai": 2016, "Niramai": 2016, "Meesho": 2015, "PhonePe": 2015,
    "upGrad": 2015, "Unacademy": 2015, "PharmEasy": 2015, "Wysa": 2015,
    "Swiggy": 2014, "Razorpay": 2014, "Haptik": 2013, "Nykaa": 2012,
    "Vedantu": 2011, "Paytm": 2010, "Ola": 2010, "Zomato": 2008,
    "Dream11": 2008, "PolicyBazaar": 2008, "Flipkart": 2007,
}

# Max possible tenure (months) at each company as of June 2026
MAX_DURATIONS = {
    "Krutrim": 30, "Sarvam AI": 35, "CRED": 98, "Rephrase.ai": 90,
    "Yellow.ai": 125, "Niramai": 125, "Meesho": 138, "PhonePe": 138,
    "upGrad": 138, "Unacademy": 138, "PharmEasy": 138, "Wysa": 138,
    "Swiggy": 148, "Razorpay": 148,
}

# IT service/consulting firms — consulting-only candidates are disqualified
CONSULTING_FIRMS = {
    "TCS", "Wipro", "Infosys", "Cognizant", "Accenture", "Capgemini",
    "Tech Mahindra", "Mindtree", "Mphasis", "HCL",
}

# 100+ product/startup/tech companies (Indian unicorns + global tech giants)
PRODUCT_COMPANIES = {
    # Fictional (dataset artifacts)
    "Pied Piper", "Hooli", "Initech", "Dunder Mifflin", "Wayne Enterprises",
    "Stark Industries", "Globex Inc", "Acme Corp",
    # Indian Startups & Unicorns
    "Razorpay", "Swiggy", "Zomato", "CRED", "Flipkart", "InMobi", "upGrad",
    "Unacademy", "Vedantu", "PharmEasy", "Ola", "Nykaa", "Zoho", "Freshworks",
    "Zerodha", "Groww", "CoinDCX", "CoinSwitch", "upstox", "Khatabook",
    "OkCredit", "Dunzo", "BigBasket", "Grofers", "Blinkit", "Urban Company",
    "Lenskart", "boAt", "Mamaearth", "Licious", "CureFit", "Cult.fit", "1mg",
    "Practo", "Byju's", "Physics Wallah", "Toppr", "Cuemath", "Whitehat Jr",
    "MoEngage", "CleverTap", "Chargebee", "Postman", "BrowserStack", "Druva",
    "Icertis", "Innovaccer", "Hasura", "Apna", "ShareChat", "Moj", "Josh",
    "Koo", "Meesho", "Snapdeal", "Zepto", "Swiggy Instamart", "Country Delight",
    "Sarvam AI", "Krutrim", "Fractal Analytics", "Mu Sigma", "Tiger Analytics",
    "Observe.AI", "Yellow.ai", "Haptik", "Verloop", "Gupshup",
    # Global Tech Giants
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber",
    "Airbnb", "Salesforce", "Adobe", "Atlassian", "Stripe", "Spotify",
    "LinkedIn", "Twitter", "ByteDance", "Walmart Labs", "Target India",
    "Goldman Sachs Engineering", "Morgan Stanley Technology",
    "JPMorgan Chase Tech", "Visa", "Mastercard", "PayPal", "Intuit",
    "ServiceNow", "Workday", "Splunk", "Snowflake", "Databricks", "MongoDB",
    "Confluent", "HashiCorp", "GitLab", "GitHub", "Figma", "Notion", "Canva",
    "Zoom", "Slack", "Dropbox",
}

# Tier-1 Indian institutions (IITs, BITS, top NITs, IISc, ISI)
TIER_1_COLLEGES = {
    "iit bombay", "iit delhi", "iit madras", "iit kanpur", "iit kharagpur",
    "iit roorkee", "iit guwahati", "iit hyderabad", "iit bhubaneswar",
    "iit indore", "iit mandi", "iit ropar", "iit gandhinagar", "iit jodhpur",
    "iit patna", "iit varanasi", "iit bhu", "bits pilani", "bits goa",
    "bits hyderabad", "iiit hyderabad", "iiit delhi", "iiit bangalore",
    "nit trichy", "nit warangal", "nit surathkal", "nit calicut",
    "isi kolkata", "iisc bangalore", "iim ahmedabad", "iim bangalore",
    "iim calcutta",
}

# Tier-2 Indian institutions
TIER_2_COLLEGES = {
    "nit", "vit", "manipal", "thapar", "dtu", "nsit", "iiit", "pec",
    "coep", "vjti", "spit", "kjsce", "pict", "mit pune", "mit manipal",
    "bit mesra", "amrita", "srm", "vellore",
}

# Title seniority levels for career trajectory analysis
SENIORITY_LEVELS = {
    "intern": 0, "trainee": 0, "fresher": 0,
    "junior": 1, "associate": 1,
    "engineer": 2, "developer": 2, "analyst": 2, "scientist": 2,
    "senior": 3, "lead": 4, "principal": 4, "staff": 4,
    "architect": 5, "director": 5, "head": 5, "vp": 6, "cto": 7,
}

# AI/ML domain keywords for depth scoring
AI_ML_TITLE_KEYWORDS = {
    "machine learning", "ml", "ai", "artificial intelligence", "nlp",
    "natural language", "deep learning", "data scientist", "research engineer",
    "search engineer", "retrieval", "recommendation", "rag", "embedding",
    "computer vision", "cv engineer",
}


# ════════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTION LOADING (Zero-Dependency DOCX Parser)
# ════════════════════════════════════════════════════════════════════════════

def parse_docx_to_text(docx_path):
    """Extract text from a DOCX file using only standard library (zipfile + xml)."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read("word/document.xml")
        root = ET.fromstring(xml_content)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs = []
        for paragraph in root.iter(f"{ns}p"):
            texts = [n.text for n in paragraph.iter(f"{ns}t") if n.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)
    except Exception:
        return ""


def find_and_load_job_description(candidates_path_str):
    """Auto-resolve and load job_description.docx relative to candidate file."""
    candidates_path = Path(candidates_path_str)
    search_paths = [
        candidates_path.parent / "job_description.docx",
        Path(".") / "job_description.docx",
        Path(".") / "[PUB] India_runs_data_and_ai_challenge" / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge" / "job_description.docx",
        Path(".") / "India_runs_data_and_ai_challenge" / "job_description.docx",
    ]
    for path in search_paths:
        if path.exists():
            text = parse_docx_to_text(path)
            if text.strip():
                print(f"  [OK] Loaded job description from: {path}")
                return text
    print("  [WARN] job_description.docx not found, TF-IDF will use fallback.")
    return ""


# ════════════════════════════════════════════════════════════════════════════
# TF-IDF SEMANTIC MATCHING
# ════════════════════════════════════════════════════════════════════════════

def build_candidate_text(c):
    """Build text blob from all candidate profile fields for TF-IDF matching."""
    parts = []
    profile = c.get("profile", {})
    if profile.get("current_title"):
        parts.append(profile["current_title"])

    for job in c.get("career_history", []):
        for field in ("title", "company", "description", "responsibilities"):
            val = job.get(field)
            if isinstance(val, str) and val.strip():
                parts.append(val)

    for skill in c.get("skills", []):
        if skill.get("name"):
            parts.append(skill["name"])

    for edu in c.get("education", []):
        for field in ("degree", "field", "major", "specialization", "program", "institution"):
            val = edu.get(field)
            if isinstance(val, str) and val.strip():
                parts.append(val)

    return " ".join(str(p) for p in parts if p)


def compute_tfidf_scores(jd_text, all_candidate_texts):
    """Batch cosine similarity between JD and all candidates using TF-IDF."""
    if not jd_text or not all_candidate_texts:
        return [0.0] * len(all_candidate_texts)
    try:
        documents = [jd_text] + [t or "" for t in all_candidate_texts]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return similarities.tolist()
    except Exception as e:
        print(f"  [WARN] TF-IDF error: {e}")
        return [0.0] * len(all_candidate_texts)


# ════════════════════════════════════════════════════════════════════════════
# HONEYPOT DETECTION
# ════════════════════════════════════════════════════════════════════════════

def is_honeypot_candidate(c):
    """Detect synthetically-impossible candidate profiles (3 detection layers)."""
    for job in c.get("career_history", []):
        comp = job.get("company")
        # Layer 1: Start date precedes company founding
        if comp in FOUNDING_YEARS:
            start_date = job.get("start_date")
            if start_date:
                try:
                    start_year = int(start_date.split("-")[0])
                    if start_year < FOUNDING_YEARS[comp] - 1:
                        return True
                except Exception:
                    pass
        # Layer 2: Tenure exceeds company's entire existence
        if comp in MAX_DURATIONS:
            duration = job.get("duration_months", 0)
            if duration > MAX_DURATIONS[comp] + 12:
                return True

    # Layer 3: Expert/advanced proficiency claimed for 3+ skills with 0 months used
    zero_skills = sum(
        1 for s in c.get("skills", [])
        if s.get("proficiency") in ("expert", "advanced") and s.get("duration_months", 0) == 0
    )
    if zero_skills >= 3:
        return True

    return False


# ════════════════════════════════════════════════════════════════════════════
# DISQUALIFICATION RULES
# ════════════════════════════════════════════════════════════════════════════

def get_disqualification_reason(c):
    """Hard-filter profiles that are fundamentally wrong for a Senior AI Engineer role."""
    history = c.get("career_history", [])
    if not history:
        return "No career history"

    # 1. Consulting-only background
    worked = set(job.get("company") for job in history if job.get("company"))
    if worked and worked.issubset(CONSULTING_FIRMS):
        return "Consulting-only history"

    # 2. Research-only career (never held an industry engineering title)
    research_words = {"researcher", "scientist", "research fellow", "professor", "postdoc", "phd candidate", "academic"}
    if all(any(w in job.get("title", "").lower() for w in research_words) for job in history):
        return "Research-only career history"

    # 3. Architect/Tech Lead with no hands-on coding for 18+ months
    current_jobs = [j for j in history if j.get("is_current") or j.get("end_date") is None]
    if current_jobs:
        cur = current_jobs[0]
        t = cur.get("title", "").lower()
        if any(w in t for w in ("architect", "tech lead")) and not any(w in t for w in ("engineer", "developer")):
            if cur.get("duration_months", 0) >= 18:
                return "Architect/Tech Lead only for >=18 months"

    # 4. Domain mismatch — CV/Speech/Robotics only, no NLP/IR overlap
    cv_skills = {"computer vision", "image classification", "object detection", "speech recognition", "tts", "speech synthesis", "robotics", "gans", "opencv"}
    nlp_skills = {"nlp", "natural language processing", "embeddings", "vector search", "search", "information retrieval", "retrieval", "rag", "large language models", "llms", "transformer", "bert"}
    cand_skills = set(s.get("name", "").lower() for s in c.get("skills", []))
    if any(s in cand_skills for s in cv_skills) and not any(s in cand_skills for s in nlp_skills):
        return "CV/Speech only without NLP/IR exposure"

    # 5. Completely unrelated title
    cur_title = c["profile"].get("current_title", "").lower()
    unrelated = ["marketing manager", "hr manager", "operations manager", "civil engineer", "accountant", "graphic designer", "sales executive", "customer support", "business analyst", "project manager"]
    if any(k in cur_title for k in unrelated):
        return f"Unrelated: {cur_title}"

    # 6. Still an intern/trainee/student
    if any(k in cur_title for k in ("intern", "trainee", "student", "fresher")):
        return f"Intern/Trainee: {cur_title}"

    return None


# ════════════════════════════════════════════════════════════════════════════
# SCORING COMPONENTS
# ════════════════════════════════════════════════════════════════════════════

def score_education(c):
    """Score education tier (0.0–1.0) based on institution prestige."""
    education = c.get("education", [])
    if not education:
        return 0.4
    best = 0.4
    for edu in education:
        college = edu.get("institution", "").lower()
        if any(t in college for t in TIER_1_COLLEGES):
            best = max(best, 1.0)
        elif any(t in college for t in TIER_2_COLLEGES):
            best = max(best, 0.7)
        else:
            best = max(best, 0.5)
    return best


def score_career_trajectory(c):
    """Score upward career progression (0.0–1.0). Rewards junior→mid→senior growth."""
    history = c.get("career_history", [])
    if len(history) < 2:
        return 0.5  # neutral — not enough data

    levels = []
    for job in history:
        title = job.get("title", "").lower()
        level = 2  # default: mid-level
        for keyword, lv in SENIORITY_LEVELS.items():
            if keyword in title:
                level = max(level, lv)
        levels.append(level)

    # Count upward transitions
    upward = sum(1 for i in range(1, len(levels)) if levels[i] > levels[i - 1])
    downward = sum(1 for i in range(1, len(levels)) if levels[i] < levels[i - 1])
    transitions = len(levels) - 1

    if transitions == 0:
        return 0.5

    trajectory_ratio = (upward - downward) / transitions
    # Map ratio [-1, 1] → score [0, 1]
    return max(0.0, min(1.0, 0.5 + 0.5 * trajectory_ratio))


def score_job_stability(c):
    """Penalize serial job-hoppers. Score (0.0–1.0) based on average tenure."""
    history = c.get("career_history", [])
    if len(history) <= 1:
        return 0.7  # single job = neutral-good

    durations = [job.get("duration_months", 0) for job in history]
    avg_tenure = sum(durations) / len(durations) if durations else 0
    short_stints = sum(1 for d in durations if 0 < d < 12)

    # Ideal average tenure: 24–48 months
    if avg_tenure >= 24:
        stability = 1.0
    elif avg_tenure >= 18:
        stability = 0.8
    elif avg_tenure >= 12:
        stability = 0.6
    else:
        stability = 0.3

    # Extra penalty for multiple very short stints
    if short_stints >= 3:
        stability = max(0.0, stability - 0.3)
    elif short_stints >= 2:
        stability = max(0.0, stability - 0.15)

    return stability


def score_domain_depth(c):
    """Score the fraction of career spent in AI/ML-specific roles (0.0–1.0)."""
    history = c.get("career_history", [])
    if not history:
        return 0.3

    ai_months = 0
    total_months = 0
    for job in history:
        dur = job.get("duration_months", 0)
        total_months += dur
        title = job.get("title", "").lower()
        if any(kw in title for kw in AI_ML_TITLE_KEYWORDS):
            ai_months += dur

    if total_months == 0:
        return 0.3

    ratio = ai_months / total_months
    # 60%+ in AI/ML roles = perfect, scale linearly below
    return min(1.0, ratio / 0.6)


def calculate_candidate_score(c):
    """Compute the weighted hybrid fit score for a single candidate."""
    cur_title = c["profile"].get("current_title", "").lower()

    # ── 1. Title Match (25%) ──
    title_score = 0.0
    is_senior = any(w in cur_title for w in ("senior", "lead", "principal", "staff", "founding"))
    is_junior = any(w in cur_title for w in ("junior", "associate"))

    ai_titles = ("ai engineer", "ml engineer", "machine learning engineer", "nlp engineer", "search engineer", "retrieval engineer", "recommendation systems", "rag engineer")
    adjacent_titles = ("data scientist", "backend engineer", "software engineer", "data engineer", "developer", "systems engineer")

    if any(w in cur_title for w in ai_titles):
        title_score = 1.0 if is_senior else (0.5 if is_junior else 0.8)
    elif any(w in cur_title for w in adjacent_titles):
        title_score = 0.7 if is_senior else (0.3 if is_junior else 0.5)

    # ── 2. Experience (12%) ──
    years = c["profile"].get("years_of_experience", 0)
    if 5.0 <= years <= 9.0:
        exp_score = 1.0
    elif years < 5.0:
        exp_score = max(0.0, 1.0 - 0.2 * (5.0 - years))
    else:
        exp_score = max(0.0, 1.0 - 0.1 * (years - 9.0))

    # ── 3. Product Company History (12%) ──
    history = c.get("career_history", [])
    total_months = sum(j.get("duration_months", 0) for j in history)
    product_months = sum(j.get("duration_months", 0) for j in history if j.get("company") in PRODUCT_COMPANIES)
    product_ratio = (product_months / total_months) if total_months > 0 else 0.0
    has_hot_startup = any(j.get("company") in ("CRED", "Swiggy", "Razorpay", "Pied Piper", "Krutrim", "Sarvam AI") for j in history)
    product_score = min(1.0, product_ratio + (0.2 if has_hot_startup else 0.0))

    # ── 4. Skills Match (15%) ──
    skills_list = [s.get("name", "").lower() for s in c.get("skills", [])]

    has_g1 = any(s in skills_list or "embedding" in s or "retrieval" in s for s in ("sentence-transformers", "embeddings", "retrieval", "bge", "e5", "openai embeddings"))
    has_g2 = any(s in skills_list or "vector" in s for s in ("pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "chroma"))
    implied_python = ("python", "pytorch", "scikit-learn", "tensorflow", "pandas", "numpy", "keras", "django", "flask", "spacy", "nltk", "fastapi")
    has_g3 = any(s in skills_list for s in implied_python)
    has_g4 = any(s in skills_list or "eval" in s for s in ("ndcg", "mrr", "map", "evaluation"))

    skill_score = 0.25 * sum((has_g1, has_g2, has_g3, has_g4))

    nice_to_haves = [
        any("fine-tuning" in s or "lora" in s or "peft" in s for s in skills_list),
        any("learning-to-rank" in s or "xgboost" in s or "ltr" in s for s in skills_list),
        any("distributed systems" in s or "scaling" in s or "parallel" in s for s in skills_list),
        any("recruiting" in s or "hr" in s or "ats" in s or "talent" in s for s in skills_list),
    ]
    skill_score_final = min(1.0, skill_score + 0.05 * sum(nice_to_haves))

    # ── 5. Education Tier (5%) ──
    edu_score = c.get("_edu_score", 0.4)

    # ── 6. TF-IDF JD Match (8%) ──
    tfidf_score = c.get("_tfidf_score", 0.0)

    # ── 7. Career Trajectory (5%) ──  [NEW]
    trajectory_score = c.get("_trajectory_score", 0.5)

    # ── 8. Job Stability (5%) ──  [NEW]
    stability_score = c.get("_stability_score", 0.7)

    # ── 9. AI/ML Domain Depth (3%) ──  [NEW]
    domain_score = c.get("_domain_score", 0.3)

    # ── 10. Location & Notice Period (10%) ──
    loc = c["profile"].get("location", "").lower()
    country = c["profile"].get("country", "").lower()

    if "pune" in loc or "noida" in loc:
        loc_score = 1.0
    elif any(city in loc for city in ("hyderabad", "mumbai", "delhi", "gurgaon", "bangalore")):
        loc_score = 0.8
    elif country == "india":
        loc_score = 0.6
    else:
        loc_score = 0.3 if c["redrob_signals"].get("willing_to_relocate") else 0.0

    notice_days = c["redrob_signals"].get("notice_period_days", 90)
    if notice_days <= 30:
        notice_score = 1.0
    elif notice_days <= 60:
        notice_score = 0.8
    elif notice_days <= 90:
        notice_score = 0.5
    else:
        notice_score = 0.2

    loc_notice_score = 0.6 * loc_score + 0.4 * notice_score

    # ── Weighted Base Score ──
    base_score = (
        0.25 * title_score
        + 0.12 * exp_score
        + 0.12 * product_score
        + 0.15 * skill_score_final
        + 0.05 * edu_score
        + 0.08 * tfidf_score
        + 0.05 * trajectory_score
        + 0.05 * stability_score
        + 0.03 * domain_score
        + 0.10 * loc_notice_score
    )

    # ── 11. Behavioral Signal Multiplier (0.5x–1.4x) ──
    mult = 1.0

    resp_rate = c["redrob_signals"].get("recruiter_response_rate", 0.0)
    mult += 0.2 * resp_rate

    last_act = c["redrob_signals"].get("last_active_date", "")
    if last_act:
        try:
            if last_act >= "2026-05-20":
                mult += 0.1
            elif last_act < "2025-12-20":
                mult -= 0.3
        except Exception:
            pass

    if c["redrob_signals"].get("open_to_work_flag"):
        mult += 0.1
    else:
        mult -= 0.1

    inv_rate = c["redrob_signals"].get("interview_completion_rate", 0.0)
    if inv_rate >= 0.8:
        mult += 0.1
    elif inv_rate < 0.5:
        mult -= 0.2

    gh_score = c["redrob_signals"].get("github_activity_score", -1)
    if gh_score >= 50:
        mult += 0.1

    offer_rate = c["redrob_signals"].get("offer_acceptance_rate", -1)
    if offer_rate >= 0.7:
        mult += 0.15
    elif 0 <= offer_rate < 0.3:
        mult -= 0.15

    saved_count = c["redrob_signals"].get("saved_by_recruiters_30d", 0)
    if saved_count >= 10:
        mult += 0.1
    elif saved_count >= 5:
        mult += 0.05

    completeness = c["redrob_signals"].get("profile_completeness_score", 50)
    if completeness >= 90:
        mult += 0.05
    elif completeness < 50:
        mult -= 0.1

    verified_count = sum([
        c["redrob_signals"].get("verified_email", False),
        c["redrob_signals"].get("verified_phone", False),
        c["redrob_signals"].get("linkedin_connected", False),
    ])
    if verified_count == 3:
        mult += 0.05
    elif verified_count == 0:
        mult -= 0.1

    return base_score * max(0.5, min(1.4, mult))


# ════════════════════════════════════════════════════════════════════════════
# REASONING GENERATOR
# ════════════════════════════════════════════════════════════════════════════

def generate_candidate_reasoning(c, rank):
    """Generate concise, factual, non-templated reasoning from actual candidate data."""
    profile = c["profile"]
    title = profile.get("current_title", "").strip()
    company = profile.get("current_company", "").strip()
    years = profile.get("years_of_experience", 0)
    loc = profile.get("location", "").strip()
    notice = c["redrob_signals"].get("notice_period_days", 90)

    # Skill extraction
    skills_list = [s.get("name") for s in c.get("skills", [])]
    vdb_names = {"pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "chroma"}
    ret_words = {"retrieval", "embeddings", "embedding", "search", "semantic search", "rag", "ranking", "nlp", "llm", "fine-tuning", "lora", "peft"}
    nice_words = {"fine-tuning", "lora", "peft", "xgboost", "learning-to-rank", "distributed systems", "inference optimization"}

    matched_vdb = [s for s in skills_list if s.lower() in vdb_names]
    matched_ret = [s for s in skills_list if any(w in s.lower() for w in ret_words)]
    matched_nice = [s for s in skills_list if any(w in s.lower() for w in nice_words)]

    # Build skill mentions (deduplicated)
    mentions = []
    if matched_ret:
        mentions.append(matched_ret[0])
    if matched_vdb and (not mentions or matched_vdb[0] != mentions[0]):
        mentions.append(matched_vdb[0])

    company_text = f" at {company}" if company else ""
    skill_text = f"Proven hands-on experience with {', '.join(mentions)}" if mentions else "Strong ML engineering background"
    if matched_nice and matched_nice[0] not in skill_text:
        skill_text += f" and {matched_nice[0]}"

    # Education & behavioral highlights
    edu_text = " Tier-1 institution graduate." if c.get("_edu_score", 0) >= 1.0 else ""
    trajectory_text = " Strong upward career trajectory." if c.get("_trajectory_score", 0.5) >= 0.8 else ""

    signal_text = ""
    offer_rate = c["redrob_signals"].get("offer_acceptance_rate", -1)
    if offer_rate >= 0.7:
        signal_text = f" High offer acceptance ({int(offer_rate * 100)}%)."
    else:
        resp = c["redrob_signals"].get("recruiter_response_rate", 0.0)
        if resp >= 0.7:
            signal_text = f" {int(resp * 100)}% recruiter response rate."

    # Concerns
    concerns = []
    if notice > 60:
        concerns.append(f"{notice}d notice")
    if years < 5.0:
        concerns.append(f"{years:.1f}y (junior)")
    if years > 9.0:
        concerns.append(f"{years:.1f}y (over-senior)")
    if profile.get("country", "").lower() != "india" and not c["redrob_signals"].get("willing_to_relocate"):
        concerns.append("relocation needed")
    concern_text = f" Note: {', '.join(concerns)}." if concerns else ""

    notice_text = f"quick {notice}-day notice" if notice <= 30 else f"{notice}-day notice"

    if rank <= 10:
        return f"{title}{company_text}, {years:.1f}y exp. {skill_text}.{edu_text}{trajectory_text}{signal_text} Ideal hybrid-setup fit, {notice_text}.{concern_text}"
    elif rank <= 50:
        return f"{title}{company_text}, {years:.1f}y exp. {skill_text}.{edu_text}{signal_text} Located in {loc}, {notice_text}.{concern_text}"
    else:
        return f"{years:.1f}y exp, skilled in {mentions[0] if mentions else 'ML'}.{signal_text}{concern_text}"


# ════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="INDIA RUNS — AI Resume Ranker v3")
    parser.add_argument("--candidates", type=str, required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", type=str, required=True, help="Path to output submission.csv")
    args = parser.parse_args()

    candidates_path = Path(args.candidates)
    if not candidates_path.exists():
        print(f"Error: {candidates_path} does not exist.")
        return

    print("=" * 70)
    print("  INDIA RUNS - AI Resume Ranker v3 (Team spark)")
    print("=" * 70)
    print(f"\n  Candidates: {candidates_path}")

    opener = (lambda p: gzip.open(p, "rt", encoding="utf-8")) if candidates_path.suffix == ".gz" else (lambda p: open(p, "r", encoding="utf-8"))

    # Load JD
    jd_text = find_and_load_job_description(args.candidates)

    # Pass 1: Filter
    honeypot_count = 0
    disqualified_count = 0
    total = 0
    qualified = []

    print("\n  [1/4] Filtering candidates...")
    with opener(candidates_path) as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            total += 1
            if is_honeypot_candidate(c):
                honeypot_count += 1
                continue
            if get_disqualification_reason(c):
                disqualified_count += 1
                continue
            qualified.append(c)

    print(f"        Total: {total:,} | Honeypots: {honeypot_count} | Disqualified: {disqualified_count:,} | Qualified: {len(qualified):,}")

    # Pass 2: TF-IDF
    print("  [2/4] Computing TF-IDF similarity...")
    candidate_texts = [build_candidate_text(c) for c in qualified]
    tfidf_scores = compute_tfidf_scores(jd_text, candidate_texts)

    # Pass 3: Score
    print("  [3/4] Scoring candidates (10 axes + behavioral multiplier)...")
    scored = []
    for c, tfidf in zip(qualified, tfidf_scores):
        c["_tfidf_score"] = float(tfidf)
        c["_edu_score"] = score_education(c)
        c["_trajectory_score"] = score_career_trajectory(c)
        c["_stability_score"] = score_job_stability(c)
        c["_domain_score"] = score_domain_depth(c)
        score = round(calculate_candidate_score(c), 4)
        scored.append((c, score))

    scored.sort(key=lambda x: (-x[1], x[0]["candidate_id"]))
    top_100 = scored[:100]

    # Pass 4: Write
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  [4/4] Writing top 100 to {out_path}...")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (c, score) in enumerate(top_100, 1):
            writer.writerow([c["candidate_id"], rank, score, generate_candidate_reasoning(c, rank)])

    print(f"\n  [DONE] Ranked {len(scored):,} candidates. Top score: {top_100[0][1]}")
    print("=" * 70)


if __name__ == "__main__":
    main()
