"""
============================================================================
SMARTHIRE - Info Extractor Module
Extraction d'informations structurées depuis les CV
============================================================================
"""

import re
import logging
from typing import Optional

from backend.config.settings import MOROCCAN_CITIES

logger = logging.getLogger(__name__)

# ========================================================
# EXTRACTION DU NOM
# ========================================================
def extraire_nom(texte: str) -> str:
    """
    Extrait le nom du candidat avec validation
    
    Args:
        texte: Texte du CV
        
    Returns:
        Nom du candidat ou "Candidat" par défaut
    """
    if not texte:
        return "Candidat"
    
    # 1️⃣ Cherche après \Large (format LaTeX)
    match = re.search(r"Large\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", texte)
    if match:
        nom = match.group(1).strip()
        words = nom.split()
        if 2 <= len(words) <= 4:
            return nom
    
    # 2️⃣ Cherche au début du document (premières lignes)
    debut = texte[:200]
    match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})", debut)
    if match:
        nom = match.group(1).strip()
        # Exclusion de mots-clés courants
        excluded_words = ["summary", "objective", "professional", "experience",
                         "skills", "education", "profile"]
        if nom.lower() not in excluded_words:
            return nom
    
    # 3️⃣ Cherche avant "Experience"
    match = re.search(r"((?:[A-Z][a-z]+\s+)+)(?:Experience|EXPERIENCE|Expérience)", texte)
    if match:
        nom = match.group(1).strip()
        words = nom.split()
        if 2 <= len(words) <= 3:
            return nom
    
    return "Candidat"


