!pip install whoosh PyPDF2 nltk -q

import os
import re
import shutil
import json
import string
import logging
from typing import List, Dict, Optional

from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.writing import AsyncWriter
from PyPDF2 import PdfReader

# Imports NLTK
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Téléchargements NLTK
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    logger.info("✅ NLTK data téléchargées avec succès")
except Exception as e:
    logger.error(f"❌ Erreur téléchargement NLTK: {e}")

# ========================================================
# CHEMINS ET CONFIGURATION
# ========================================================
CV_FOLDER = "/content/drive/MyDrive/CV_Generated"
INDEX_DIR = "/content/drive/MyDrive/SmartHire_INDEX_VRAI"
CV_INDEX = os.path.join(INDEX_DIR, "cv")

# Créer les dossiers si nécessaire
os.makedirs(INDEX_DIR, exist_ok=True)

# Initialisation NLTK
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# ========================================================
# SCHÉMA D'INDEXATION ENRICHI
# ========================================================
schema = Schema(
    doc_id=ID(stored=True, unique=True),
    nom=TEXT(stored=True),
    titre_profil=TEXT(stored=True),
    localisation=TEXT(stored=True),
    annees=NUMERIC(stored=True, sortable=True),
    description_experience=TEXT(stored=True),
    competences=KEYWORD(commas=True, lowercase=True, stored=True),
    projets=TEXT(stored=True),
    resume_complet=TEXT(stored=True)
)

# ========================================================
# LISTE DES COMPÉTENCES
# ========================================================
SKILLS = [
    "python", "java", "kotlin", "javascript", "react", "react native", 
    "node.js", "express", "flutter", "android", "ios", "go", "spring", 
    "django", "flask", "sql", "postgresql", "mongodb", "docker", 
    "kubernetes", "terraform", "aws", "gcp", "azure", "jenkins", 
    "git", "gitlab", "github", "microservices", "graphql", "rabbitmq", 
    "redis", "websocket", "ml", "ai", "nlp", "tensorflow", "pytorch", 
    "scikit-learn", "pandas", "power bi", "tableau", "c++", "c#", 
    "php", "ruby", "scala", "rust", "typescript", "vue", "angular", 
    "svelte", "fastapi", "nextjs", "tailwind", "bootstrap", "jest",
    "pytest", "selenium", "unity", "unreal", "figma", "sketch"
]

# Map des alias pour meilleure détection
SKILL_ALIASES = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js"],
    "react": ["react", "reactjs", "react.js"],
    "node.js": ["node.js", "node", "nodejs"],
    "typescript": ["typescript", "ts"],
    "ml": ["machine learning", "ml"],
    "ai": ["artificial intelligence", "ai"],
    "nlp": ["nlp", "natural language processing"],
    "power bi": ["power bi", "powerbi"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp"],
    "react native": ["react native", "react-native", "reactnative"],
}

# Villes marocaines étendues
MOROCCAN_CITIES = {
    "casablanca": "Casablanca",
    "rabat": "Rabat",
    "marrakech": "Marrakech",
    "fes": "Fès",
    "fès": "Fès",
    "tangier": "Tanger",
    "tanger": "Tanger",
    "agadir": "Agadir",
    "meknes": "Meknès",
    "meknès": "Meknès",
    "sale": "Salé",
    "salé": "Salé",
    "kenitra": "Kénitra",
    "kénitra": "Kénitra",
    "oujda": "Oujda",
    "tetouan": "Tétouan",
    "tétouan": "Tétouan",
    "safi": "Safi",
    "mohammedia": "Mohammedia",
    "el jadida": "El Jadida",
    "beni mellal": "Beni Mellal",
    "nador": "Nador",
}

# ========================================================
# FONCTIONS D'EXTRACTION DE TEXTE
# ========================================================

