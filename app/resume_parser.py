import spacy
from spacy.matcher import PhraseMatcher
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

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

def _extract_education_from_doc(text: str) -> List[Dict[str, str]]:
    # (Pattern matching as before—can be optimized/extended as needed)
    # [Patterns and function unchanged for brevity]
    return []  # Implement as before

def _extract_experience_details(text: str) -> List[Dict[str, Any]]:
    # (Pattern matching as before)
    return []  # Implement as before

def _calculate_total_experience(entries: List[Dict[str, Any]]) -> float:
    # Returns total years of experience
    return 0.0  # Implement as before

def _extract_contact_info(doc) -> Dict[str, str]:
    # (Regex patterns as before)
    return {}  # Implement as before

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
