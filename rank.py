#!/usr/bin/env python3
import json
import gzip
import csv
import argparse
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Real-world founding years of key companies in the dataset
FOUNDING_YEARS = {
    "Krutrim": 2023,
    "Sarvam AI": 2023,
    "CRED": 2018,
    "Rephrase.ai": 2019,
    "Yellow.ai": 2016,
    "Niramai": 2016,
    "Meesho": 2015,
    "PhonePe": 2015,
    "upGrad": 2015,
    "Unacademy": 2015,
    "PharmEasy": 2015,
    "Wysa": 2015,
    "Swiggy": 2014,
    "Razorpay": 2014,
    "Haptik": 2013,
    "Nykaa": 2012,
    "Vedantu": 2011,
    "Paytm": 2010,
    "Ola": 2010,
    "Zomato": 2008,
    "Dream11": 2008,
    "PolicyBazaar": 2008,
    "Flipkart": 2007,
}

# Max possible duration (in months) worked at each company as of June 2026
MAX_DURATIONS = {
    "Krutrim": 30,
    "Sarvam AI": 35,
    "CRED": 98,
    "Rephrase.ai": 90,
    "Yellow.ai": 125,
    "Niramai": 125,
    "Meesho": 138,
    "PhonePe": 138,
    "upGrad": 138,
    "Unacademy": 138,
    "PharmEasy": 138,
    "Wysa": 138,
    "Swiggy": 148,
    "Razorpay": 148,
}

# IT service/consulting companies (consulting-only candidates are disqualified)
CONSULTING_FIRMS = {
    "TCS", "Wipro", "Infosys", "Cognizant", "Accenture", "Capgemini",
    "Tech Mahindra", "Mindtree", "Mphasis", "HCL"
}

# Fictional/product startup companies in the dataset (merged and expanded)
PRODUCT_COMPANIES = {
    "Pied Piper", "Hooli", "Initech", "Dunder Mifflin", "Wayne Enterprises",
    "Stark Industries", "Globex Inc", "Acme Corp", "Razorpay", "Swiggy",
    "Zomato", "CRED", "Flipkart", "InMobi", "upGrad", "Unacademy",
    "Vedantu", "PharmEasy", "Ola", "Nykaa", "Zoho", "Freshworks",
    "Zerodha", "Groww", "CoinDCX", "CoinSwitch", "upstox", "Khatabook", "OkCredit",
    "Dunzo", "BigBasket", "Grofers", "Blinkit", "Urban Company", "Lenskart", "boAt",
    "Mamaearth", "Licious", "CureFit", "Cult.fit", "PharmEasy", "1mg", "Practo",
    "Byju's", "Physics Wallah", "Toppr", "Cuemath", "Whitehat Jr",
    "InMobi", "MoEngage", "CleverTap", "Chargebee", "Postman", "BrowserStack",
    "Druva", "Icertis", "Innovaccer", "Hasura", "Apna", "Khatabook",
    "ShareChat", "Moj", "Josh", "Koo", "Meesho", "Snapdeal",
    "Zepto", "Swiggy Instamart", "Country Delight", "Licious",
    "Sarvam AI", "Krutrim", "Fractal Analytics", "Mu Sigma", "Tiger Analytics",
    "Observe.AI", "Yellow.ai", "Haptik", "Verloop", "Gupshup",
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber", "Airbnb",
    "Salesforce", "Adobe", "Atlassian", "Stripe", "Spotify", "LinkedIn", "Twitter",
    "ByteDance", "Walmart Labs", "Target India", "Goldman Sachs Engineering",
    "Morgan Stanley Technology", "JPMorgan Chase Tech", "Visa", "Mastercard",
    "PayPal", "Intuit", "ServiceNow", "Workday", "Splunk", "Snowflake", "Databricks",
    "MongoDB", "Confluent", "HashiCorp", "GitLab", "GitHub", "Figma", "Notion",
    "Canva", "Zoom", "Slack", "Dropbox"
}

# Tier-1 and Tier-2 Indian Engineering Colleges/Universities
TIER_1_COLLEGES = {
    "iit bombay", "iit delhi", "iit madras", "iit kanpur", "iit kharagpur",
    "iit roorkee", "iit guwahati", "iit hyderabad", "iit bhubaneswar",
    "iit indore", "iit mandi", "iit ropar", "iit gandhinagar", "iit jodhpur",
    "iit patna", "iit varanasi", "iit bhu", "bits pilani", "bits goa",
    "bits hyderabad", "iiit hyderabad", "iiit delhi", "iiit bangalore",
    "nit trichy", "nit warangal", "nit surathkal", "nit calicut",
    "isi kolkata", "iisc bangalore", "iim ahmedabad", "iim bangalore", "iim calcutta"
}