def lire_pdf_propre(path: str) -> str:
    """
    Lit et nettoie le texte d'un PDF
    
    Args:
        path: Chemin vers le fichier PDF
        
    Returns:
        Texte nettoyé du PDF
    """
    try:
        text = ""
        reader = PdfReader(path)
        
        for page in reader.pages:
            t = page.extract_text()
            if t: 
                text += t + " "
        
        if not text.strip():
            logger.warning(f"PDF vide ou non lisible: {path}")
            return ""
        
        # Nettoyage du texte
        text = re.sub(r'\\[a-zA-Z]+\{.*?\}', ' ', text)  # Commandes LaTeX
        text = re.sub(r'Email\s*[: ].*?(\s|$)', ' ', text, flags=re.I)
        text = re.sub(r'Mobile\s*[: ].*?(\s|$)', ' ', text, flags=re.I)
        text = re.sub(r'Phone\s*[: ].*?(\s|$)', ' ', text, flags=re.I)
        text = re.sub(r'\s+', ' ', text)  # Espaces multiples
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Erreur lecture PDF {path}: {e}")
        return ""

# ========================================================
# FONCTIONS D'EXTRACTION D'INFORMATIONS
# ========================================================

def get_nom(text: str) -> str:
    """Extrait le nom du candidat avec validation"""
    if not text:
        return "Candidat"
    
    # 1️⃣ Cherche après \Large (format LaTeX)
    match = re.search(r"Large\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text)
    if match: 
        nom = match.group(1).strip()
        if 2 <= len(nom.split()) <= 4:
            return nom
    
    # 2️⃣ Cherche au début du document
    debut = text[:200]
    match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})", debut)
    if match: 
        nom = match.group(1).strip()
        excluded_words = ["summary", "objective", "professional", "experience", 
                         "skills", "education", "profile"]
        if nom.lower() not in excluded_words:
            return nom
    
    # 3️⃣ Cherche avant "Experience"
    match = re.search(r"((?:[A-Z][a-z]+\s+)+)(?:Experience|EXPERIENCE|Expérience)", text)
    if match: 
        nom = match.group(1).strip()
        words = nom.split()
        if 2 <= len(words) <= 3:
            return nom
    
    # 4️⃣ Cherche après "CV" ou "Curriculum"
    match = re.search(r"(?:CV|Curriculum\s+Vitae)\s*[:\-]?\s*(.*?)\n", text, re.I)
    if match:
        candidates = match.group(1).split()
        if len(candidates) >= 2 and candidates[0][0].isupper():
            return " ".join(candidates[:2])
    
    return "Candidat"


