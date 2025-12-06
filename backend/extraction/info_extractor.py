"""
============================================================================
SMARTHIRE - Info Extractor Module (FIXED)
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
    
    # 2️⃣ Cherche au tout début du document (première ligne non vide)
    lines = texte.strip().split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if not line:
            continue
        
        # Pattern pour nom complet (2-4 mots capitalisés)
        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$', line)
        if match:
            nom = match.group(1).strip()
            # Exclusion de mots-clés courants
            excluded_words = ["summary", "objective", "professional", "experience",
                            "skills", "education", "profile", "curriculum", "vitae"]
            if nom.lower() not in excluded_words and len(nom) > 5:
                return nom
    
    # 3️⃣ Cherche avant le titre professionnel (pattern plus flexible)
    match = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\n\s*[A-Z]', texte, re.MULTILINE)
    if match:
        nom = match.group(1).strip()
        words = nom.split()
        if 2 <= len(words) <= 4:
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
        "développeur", "ingénieur", "chef", "responsable", "scientist",
        "technician", "coordinator", "supervisor", "programmer"
    ]
    
    lines = texte.strip().split('\n')
    
    # 1️⃣ Cherche dans les 10 premières lignes
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Check si la ligne contient un mot-clé de job
        if any(kw in line.lower() for kw in job_keywords):
            # Nettoie la ligne des caractères spéciaux au début/fin
            title = re.sub(r'^[\W_]+|[\W_]+$', '', line)
            if 5 < len(title) < 100:
                return title
    
    # 2️⃣ Pattern "Titre | Location" ou "Titre - Location"
    match = re.search(r'^([A-Z][a-zA-Z\s\-/+\.]{5,80}?)\s*[\|\-]\s*[A-Z]', texte, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        if any(kw in title.lower() for kw in job_keywords):
            return title
    
    # 3️⃣ Cherche les titres courants avec patterns spécifiques
    match = re.search(
        r"(?:^|\n)([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Designer|Consultant|Architect|Specialist|Lead))",
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
    
    # Recherche de la section Summary/Objective avec variations
    patterns = [
        r"(?:PROFESSIONAL\s+SUMMARY|Summary|Objective|Professional\s+Summary|Résumé|Professionnel|Profile)\s*[:\-]?\s*\n\s*(.*?)(?:\n\s*\n|\n\s*[A-Z]{3,})",
        r"(?:PROFESSIONAL\s+SUMMARY|Summary|Objective)\s*[:\-]?\s*(.*?)(?:EXPERIENCE|SKILLS|EDUCATION)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
        if match:
            resume = match.group(1).strip()
            # Nettoyage des espaces multiples et retours à la ligne
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
    
    # Recherche de la section Experience (avec \n pour capturer après le titre)
    match = re.search(
        r"(?:EXPERIENCE|Expérience|Professional\s+Experience|PROFESSIONAL\s+EXPERIENCE|Work\s+Experience)\s*[:\-]?\s*\n(.*?)(?:\n\s*(?:SKILLS|EDUCATION|PROJECTS|CERTIFICATIONS|Compétences|Formation|Projets)|$)",
        texte,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        experience = match.group(1).strip()
        # Nettoyage des espaces multiples tout en gardant les retours à la ligne importants
        experience = re.sub(r'[ \t]+', ' ', experience)
        experience = re.sub(r'\n{3,}', '\n\n', experience)
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
        r"PROJECTS?\s*[:\-]?(.*?)(?:SKILLS|EDUCATION|CERTIFICATIONS|LANGUAGES|$)",
        texte,
        re.DOTALL | re.IGNORECASE
    )
    
    if not match:
        return ""
    
    block = match.group(1)
    
    # Extraction des lignes de projets (format: "Nom du projet: Description")
    projets = []
    lines = block.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Pattern 1: "Project Name: Description"
        match_colon = re.match(r'^([^:]{10,80}):\s*(.+)', line)
        if match_colon:
            projets.append(match_colon.group(1).strip())
            continue
        
        # Pattern 2: Ligne commençant par une majuscule avec mots-clés
        if any(keyword in line for keyword in ['Application', 'Dashboard', 'System', 'Platform', 'Tool', 'Website', 'Portal', 'Solution', 'Framework', 'API', 'App', 'Service']):
            # Extrait jusqu'au premier : ou fin de ligne
            proj_name = line.split(':')[0].strip()
            if 10 < len(proj_name) < 100:
                projets.append(proj_name)
    
    # Limitation à 5 projets
    projets = projets[:5]
    
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
    
    if infos['resume']:
        print(f"\n📝 RÉSUMÉ:")
        print(f"   {infos['resume']}")
    else:
        print(f"\n📝 RÉSUMÉ: (vide)")
    
    if infos['projets']:
        print(f"\n💡 PROJETS:")
        print(f"   {infos['projets']}")
    else:
        print(f"\n💡 PROJETS: (aucun)")
    
    if infos['description_experience']:
        print(f"\n🏢 EXPÉRIENCE:")
        preview = infos['description_experience'][:200]
        print(f"   {preview}...")
    else:
        print(f"\n🏢 EXPÉRIENCE: (vide)")