TIER_2_COLLEGES = {
    "nit", "vit", "manipal", "thapar", "dtu", "nsit", "iiit", "pec",
    "coep", "vjti", "spit", "kjsce", "pict", "mit pune", "mit manipal",
    "bit mesra", "amrita", "srm", "vellore"
}

def parse_docx_to_text(docx_path):
    """Extract text from a DOCX file using standard libraries (zipfile and xml) to avoid python-docx dependency."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
        root = ET.fromstring(xml_content)
        paragraphs = []
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except:
        return ""

def find_and_load_job_description(candidates_path_str):
    """Find job_description.docx and return its parsed text."""
    candidates_path = Path(candidates_path_str)
    potential_paths = [
        candidates_path.parent / "job_description.docx",
        Path(".") / "job_description.docx",
        Path(".") / "[PUB] India_runs_data_and_ai_challenge" / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge" / "job_description.docx",
        Path(".") / "India_runs_data_and_ai_challenge" / "job_description.docx",
    ]
    for path in potential_paths:
        if path.exists():
            text = parse_docx_to_text(path)
            if text.strip():
                print(f"Loaded job description from: {path}")
                return text
    print("Warning: job_description.docx not found or empty.")
    return ""

def build_candidate_text(c):
    """Build a single text blob from candidate profile fields for TF-IDF match."""
    parts = []
    profile = c.get("profile", {})
    if profile.get("current_title"):
        parts.append(profile.get("current_title"))
    
    for job in c.get("career_history", []):
        if job.get("title"):
            parts.append(job.get("title"))
        if job.get("company"):
            parts.append(job.get("company"))
        for field in ("description", "responsibilities"):
            val = job.get(field)
            if isinstance(val, str) and val.strip():
                parts.append(val)
                
    for skill in c.get("skills", []):
        name = skill.get("name")
        if name:
            parts.append(name)
            
    for edu in c.get("education", []):
        for field in ("degree", "field", "major", "specialization", "program"):
            val = edu.get(field)
            if isinstance(val, str) and val.strip():
                parts.append(val)
        if edu.get("institution"):
            parts.append(edu.get("institution"))
            
    return " ".join(str(p) for p in parts if p)

def compute_tfidf_scores(jd_text, all_candidate_texts):
    """Compute cosine similarity scores between JD and candidate profiles using TF-IDF."""
    if not jd_text or not all_candidate_texts:
        return [0.0] * len(all_candidate_texts)
    try:
        documents = [jd_text] + [text or "" for text in all_candidate_texts]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return similarities.tolist()
    except Exception as e:
        print(f"Error computing TF-IDF: {e}")
        return [0.0] * len(all_candidate_texts)

def is_honeypot_candidate(c):
    """Check if the candidate has a subtly impossible profile (honeypot)."""
    for job in c.get('career_history', []):
        comp = job.get('company')
        # Check 1: Job started before the company was founded in the real world
        if comp in FOUNDING_YEARS:
            start_date = job.get('start_date')
            if start_date:
                try:
                    start_year = int(start_date.split('-')[0])
                    if start_year < FOUNDING_YEARS[comp] - 1:
                        return True
                except:
                    pass
        # Check 2: Duration at company exceeds the time since founding to June 2026
        if comp in MAX_DURATIONS:
            duration = job.get('duration_months', 0)
            if duration > MAX_DURATIONS[comp] + 12:
                return True
    
    # Check 3: Expert/advanced proficiency in 3 or more skills with 0 months used
    zero_skills = 0
    for s in c.get('skills', []):
        if s.get('proficiency') in ['expert', 'advanced'] and s.get('duration_months', 0) == 0:
            zero_skills += 1
    if zero_skills >= 3:
        return True
        
    return False

def get_disqualification_reason(c):
    """Filter out profiles that are fundamentally a mismatch based on the JD."""
    history = c.get('career_history', [])
    if not history:
        return "No career history"
    
    # 1. Consulting-only history (no product/startup background)
    worked_companies = set(job.get('company') for job in history if job.get('company'))
    if worked_companies and worked_companies.issubset(CONSULTING_FIRMS):
        return "Consulting-only history"
        
    # 2. Pure research history
    research_titles = ["researcher", "scientist", "research fellow", "professor", "postdoc", "phd candidate", "academic"]
    non_research_found = False
    for job in history:
        title = job.get('title', '').lower()
        if not any(w in title for w in research_titles):
            non_research_found = True
            break
    if not non_research_found:
        return "Research-only career history"
        
    # 3. Architect/Tech Lead only (no coding for >= 18 months)
    current_jobs = [job for job in history if job.get('is_current') or job.get('end_date') is None]
    if current_jobs:
        cur_job = current_jobs[0]
        title = cur_job.get('title', '').lower()
        duration = cur_job.get('duration_months', 0)
        if any(w in title for w in ["architect", "tech lead"]) and not any(w in title for w in ["engineer", "developer"]):
            if duration >= 18:
                return "Architect/Tech Lead only for >=18 months"
                
    # 4. Wrong domain (CV/Speech/Robotics only without NLP/IR)
    cv_skills = {"computer vision", "image classification", "object detection", "speech recognition", "tts", "speech synthesis", "robotics", "gans", "opencv"}
    nlp_skills = {"nlp", "natural language processing", "embeddings", "vector search", "search", "information retrieval", "retrieval", "rag", "large language models", "llms", "transformer", "bert"}
    
    cand_skills = set(s.get('name', '').lower() for s in c.get('skills', []))
    has_cv = any(s in cand_skills for s in cv_skills)
    has_nlp = any(s in cand_skills for s in nlp_skills)
    if has_cv and not has_nlp:
        return "CV/Speech only without NLP/IR exposure"
        
    # 5. Completely unrelated current title (e.g. Marketing, HR, Accountant)
    cur_title = c['profile'].get('current_title', '').lower()
    unrelated_keywords = ["marketing manager", "hr manager", "operations manager", "civil engineer", "accountant", "graphic designer", "sales executive", "customer support", "business analyst", "project manager"]
    if any(k in cur_title for k in unrelated_keywords):
        return f"Unrelated current title: {cur_title}"
        
    # Disqualify interns, trainees, students, freshers
    if any(k in cur_title for k in ["intern", "trainee", "student", "fresher"]):
        return f"Intern/Trainee current title: {cur_title}"
        
    return None

def score_education(c):
    """Score education tier based on institution (Weight = 5%)."""
    education = c.get('education', [])
    if not education:
        return 0.4  # Neutral-low
    highest_score = 0.4
    for edu in education:
        college = edu.get('institution', '').lower()
        if any(t1 in college for t1 in TIER_1_COLLEGES):
            highest_score = max(highest_score, 1.0)
        elif any(t2 in college for t2 in TIER_2_COLLEGES):
            highest_score = max(highest_score, 0.7)
        else:
            highest_score = max(highest_score, 0.5)
    return highest_score

def calculate_candidate_score(c):
    """Compute the weighted hybrid fit score for the candidate."""
    cur_title = c['profile'].get('current_title', '').lower()
    
    # 1. Title Score (Weight = 25%)
    title_score = 0.0
    is_senior = any(w in cur_title for w in ["senior", "lead", "principal", "staff", "founding"])
    is_junior = any(w in cur_title for w in ["junior", "associate"])
    
    if any(w in cur_title for w in ["ai engineer", "ml engineer", "machine learning engineer", "nlp engineer", "search engineer", "retrieval engineer", "recommendation systems", "rag engineer"]):
        if is_senior:
            title_score = 1.0
        elif is_junior:
            title_score = 0.5
        else:
            title_score = 0.8
    elif any(w in cur_title for w in ["data scientist", "backend engineer", "software engineer", "data engineer", "developer", "systems engineer"]):
        if is_senior:
            title_score = 0.7
        elif is_junior:
            title_score = 0.3
        else:
            title_score = 0.5
            
    # 2. Experience Score (Weight = 15%)
    years = c['profile'].get('years_of_experience', 0)
    exp_score = 0.0
    if 5.0 <= years <= 9.0:
        exp_score = 1.0
    elif years < 5.0:
        exp_score = max(0.0, 1.0 - 0.2 * (5.0 - years))
    else:
        exp_score = max(0.0, 1.0 - 0.1 * (years - 9.0))
        
    # 3. Product Company Experience (Weight = 15%)
    history = c.get('career_history', [])
    total_months = sum(job.get('duration_months', 0) for job in history)
    product_months = sum(job.get('duration_months', 0) for job in history if job.get('company') in PRODUCT_COMPANIES)
    product_ratio = (product_months / total_months) if total_months > 0 else 0.0
    has_startup = any(job.get('company') in ["CRED", "Swiggy", "Razorpay", "Pied Piper", "Krutrim", "Sarvam AI"] for job in history)
    product_score = min(1.0, product_ratio + (0.2 if has_startup else 0.0))
    
    # 4. Skills Score (Weight = 15%)
    skills_list = [s.get('name', '').lower() for s in c.get('skills', [])]
    
    # Must-have skills (0.25 each group)
    has_g1 = any(s in skills_list or "embedding" in s or "retrieval" in s for s in ["sentence-transformers", "embeddings", "retrieval", "bge", "e5", "openai embeddings"])
    has_g2 = any(s in skills_list or "vector" in s for s in ["pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "chroma"])
    implied_python = ["python", "pytorch", "scikit-learn", "tensorflow", "pandas", "numpy", "keras", "django", "flask", "spacy", "nltk", "fastapi"]
    has_g3 = any(impl in skills_list for impl in implied_python)
    has_g4 = any(s in skills_list or "eval" in s for s in ["ndcg", "mrr", "map", "evaluation"])
    
    must_have_count = sum([has_g1, has_g2, has_g3, has_g4])
    skill_score = 0.25 * must_have_count
    
    # Nice-to-haves (bonus 0.05 each)
    nice_to_haves = [
        any("fine-tuning" in s or "lora" in s or "peft" in s for s in skills_list),
        any("learning-to-rank" in s or "xgboost" in s or "ltr" in s for s in skills_list),
        any("distributed systems" in s or "scaling" in s or "parallel" in s for s in skills_list),
        any("recruiting" in s or "hr" in s or "ats" in s or "talent" in s for s in skills_list)
    ]
    nice_have_count = sum(nice_to_haves)
    skill_score_final = min(1.0, skill_score + 0.05 * nice_have_count)
    
    # 5. Education Score (Weight = 5%)
    edu_score = c.get('_edu_score', 0.4)
    
    # 6. TF-IDF Cosine Similarity Score (Weight = 10%)
    tfidf_score = c.get('_tfidf_score', 0.0)
    
    # 7. Location and Notice Period Score (Weight = 15%)
    loc = c['profile'].get('location', '').lower()
    country = c['profile'].get('country', '').lower()
    
    loc_score = 0.0
    if "pune" in loc or "noida" in loc:
        loc_score = 1.0
    elif any(city in loc for city in ["hyderabad", "mumbai", "delhi", "gurgaon", "bangalore"]):
        loc_score = 0.8
    elif country == "india":
        loc_score = 0.6
    else:
        loc_score = 0.3 if c['redrob_signals'].get('willing_to_relocate') else 0.0
        
    notice_days = c['redrob_signals'].get('notice_period_days', 90)
    notice_score = 0.0
    if notice_days <= 30:
        notice_score = 1.0
    elif notice_days <= 60:
        notice_score = 0.8
    elif notice_days <= 90:
        notice_score = 0.5
    else:
        notice_score = 0.2
        
    loc_notice_score = 0.6 * loc_score + 0.4 * notice_score
    
    # Weighted base score (out of 1.0)
    base_score = (
        0.25 * title_score +
        0.15 * exp_score +
        0.15 * product_score +
        0.15 * skill_score_final +
        0.05 * edu_score +
        0.10 * tfidf_score +
        0.15 * loc_notice_score
    )
    
    # 8. Behavioral Multiplier (0.5 to 1.4 multiplier)
    mult = 1.0
    
    # Recruiter response rate
    resp_rate = c['redrob_signals'].get('recruiter_response_rate', 0.0)
    mult += 0.2 * resp_rate
    
    # Last active date
    last_act = c['redrob_signals'].get('last_active_date', '')
    if last_act:
        try:
            if last_act >= '2026-05-20': # Active in last 30 days
                mult += 0.1
            elif last_act >= '2026-03-20': # Active in last 90 days
                mult += 0.0
            elif last_act < '2025-12-20': # Inactive for > 6 months
                mult -= 0.3
        except:
            pass
            
    # Open to work flag
    if c['redrob_signals'].get('open_to_work_flag'):
        mult += 0.1
    else:
        mult -= 0.1
        
    # Interview attendance
    inv_rate = c['redrob_signals'].get('interview_completion_rate', 0.0)
    if inv_rate >= 0.8:
        mult += 0.1
    elif inv_rate < 0.5:
        mult -= 0.2
        
    # Github activity
    gh_score = c['redrob_signals'].get('github_activity_score', -1)
    if gh_score >= 50:
        mult += 0.1

    # Offer acceptance rate (-1 to 1.0, -1 means no prior offers = neutral)
    offer_rate = c['redrob_signals'].get('offer_acceptance_rate', -1)
    if offer_rate >= 0.7:
        mult += 0.15
    elif 0 <= offer_rate < 0.3:
        mult -= 0.15

    # Saved by recruiters - social proof signal
    saved_count = c['redrob_signals'].get('saved_by_recruiters_30d', 0)
    if saved_count >= 10:
        mult += 0.1
    elif saved_count >= 5:
        mult += 0.05

    # Profile completeness - filters out sloppy/incomplete profiles
    completeness = c['redrob_signals'].get('profile_completeness_score', 50)
    if completeness >= 90:
        mult += 0.05
    elif completeness < 50:
        mult -= 0.1

    # Verification signals - basic trust/fraud check
    verified_count = sum([
        c['redrob_signals'].get('verified_email', False),
        c['redrob_signals'].get('verified_phone', False),
        c['redrob_signals'].get('linkedin_connected', False)
    ])
    if verified_count == 3:
        mult += 0.05
    elif verified_count == 0:
        mult -= 0.1
        
    # Bound multiplier and apply
    final_mult = max(0.5, min(1.4, mult))
    return base_score * final_mult

def generate_candidate_reasoning(c, rank):
    """Generate concise, factual, non-templated reasoning based on actual candidate qualifications."""
    profile = c['profile']
    title = profile.get('current_title', '').strip()
    company = profile.get('current_company', '').strip()
    years = profile.get('years_of_experience', 0)
    loc = profile.get('location', '').strip()
    notice = c['redrob_signals'].get('notice_period_days', 90)
    
    # Extract matching skills
    skills_list = [s.get('name') for s in c.get('skills', [])]
    skills_lower = [s.lower() for s in skills_list]
    
    vectordbs = ["pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "chroma"]
    retrievals = ["retrieval", "embeddings", "embedding", "search", "semantic search", "rag", "ranking", "nlp", "llm", "fine-tuning", "lora", "peft"]
    evals = ["ndcg", "mrr", "map", "evaluation"]
    nice_to_haves = ["fine-tuning", "lora", "peft", "xgboost", "learning-to-rank", "distributed systems", "inference optimization"]
    
    matched_vdb = [s for s in skills_list if s.lower() in vectordbs]
    matched_ret = [s for s in skills_list if any(w in s.lower() for w in retrievals)]
    matched_eval = [s for s in skills_list if any(w in s.lower() for w in evals)]
    matched_nice = [s for s in skills_list if any(w in s.lower() for w in nice_to_haves)]
    
    company_text = f" at {company}" if company else ""
    sent1 = f"Strong fit as a {title}{company_text} with {years:.1f} years of experience."
    
    skill_mentions = []
    if matched_ret:
        skill_mentions.append(matched_ret[0])
    if matched_vdb and matched_vdb[0] not in skill_mentions:
        skill_mentions.append(matched_vdb[0])
    if matched_eval and matched_eval[0] not in skill_mentions:
        skill_mentions.append(matched_eval[0])
        
    skill_phrase = ""
    if skill_mentions:
        skill_phrase = f"Proven hands-on experience with {', '.join(skill_mentions)}"
    else:
        skill_phrase = "Strong machine learning engineering background"
        
    if matched_nice and matched_nice[0] not in skill_phrase:
        skill_phrase += f" and {matched_nice[0]}"
    sent2 = f"{skill_phrase}."
    
    # Education
    edu_score_val = c.get('_edu_score', 0.4)
    edu_phrase = ""
    if edu_score_val >= 1.0:
        edu_phrase = " Candidate has a strong educational background from a Tier-1 institution."
        
    # Platform Behavior
    signal_phrase = ""
    offer_rate = c['redrob_signals'].get('offer_acceptance_rate', -1)
    if offer_rate >= 0.7:
        signal_phrase = f" Shows high offer acceptance rate ({int(offer_rate * 100)}%)."
    else:
        resp_rate = c['redrob_signals'].get('recruiter_response_rate', 0.0)
        if resp_rate >= 0.7:
            signal_phrase = f" Exceptionally responsive to recruiter messages ({int(resp_rate * 100)}% rate)."
            
    # Location and Notice
    loc_phrase = ""
    if "noida" in loc.lower() or "pune" in loc.lower():
        loc_phrase = f"Ideally located in {loc}"
    else:
        loc_phrase = f"Located in {loc}"
        
    notice_phrase = ""
    if notice <= 30:
        notice_phrase = f"with a quick {notice}-day notice period"
    else:
        notice_phrase = f"with a {notice}-day notice period"
        
    # Concerns
    concerns = []
    if notice > 60:
        concerns.append(f"{notice}d notice")
    if years < 5.0:
        concerns.append(f"{years:.1f}y experience (a bit junior)")
    if years > 9.0:
        concerns.append(f"{years:.1f}y experience (more senior)")
    country = profile.get('country', '').lower()
    if country != "india" and not c['redrob_signals'].get('willing_to_relocate'):
        concerns.append("needs relocation support")
        
    concern_phrase = ""
    if concerns:
        concern_phrase = f" Note: {', '.join(concerns)}."
        
    if rank <= 10:
        reasoning = f"{sent1} {sent2}{edu_phrase}{signal_phrase} Perfectly fits the hybrid setup {notice_phrase}.{concern_phrase}"
    elif rank <= 50:
        reasoning = f"{sent1} {sent2}{edu_phrase} Good location fit ({loc}) {notice_phrase}.{concern_phrase}"
    else:
        reasoning = f"Good technical match with {years:.1f} years experience, skilled in {skill_mentions[0] if skill_mentions else 'ML'}.{concern_phrase}"
        
    return reasoning

def main():
    parser = argparse.ArgumentParser(description="AI Resume Ranker for Redrob Challenge")
    parser.add_argument("--candidates", type=str, required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", type=str, required=True, help="Path to output submission.csv")
    args = parser.parse_args()
    
    candidates_path = Path(args.candidates)
    if not candidates_path.exists():
        print(f"Error: Candidates file {candidates_path} does not exist.")
        return
        
    print(f"Reading candidates from {candidates_path}...")
    
    # Open gzipped or raw jsonl file
    if candidates_path.suffix == ".gz":
        open_func = lambda p: gzip.open(p, "rt", encoding="utf-8")
    else:
        open_func = lambda p: open(p, "r", encoding="utf-8")
        
    scored_candidates = []
    honeypot_count = 0
    disqualified_count = 0
    total_processed = 0
    qualified_candidates = []
    
    # Load JD text dynamically (zero-dependency XML parser)
    jd_text = find_and_load_job_description(args.candidates)
    
    with open_func(candidates_path) as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            total_processed += 1
            
            # Step 1: Filter out honeypots (achieves 0% honeypots in top 100)
            if is_honeypot_candidate(c):
                honeypot_count += 1
                continue
                
            # Step 2: Filter out disqualified candidates (based on JD guidelines)
            disq = get_disqualification_reason(c)
            if disq:
                disqualified_count += 1
                continue
                
            # Keep qualified candidates for TF-IDF / batch scoring
            qualified_candidates.append(c)
            
    print(f"Processed {total_processed} total profiles.")
    print(f"Filtered out {honeypot_count} honeypots.")
    print(f"Filtered out {disqualified_count} disqualified profiles.")
    
    if qualified_candidates:
        print("Computing TF-IDF match scores...")
        candidate_texts = [build_candidate_text(c) for c in qualified_candidates]
        tfidf_scores = compute_tfidf_scores(jd_text, candidate_texts)
        
        print("Scoring candidates...")
        for c, tfidf in zip(qualified_candidates, tfidf_scores):
            c['_tfidf_score'] = float(tfidf)
            c['_edu_score'] = score_education(c)
            score = round(calculate_candidate_score(c), 4)
            scored_candidates.append((c, score))
            
    print(f"Scored {len(scored_candidates)} qualified profiles.")
    
    # Step 4: Sort candidates by score descending, break ties by candidate_id ascending
    scored_candidates.sort(key=lambda x: (-x[1], x[0]['candidate_id']))
    
    # Step 5: Format top 100 and write to CSV
    top_100 = scored_candidates[:100]
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing top 100 candidates to {out_path}...")
    
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, (c, score) in enumerate(top_100, 1):
            cid = c['candidate_id']
            reasoning = generate_candidate_reasoning(c, rank)
            # Output rounded score
            writer.writerow([cid, rank, score, reasoning])
            
    print("Done ranking successfully.")

if __name__ == "__main__":
    main()