# ========================================================
# EXTRACTION DU TITRE PROFESSIONNEL
# ========================================================
def extraire_titre_profil(texte: str) -> str:
    """
    Extrait le titre du profil professionnel
    
    Args:
        texte: Texte du CV
        
    Returns:
        Titre professionnel ou "Professional" par défaut
    """
    if not texte:
        return "Professional"
    
    job_keywords = [
        "developer", "engineer", "manager", "analyst", "architect",
        "specialist", "lead", "senior", "junior", "designer",
        "officer", "consultant", "administrator", "director",
        "développeur", "ingénieur", "chef", "responsable"
    ]
    
    # 1️⃣ Après le nom (ligne suivante)
    match = re.search(
        r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*\n\s*([A-Z][a-zA-Z\s\-/+\.]{5,80}?)(?:\n|$)",
        texte,
        re.MULTILINE
    )
    if match:
        title = match.group(1).strip()
        if any(kw in title.lower() for kw in job_keywords):
            return title
    
    # 2️⃣ Pattern "Titre | Location"
    match = re.search(r"^([A-Z][a-zA-Z\s\-/+\.]{5,80}?)\s*\|\s*(?:\d+|[A-Z])", texte, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        if any(kw in title.lower() for kw in job_keywords):
            return title
    
    # 3️⃣ Cherche les titres courants
    match = re.search(
        r"(?:^|\n)([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Designer|Consultant))",
        texte,
        re.MULTILINE
    )
    if match:
        return match.group(1).strip()
    
    return "Professional"


# ========================================================
# EXTRACTION DES ANNÉES D'EXPÉRIENCE
# ========================================================
def extraire_annees_experience(texte: str) -> int:
    """
    Extrait le nombre d'années d'expérience
    
    Args:
        texte: Texte du CV
        
    Returns:
        Nombre d'années (0-50)
    """
    if not texte:
        return 0
    
    # 1️⃣ Recherche explicite "X years"
    match = re.search(
        r"(\d+)\+?\s*(?:years?|ans|year|an)\s+(?:of\s+)?(?:experience|expérience)",
        texte,
        re.IGNORECASE
    )
    if match:
        years = int(match.group(1))
        return min(years, 50)
    
    # 2️⃣ Calcul depuis les dates d'expérience
    total = 0
    dates = re.findall(
        r"(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(Present|Current|Aujourd'hui|Actuel|\w+\s+\d{4}|\d{4})",
        texte
    )
    
    for start, end in dates:
        try:
            # Extraction année de début
            y1 = int(re.search(r"\d{4}", start).group())
            
            # Validation année
            if y1 < 1970 or y1 > 2025:
                continue
            
            # Extraction année de fin
            if any(x in end.lower() for x in ["present", "current", "actuel", "aujourd'hui"]):
                y2 = 2025
            else:
                y2 = int(re.search(r"\d{4}", end).group())
                if y2 < 1970 or y2 > 2025:
                    continue
            
            # Calcul de la durée
            if y2 >= y1:
                total += (y2 - y1)
        except Exception:
            continue
    
    # Limite à 50 ans maximum
    if total > 50:
        total = 50
    
    return max(total, 0)


# ========================================================
# EXTRACTION DE LA LOCALISATION
# ========================================================
def extraire_localisation(texte: str) -> str:
    """
    Extrait la localisation du candidat
    
    Args:
        texte: Texte du CV
        
    Returns:
        Ville ou "Maroc" par défaut
    """
    if not texte:
        return "Maroc"
    
    lower_text = texte.lower()
    
    # Recherche des villes marocaines
    for ville_lower, ville_proper in MOROCCAN_CITIES.items():
        if ville_lower in lower_text:
            return ville_proper
    
    return "Maroc"


# ========================================================
# EXTRACTION DU RÉSUMÉ
# ========================================================
def extraire_resume(texte: str, max_length: int = 500) -> str:
    """
    Extrait le résumé professionnel
    
    Args:
        texte: Texte du CV
        max_length: Longueur maximale du résumé
        
    Returns:
        Résumé professionnel
    """
    if not texte:
        return ""
    
    # Recherche de la section Summary/Objective
    match = re.search(
        r"(?:Summary|Objective|Professional\s+Summary|Résumé|Professionnel|Profile)\s*[:\-]?\s*(.*?)(?:Experience|Skills|Education|Expérience|Compétences|$)",
        texte,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        resume = match.group(1).strip()
        # Nettoyage des espaces multiples
        resume = re.sub(r'\s+', ' ', resume)
        # Limitation de la longueur
        resume = resume[:max_length]
        
        # Validation: au moins 20 caractères
        if len(resume) > 20:
            return resume
    
    return ""


# ========================================================
# EXTRACTION DE L'EXPÉRIENCE
# ========================================================
def extraire_description_experience(texte: str, max_length: int = 1000) -> str:
    """
    Extrait la description de l'expérience professionnelle
    
    Args:
        texte: Texte du CV
        max_length: Longueur maximale
        
    Returns:
        Description de l'expérience
    """
    if not texte:
        return ""
    
    # Recherche de la section Experience
    match = re.search(
        r"(?:Experience|Expérience|Professional\s+Experience)\s*[:\-]?\s*(.*?)(?:Skills|Education|Projects|Certifications|Compétences|Formation|Projets|$)",
        texte,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        experience = match.group(1).strip()
        # Nettoyage
        experience = re.sub(r'\s+', ' ', experience)
        experience = experience[:max_length]
        
        if len(experience) > 20:
            return experience
    
    return ""


# ========================================================
# EXTRACTION DES PROJETS
# ========================================================
def extraire_projets(texte: str) -> str:
    """
    Extrait les noms des projets
    
    Args:
        texte: Texte du CV
        
    Returns:
        Projets séparés par " | "
    """
    if not texte:
        return ""
    
    # Recherche de la section Projects
    match = re.search(
        r"Projects?\s*[:\-]?(.*?)(?:Skills|Education|Certifications|Languages|$)",
        texte,
        re.DOTALL | re.IGNORECASE
    )
    
    if not match:
        return ""
    
    block = match.group(1)
    
    # Extraction des noms de projets (patterns courants)
    projets = re.findall(
        r"([A-Z][\w\s\-\(\)]{10,100}(?:Application|Dashboard|System|Model|Platform|App|API|Website|Tool|Service|Portal|Solution|Framework))",
        block
    )
    
    # Nettoyage et limitation
    projets = [p.strip() for p in projets[:5]]
    
    return " | ".join(projets) if projets else ""


# ========================================================
# FONCTION COMPLÈTE D'EXTRACTION
# ========================================================
def extraire_toutes_infos(texte: str) -> dict:
    """
    Extrait toutes les informations d'un CV
    
    Args:
        texte: Texte complet du CV
        
    Returns:
        Dictionnaire avec toutes les informations
    """
    return {
        'nom': extraire_nom(texte),
        'titre_profil': extraire_titre_profil(texte),
        'annees_experience': extraire_annees_experience(texte),
        'localisation': extraire_localisation(texte),
        'resume': extraire_resume(texte),
        'description_experience': extraire_description_experience(texte),
        'projets': extraire_projets(texte)
    }


if __name__ == "__main__":
    # Test du module
    texte_test = """
    Jean Dupont
    Senior Software Engineer
    
    Casablanca, Morocco | +212 600 000 000
    
    PROFESSIONAL SUMMARY
    Experienced software engineer with 8 years of experience in full-stack development.
    Specialized in Python, JavaScript, and cloud technologies.
    
    EXPERIENCE
    Senior Developer at TechCorp (2020 - Present)
    Led development of microservices architecture using Docker and Kubernetes.
    Implemented CI/CD pipelines and automated testing frameworks.
    
    Software Engineer at StartupXYZ (2016 - 2020)
    Developed web applications using Django and React.
    
    SKILLS
    Python, Django, Flask, React, Node.js, Docker, Kubernetes, AWS
    
    PROJECTS
    E-commerce Platform: Built scalable e-commerce system
    Analytics Dashboard: Real-time data visualization tool
    """
    
    print("="*80)
    print("TEST DU MODULE INFO EXTRACTOR")
    print("="*80)
    
    infos = extraire_toutes_infos(texte_test)
    
    print(f"\n👤 NOM: {infos['nom']}")
    print(f"💼 TITRE: {infos['titre_profil']}")
    print(f"📅 EXPÉRIENCE: {infos['annees_experience']} ans")
    print(f"📍 LOCALISATION: {infos['localisation']}")
    print(f"📝 RÉSUMÉ: {infos['resume'][:100]}...")
    print(f"💡 PROJETS: {infos['projets']}")
    print(f"🏢 EXPÉRIENCE: {infos['description_experience'][:100]}...")