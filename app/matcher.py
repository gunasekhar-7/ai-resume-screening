from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Any

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def compute_semantic_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    model = get_model()
    embeddings = model.encode([text1, text2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score * 100), 2)

def _score_skills(resume_skills, jd_skills):
    if not jd_skills:
        return 100.0
    if not resume_skills:
        return 0.0
    sem_score = compute_semantic_similarity(" ".join(resume_skills), " ".join(jd_skills))
    jd_skills_lower = [s.lower() for s in jd_skills]
    matched_count = 0
    for r_skill in resume_skills:
        if r_skill.lower() in jd_skills_lower:
            matched_count += 1
        else:
            for jd_skill in jd_skills:
                if compute_semantic_similarity(r_skill, jd_skill) > 70:
                    matched_count += 0.5
                    break
    overlap_score = (matched_count / len(jd_skills)) * 100 if jd_skills else 0.0
    return min(0.7 * sem_score + 0.3 * overlap_score, 100.0)

def _score_experience(resume_years: float, jd_years: int):
    if jd_years == 0: return 100.0
    if resume_years >= jd_years: return 100.0
    return min(round((resume_years / jd_years) * 100, 2), 100.0)

def _score_education(resume_edu, jd_edu_reqs):
    if not jd_edu_reqs: return 100.0
    if not resume_edu: return 0.0
    jd_edu_lower = [req.lower() for req in jd_edu_reqs]
    for entry in resume_edu:
        if any(req in entry.get("degree", "").lower() for req in jd_edu_lower):
            return 100.0
    return 0.0

def calculate_match_score(parsed_resume, parsed_jd, weights=None):
    if weights is None:
        weights = {"skills":0.6,"experience":0.3,"education":0.1,"overall_text":0.0}
    total_weight = sum(weights.values())
    if total_weight != 1.0:
        weights = {k:v/total_weight for k,v in weights.items()}
    scores = {
        "skills": _score_skills(parsed_resume.get("skills", []), parsed_jd.get("required_skills", [])),
        "experience": _score_experience(parsed_resume.get("total_experience_years", 0.0), parsed_jd.get("experience_requirements",0)),
        "education": _score_education(parsed_resume.get("education", []), parsed_jd.get("education_requirements",[])),
        "overall_text": compute_semantic_similarity(parsed_resume.get("full_text",""), parsed_jd.get("full_text",""))
    }
    final_score = sum(scores[k] * weights[k] for k in weights)
    return round(final_score, 2)

def rank_resumes(resumes_parsed_data: List[Dict[str, Any]], parsed_jd: Dict[str, Any]) -> List[Dict[str, Any]]:
    return sorted(
        [{"filename": data.get('filename','Unknown'), "score": calculate_match_score(data, parsed_jd), "parsed_data": data}
        for data in resumes_parsed_data],
        key=lambda x: x['score'], reverse=True
    )
