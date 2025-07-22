import spacy
from spacy.matcher import PhraseMatcher
import re
from datetime import datetime
from typing import List, Dict, Any

# Load spaCy model (optimized for speed on 'en_core_web_lg')
try:
    nlp = spacy.load("en_core_web_lg", disable=["parser", "textcat"])
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg", disable=["parser", "textcat"])

# Efficient, dynamically extendable skill list
DEFAULT_SKILLS = [
    # (abbreviated for brevity—extend or load dynamically as needed)
    "Python", "Java", "C++", "Data Science", "Machine Learning", "AWS", "React", "Django",
    # ...
]

def _extract_skills_from_doc(doc, skillset) -> List[str]:
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp.make_doc(skill) for skill in skillset]
    matcher.add("SKILL_PATTERNS", patterns)
    found_skills = {doc[start:end].text for _, start, end in matcher(doc)}
    text_lower = doc.text.lower()
    for skill in skillset:
        if skill.lower() in text_lower:
            found_skills.add(skill)
    return sorted(found_skills)



def _extract_education_from_doc(text: str):
    """Extract the main degree or education info from resume text."""
    education_entries = []
    # Common degree patterns seen in resumes
    degree_patterns = [
        r"(Bachelor(?:'s)?\s*(?:of)?\s*[A-Za-z &]+|B\.?(?:Sc|Eng|Tech|E|A)?(?:\.| )+)",
        r"(Master(?:'s)?\s*(?:of)?\s*[A-Za-z &]+|M\.?(?:Sc|Tech|E|A)?(?:\.| )+)",
        r"(Ph\.?\s?D\.?|Doctor(?:ate| of Philosophy))",
        r"(Diploma\s*in\s*[A-Za-z &]+)",
        r"(Associate(?:'s)?\s*(?:Degree)?\s*in\s*[A-Za-z &]+)"
    ]

    # Combine the patterns for a single regex search
    degree_regex = re.compile("|".join(degree_patterns), re.IGNORECASE)

    # Split document into lines for easier parsing
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:
        degree_match = degree_regex.search(line)
        if degree_match:
            degree = degree_match.group(0)
            # Try to also grab subject/major after the degree
            after = ""
            m = re.search(r"in ([A-Za-z0-9 &/]+)", line, re.IGNORECASE)
            if m:
                after = f"in {m.group(1)}"
            education_entry = {
                'degree': f"{degree} {after}".strip()
            }
            education_entries.append(education_entry)

    return education_entries or [{'degree': "N/A"}]




def _extract_experience_details(text: str) -> List[Dict[str, Any]]:
    """
    Extracts work experience entries from resume text.
    Returns a list of dicts, each containing: job_title, company, duration, and years.
    """
    experience_entries = []
    # Split text into lines for targeted parsing
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Define regular expressions for date ranges (e.g., Jan 2019 - Feb 2023)
    date_patterns = [
        r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s?\d{4}\s*[-–to]+\s*(Present|Current|\w+\s?\d{4}))',
        r'(\d{4}\s*[-–to]+\s*(Present|Current|\d{4}))'
    ]
    date_regex = re.compile("|".join(date_patterns), re.IGNORECASE)

    # Simple patterns for job and company (used as context clues)
    title_keywords = ['engineer', 'developer', 'scientist', 'manager', 'analyst', 'consultant', 'lead', 'intern', 'director']
    company_pattern = re.compile(r'at\s+([A-Z][A-Za-z0-9\-\s&\.]+)|,\s*([A-Z][A-Za-z0-9\-\s&\.]+)', re.IGNORECASE)

    for i, line in enumerate(lines):
        entry = {}
        # Search for date/duration info
        date_match = date_regex.search(line)
        if date_match:
            entry['duration'] = date_match.group(0)
            # Attempt to parse years
            years = 0.0
            if 'present' in entry['duration'].lower() or 'current' in entry['duration'].lower():
                end_year = 2025  # Use current year or get from datetime
            else:
                end_year_search = re.search(r'(\d{4})$', entry['duration'])
                end_year = int(end_year_search.group(1)) if end_year_search else None
            start_year_search = re.search(r'(\d{4})', entry['duration'])
            start_year = int(start_year_search.group(1)) if start_year_search else None
            if start_year and end_year and end_year >= start_year:
                years = end_year - start_year
            entry['years'] = years

            # Try to extract job title (look at current line or previous line)
            job_title = ""
            cur = line
            prev = lines[i-1] if i > 0 else ""
            # Heuristic: title contains certain keywords
            for l in [cur, prev]:
                for kw in title_keywords:
                    if kw.lower() in l.lower() and len(l.split()) < 8:
                        job_title = l
                        break
                if job_title:
                    break
            entry['job_title'] = job_title.strip() if job_title else "N/A"

            # Try to extract company name (from "at" or comma patterns)
            company_match = company_pattern.search(cur) or (company_pattern.search(prev) if prev else None)
            entry['company'] = company_match.group(1) or company_match.group(2) if company_match else "N/A"

            experience_entries.append(entry)

    return experience_entries