def get_titre_profil(text: str) -> str:
    """Extrait le titre du profil professionnel"""
    if not text:
        return "Professional"
    
    job_keywords = [
        "developer", "engineer", "manager", "analyst", "architect", 
        "specialist", "lead", "senior", "junior", "designer", 
        "officer", "consultant", "administrator", "director"
    ]
    
    # 1️⃣ Après le nom (ligne suivante)
    match = re.search(
        r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*\n\s*([A-Z][a-zA-Z\s\-/+\.]{5,80}?)(?:\n|$)", 
        text, 
        re.MULTILINE
    )
    if match:
        title = match.group(1).strip()
        if any(kw in title.lower() for kw in job_keywords):
            return title
    
    # 2️⃣ Pattern "Titre | Location"
    match = re.search(r"^([A-Z][a-zA-Z\s\-/+\.]{5,80}?)\s*\|\s*(?:\d+|[A-Z])", text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        if any(kw in title.lower() for kw in job_keywords):
            return title
    
    # 3️⃣ Dans la section Experience
    match = re.search(r"(?:Experience|Expérience)\s*[:\-]?\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
    if match:
        block = match.group(1)
        job_match = re.search(r"([A-Z][a-zA-Z\s\-/+\.]{5,80}?)\s*(?:\||,|\n)", block)
        if job_match:
            title = job_match.group(1).strip()
            if any(kw in title.lower() for kw in job_keywords):
                return title
    
    return "Professional"


def get_annees(text: str) -> int:
    """
    Extrait le nombre d'années d'expérience avec validation
    
    Returns:
        Nombre d'années (0-50)
    """
    if not text:
        return 0
    
    # 1️⃣ Recherche explicite "X years"
    match = re.search(r"(\d+)\+?\s*(?:years?|ans|year|an)\s+(?:of\s+)?(?:experience|expérience)", text, re.I)
    if match:
        years = int(match.group(1))
        return min(years, 50)  # Cap à 50 ans
    
    # 2️⃣ Calcul depuis les dates
    total = 0
    dates = re.findall(
        r"(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(Present|Current|Aujourd'hui|Actuel|\w+\s+\d{4}|\d{4})",
        text
    )
    
    for start, end in dates:
        try:
            y1 = int(re.search(r"\d{4}", start).group())
            
            # Validation de l'année de début
            if y1 < 1970 or y1 > 2025:
                continue
            
            if any(x in end.lower() for x in ["present", "current", "actuel", "aujourd'hui"]):
                y2 = 2025
            else:
                y2 = int(re.search(r"\d{4}", end).group())
                if y2 < 1970 or y2 > 2025:
                    continue
            
            if y2 >= y1:
                total += (y2 - y1)
        except:
            continue
    
    # Validation finale
    if total > 50:
        total = 50
    
    return max(total, 0)


def get_competences(text: str) -> List[str]:
    """
    Extrait les compétences avec priorité à la section Skills
    
    Returns:
        Liste ordonnée de compétences
    """
    if not text:
        return []
    
    lower = text.lower()
    
    # Extraction de la section Skills
    match = re.search(
        r"(?:skills|compétences|technical\s+skills|expertise)\s*[:\-]?\s*(.*?)(?:Projects|Education|Experience|Languages|Certifications|$)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    skills_section = match.group(1) if match else ""
    skills_section_lower = skills_section.lower()
    
    found = set()
    found_in_skills_section = set()
    
    # Recherche des compétences
    for skill in SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        
        # Recherche dans tout le CV
        if re.search(pattern, lower):
            found.add(skill)
            if re.search(pattern, skills_section_lower):
                found_in_skills_section.add(skill)
        else:
            # Recherche des alias
            for alias in SKILL_ALIASES.get(skill, []):
                alias_pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(alias_pattern, lower):
                    found.add(skill)
                    if re.search(alias_pattern, skills_section_lower):
                        found_in_skills_section.add(skill)
                    break
    
    # Tri: compétences de la section Skills en premier
    result = list(found_in_skills_section) + list(found - found_in_skills_section)
    return result


def get_localisation(text: str) -> str:
    """Extrait la localisation du candidat"""
    if not text:
        return "Maroc"
    
    lower = text.lower()
    
    for ville_lower, ville_proper in MOROCCAN_CITIES.items():
        if ville_lower in lower:
            return ville_proper
    
    return "Maroc"


def get_resume_complet(text: str) -> str:
    """Extrait le résumé professionnel"""
    if not text:
        return ""
    
    match = re.search(
        r"(?:Summary|Objective|Professional\s+Summary|Résumé|Professionnel)\s*[:\-]?\s*(.*?)(?:Experience|Skills|Education|Expérience|Compétences|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        resume = match.group(1).strip()
        resume = re.sub(r'\s+', ' ', resume)[:500]
        return resume if len(resume) > 20 else ""
    
    return ""


def get_description_experience(text: str) -> str:
    """Extrait la description de l'expérience"""
    if not text:
        return ""
    
    match = re.search(
        r"(?:Experience|Expérience)\s*[:\-]?\s*(.*?)(?:Skills|Education|Projects|Certifications|Compétences|Formation|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    if match:
        experience = match.group(1).strip()
        experience = re.sub(r'\s+', ' ', experience)[:1000]
        return experience if len(experience) > 20 else ""
    
    return ""


def get_projets(text: str) -> str:
    """Extrait les noms des projets"""
    if not text:
        return ""
    
    match = re.search(
        r"Projects?\s*[:\-]?(.*?)(?:Skills|Education|Certifications|Languages|$)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    if not match: 
        return ""
    
    block = match.group(1)
    
    projets = re.findall(
        r"([A-Z][\w\s\-\(\)]{10,100}(?:Application|Dashboard|System|Model|Platform|App|API|Website|Tool|Service|Portal|Solution|Framework))",
        block
    )
    
    projets = [p.strip() for p in projets[:5]]
    return " | ".join(projets) if projets else ""


# ========================================================
# FONCTION PRINCIPALE D'INDEXATION
# ========================================================

def indexer_cvs():
    """Fonction principale d'indexation des CV"""
    
    logger.info("="*120)
    logger.info("DÉBUT DE L'INDEXATION DES CV")
    logger.info("="*120)
    
    # Suppression de l'ancien index
    if os.path.exists(CV_INDEX):
        shutil.rmtree(CV_INDEX)
        logger.info(f"✅ Ancien index supprimé: {CV_INDEX}")
    
    os.makedirs(CV_INDEX)
    
    # Création de l'index
    ix = create_in(CV_INDEX, schema)
    writer = AsyncWriter(ix)
    
    # Récupération des fichiers PDF
    try:
        cv_files = sorted([x for x in os.listdir(CV_FOLDER) if x.endswith(".pdf")])
        total_cvs = len(cv_files)
        logger.info(f"📁 {total_cvs} CV trouvés dans {CV_FOLDER}\n")
    except FileNotFoundError:
        logger.error(f"❌ Dossier introuvable: {CV_FOLDER}")
        return
    
    # Compteurs
    success_count = 0
    error_count = 0
    
    # Traitement de chaque CV
    for i, filename in enumerate(cv_files, 1):
        filepath = os.path.join(CV_FOLDER, filename)
        
        try:
            # Extraction du texte
            texte = lire_pdf_propre(filepath)
            
            if not texte:
                logger.warning(f"{i:02d}/{total_cvs} → ⚠️ CV vide: {filename}")
                error_count += 1
                continue
            
            # Extraction des informations
            nom = get_nom(texte)
            titre_profil = get_titre_profil(texte)
            annees = get_annees(texte)
            competences = get_competences(texte)
            projets = get_projets(texte)
            loc = get_localisation(texte)
            description_exp = get_description_experience(texte)
            resume = get_resume_complet(texte)
            
            # Indexation
            writer.add_document(
                doc_id=filename,
                nom=nom,
                titre_profil=titre_profil,
                localisation=loc,
                annees=annees,
                description_experience=description_exp,
                competences=",".join(competences),
                projets=projets,
                resume_complet=resume
            )
            
            # Affichage
            skills_list = ", ".join(competences[:5]) + ("..." if len(competences) > 5 else "")
            projets_count = len([p for p in projets.split("|") if p.strip()])
            resume_preview = (resume[:50] + "...") if len(resume) > 50 else resume
            
            print(f"\n{i:02d}/{total_cvs} {'='*100}")
            print(f"  👤 NOM:              {nom}")
            print(f"  💼 TITRE:            {titre_profil}")
            print(f"  📍 LOCALISATION:     {loc}")
            print(f"  📅 EXPÉRIENCE:       {annees} ans")
            print(f"  🛠️  COMPÉTENCES:      {len(competences)} skills → {skills_list}")
            print(f"  📌 PROJETS:          {projets_count} projets")
            print(f"  📝 RÉSUMÉ:           {resume_preview}")
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"{i:02d}/{total_cvs} → ❌ ERREUR: {filename} - {e}")
            error_count += 1
            continue
    
    # Commit des changements
    try:
        writer.commit()
        logger.info("\n" + "="*120)
        logger.info("✅ INDEXATION TERMINÉE AVEC SUCCÈS")
        logger.info("="*120)
        logger.info(f"\n📊 Résumé:")
        logger.info(f"   • CV indexés avec succès: {success_count}")
        logger.info(f"   • CV en erreur: {error_count}")
        logger.info(f"   • Total traité: {total_cvs}")
        logger.info(f"\n📁 Index sauvegardé: {CV_INDEX}")
    except Exception as e:
        logger.error(f"❌ Erreur lors du commit: {e}")


# ========================================================
# EXÉCUTION
# ========================================================

if __name__ == "__main__":
    indexer_cvs()