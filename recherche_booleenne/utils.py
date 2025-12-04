"""
UTILITAIRES POUR LA RECHERCHE BOOLÉENNE
Normalisation, validation, formatage
"""
import re
from typing import List, Dict, Set, Optional

def normalize_text(text: str) -> str:
    """
    Normalise un texte (comme le preprocessing NLP)
    
    Args:
        text: Texte brut
    
    Returns:
        Texte normalisé (minuscules, espaces nettoyés)
    """
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def parse_skills_string(skills_str: str) -> List[str]:
    """
    Parse une chaîne de compétences (format Whoosh KEYWORD)
    
    Args:
        skills_str: "python,django,react" (comma-separated)
    
    Returns:
        ["python", "django", "react"]
    """
    if not skills_str:
        return []
    return [s.strip().lower() for s in skills_str.split(",") if s.strip()]

def validate_search_filters(filters: Dict) -> Dict:
    """
    Valide et normalise les filtres de recherche
    
    Args:
        filters: Dictionnaire brut depuis l'API
    
    Returns:
        Dictionnaire validé
    
    Exemple:
        Input:  {"skills": ["Python", "DJANGO"], "experience": [3, 10]}
        Output: {"skills": ["python", "django"], "experience_min": 3, "experience_max": 10}
    """
    validated = {}
    
    # 1. Compétences (liste de strings)
    if "skills" in filters and isinstance(filters["skills"], list):
        validated["skills"] = [
            s.lower().strip() 
            for s in filters["skills"] 
            if isinstance(s, str) and s.strip()
        ]
    
    # 2. Expérience (plage [min, max])
    if "experience" in filters:
        exp = filters["experience"]
        if isinstance(exp, list) and len(exp) == 2:
            validated["experience_min"] = max(0, int(exp[0]))
            validated["experience_max"] = min(50, int(exp[1]))
        elif isinstance(exp, (int, float)):
            # Si un seul chiffre, cherche >= ce chiffre
            validated["experience_min"] = max(0, int(exp))
    
    # 3. Localisation (string)
    if "location" in filters and filters["location"]:
        validated["location"] = normalize_text(str(filters["location"]))
    
    # 4. Niveau (junior/senior/expert)
    if "level" in filters and filters["level"]:
        level = str(filters["level"]).lower()
        if level in ["junior", "intermediaire", "senior", "expert"]:
            validated["level"] = level
    
    # 5. Opérateur booléen (AND/OR pour compétences)
    if "boolean_operator" in filters:
        op = str(filters["boolean_operator"]).upper()
        validated["boolean_operator"] = op if op in ["AND", "OR"] else "AND"
    else:
        validated["boolean_operator"] = "AND"
    
    # 6. Remote (booléen)
    if "remote" in filters:
        validated["remote"] = bool(filters["remote"])
    
    return validated

def format_cv_result(whoosh_hit: Dict, postgres_id: Optional[int] = None) -> Dict:
    """
    Formate un résultat CV Whoosh pour l'API
    
    Args:
        whoosh_hit: Document Whoosh (dict-like)
        postgres_id: ID PostgreSQL (depuis mapping)
    
    Returns:
        Dictionnaire formaté pour le frontend
    """
    return {
        "id": whoosh_hit.get("doc_id"),  # ID système
        "postgres_id": postgres_id,       # ID PostgreSQL
        "nom": whoosh_hit.get("nom", ""),
        "titre": whoosh_hit.get("titre_profil", ""),
        "competences": parse_skills_string(whoosh_hit.get("competences", "")),
        "experience": int(whoosh_hit.get("annees", 0)),
        "localisation": whoosh_hit.get("localisation", ""),
        "projets": whoosh_hit.get("projets", ""),
        "score_booleen": 1.0  # Booléen = match exact (pas de score partiel)
    }

def format_job_result(whoosh_hit: Dict, postgres_id: Optional[int] = None) -> Dict:
    """
    Formate un résultat offre Whoosh pour l'API
    
    Args:
        whoosh_hit: Document Whoosh
        postgres_id: ID PostgreSQL
    
    Returns:
        Dictionnaire formaté
    """
    return {
        "id": whoosh_hit.get("job_id"),
        "postgres_id": postgres_id,
        "titre": whoosh_hit.get("titre_poste", ""),
        "entreprise": whoosh_hit.get("entreprise", ""),
        "competences": parse_skills_string(whoosh_hit.get("competences_requises", "")),
        "localisation": whoosh_hit.get("localisation", ""),
        "niveau": whoosh_hit.get("niveau_souhaite", ""),
        "experience_min": int(whoosh_hit.get("annees_min", 0)),
        "experience_max": int(whoosh_hit.get("annees_max", 50)),
        "type_contrat": whoosh_hit.get("type_contrat", ""),
        "score_booleen": 1.0
    }

def extract_keywords_from_query(query_text: str, known_skills: Set[str]) -> List[str]:
    """
    Extrait les compétences techniques d'une requête libre
    
    Args:
        query_text: "Je cherche un développeur Python avec Django"
        known_skills: Set de compétences connues (depuis skills_json_file.json)
    
    Returns:
        ["python", "django"]
    """
    query_lower = normalize_text(query_text)
    detected = []
    
    for skill in known_skills:
        # Recherche avec word boundary pour éviter faux positifs
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, query_lower):
            detected.append(skill.lower())
    
    return detected