def _calculate_total_experience(entries: list) -> float:
    """
    Calculates the total years of experience from parsed experience entries.
    Adds all 'years' fields that are positive numbers.
    """
    total = 0.0
    for entry in entries:
        years = entry.get("years", 0.0)
        try:
            val = float(years)
            if val > 0:
                total += val
        except (ValueError, TypeError):
            continue
    # Optionally, round to 1 decimal place
    return round(total, 1)


def _extract_contact_info(doc):
    text = doc.text
    result = {}

    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        result["email"] = email_match.group(0)
    else:
        result["email"] = ""

    # Extract phone number (basic pattern)
    phone_match = re.search(r'(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?|\d{3}[\s-])\d{3}[\s-]?\d{4}', text)
    if phone_match:
        result["phone"] = phone_match.group(0)
    else:
        result["phone"] = ""

    # --- Improved Name Extraction ---
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name = ""

    # 1. Look for "Name:" or similar patterns anywhere in first 10 lines
    for line in lines[:10]:
        m = re.match(r'(Name|Candidate Name|Full Name)\s*:\s*(.+)', line, re.IGNORECASE)
        if m:
            name = m.group(2).strip()
            break

    # 2. If not found, assume first line is name if it's not an email/phone/address/heading
    if not name and lines:
        first_line = lines[0]
        # Skip common headings
        ignore_headings = ['resume', 'curriculum vitae', 'cv', 'profile', 'bio']
        if not any(h in first_line.lower() for h in ignore_headings) and \
           not re.search(r'\d', first_line) and \
           '@' not in first_line and \
           len(first_line.split()) in [2, 3] and \
           first_line != '':
            name = first_line.strip()

    # 3. As a last resort, take the username from the email
    if not name and result["email"]:
        name = result["email"].split('@')[0].replace('.', ' ').replace('_', ' ').title()

    result["name"] = name or "N/A"
    return result


def parse_resume(full_text: str) -> Dict[str, Any]:
    if not full_text:
        return {}
    doc = nlp(full_text)
    clean_text = re.sub(r'\s+', ' ', full_text).strip()
    return {
        "contact_info": _extract_contact_info(doc),
        "skills": _extract_skills_from_doc(doc, DEFAULT_SKILLS),
        "education": _extract_education_from_doc(clean_text),
        "experience": _extract_experience_details(clean_text),
        "total_experience_years": _calculate_total_experience(_extract_experience_details(clean_text)),
        "full_text": clean_text
    }

def parse_job_description(jd_text: str) -> Dict[str, Any]:
    if not jd_text:
        return {}
    doc = nlp(jd_text)
    clean_text = re.sub(r'\s+', ' ', jd_text).strip()
    skills = _extract_skills_from_doc(doc, DEFAULT_SKILLS)
    experience_req = 0
    exp_match = re.search(r'(\d+)(?:\+)?\s*(?:years?|yrs?)\s+of\s+experience', jd_text, re.I)
    if exp_match:
        experience_req = int(exp_match.group(1))
    education_reqs = []
    edu_match = re.search(r'(Bachelor\'s|Master\'s|PhD|B\.S\.|M\.S\.|B\.Tech|M\.Tech|B\.E|M\.E)', jd_text, re.I)
    if edu_match:
        education_reqs.append(edu_match.group(1))
    return {
        "required_skills": skills,
        "experience_requirements": experience_req,
        "education_requirements": education_reqs,
        "full_text": clean_text
    }
