!pip install whoosh PyPDF2 nltk -q

import os
import re
import shutil
import json
import string
import logging
from typing import List, Dict, Optional, Tuple

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
    nltk.download('punkt_tab', quiet=True)  # ✅ Ajout de punkt_tab
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)  # Pour POS tagging
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

# Ajout de stopwords personnalisés pour les CV
custom_stopwords = {
    'cv', 'resume', 'curriculum', 'vitae', 'email', 'phone', 
    'mobile', 'address', 'page', 'http', 'https', 'www'
}
stop_words.update(custom_stopwords)

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
    resume_complet=TEXT(stored=True),
    # Nouveau champ pour le texte prétraité
    texte_pretraite=TEXT(stored=True)
)

# ========================================================
# CHARGEMENT DES COMPÉTENCES DEPUIS JSON
# ========================================================

SKILLS_JSON_PATH = "/content/drive/MyDrive/skills_json_file.json"

def load_skills_from_json(json_path: str = SKILLS_JSON_PATH) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Charge les compétences depuis un fichier JSON
    
    Args:
        json_path: Chemin vers le fichier JSON
        
    Returns:
        Tuple (liste_skills, dictionnaire_aliases)
    """
    try:
        if not os.path.exists(json_path):
            logger.error(f"❌ FICHIER INTROUVABLE: {json_path}")
            logger.error(f"📋 INSTRUCTIONS:")
            logger.error(f"   1. Téléchargez le fichier skills_database.json")
            logger.error(f"   2. Uploadez-le dans votre Google Drive: /MyDrive/")
            logger.error(f"   3. Relancez le script")
            logger.warning(f"⚠️ Utilisation de la liste minimale par défaut...")
            return _get_default_skills()
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Aplatir toutes les catégories en une seule liste
        all_skills = []
        for category, skills in data.items():
            if category != "aliases" and isinstance(skills, list):
                all_skills.extend(skills)
        
        # Récupérer les aliases
        aliases = data.get("aliases", {})
        
        logger.info(f"✅ {len(all_skills)} compétences chargées depuis {json_path}")
        logger.info(f"✅ {len(aliases)} aliases chargés")
        
        return all_skills, aliases
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erreur format JSON invalide: {e}")
        logger.warning(f"⚠️ Vérifiez la syntaxe du fichier JSON")
        return _get_default_skills()
    except Exception as e:
        logger.error(f"❌ Erreur chargement JSON: {e}")
        return _get_default_skills()


def _get_default_skills() -> Tuple[List[str], Dict[str, List[str]]]:
    """Liste de compétences minimale par défaut en cas d'erreur"""
    default_skills = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "spring", "laravel", "docker", "kubernetes",
        "aws", "azure", "gcp", "postgresql", "mongodb", "redis", "git", "jenkins",
        "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn"
    ]
    
    default_aliases = {
        "javascript": ["javascript", "js"],
        "typescript": ["typescript", "ts"],
        "node.js": ["node.js", "node", "nodejs"],
        "kubernetes": ["kubernetes", "k8s"],
        "postgresql": ["postgresql", "postgres"],
        "mongodb": ["mongodb", "mongo"]
    }
    
    logger.info(f"📋 Utilisation de {len(default_skills)} compétences par défaut")
    return default_skills, default_aliases


# Chargement des compétences au démarrage
logger.info("="*80)
logger.info("🔄 CHARGEMENT DE LA BASE DE COMPÉTENCES")
logger.info("="*80)

SKILLS, SKILL_ALIASES = load_skills_from_json()

logger.info(f"📊 Total compétences disponibles: {len(SKILLS)}")
logger.info(f"📊 Total aliases: {len(SKILL_ALIASES)}")
logger.info("="*80)

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
# PRÉTRAITEMENT NLP COMPLET
# ========================================================

def pretraiter_texte(texte: str, preserve_skills: bool = True) -> Tuple[str, List[str]]:
    """
    Prétraite le texte avec le pipeline NLP complet
    
    Étapes:
    1. Extraction du texte (déjà fait par lire_pdf_propre)
    2. Passage en minuscules
    3. Suppression de la ponctuation
    4. Tokenisation
    5. Suppression des stopwords
    6. Lemmatisation
    
    Args:
        texte: Texte brut à prétraiter
        preserve_skills: Si True, conserve les compétences techniques intactes
        
    Returns:
        Tuple (texte_pretraité, tokens_prétraités)
    """
    if not texte:
        return "", []
    
    # Protection des compétences techniques (optionnel)
    protected_terms = {}
    if preserve_skills:
        for skill in SKILLS:
            # Remplacer temporairement les compétences par des placeholders
            placeholder = f"__SKILL_{skill.replace(' ', '_').replace('.', '_').upper()}__"
            pattern = r'\b' + re.escape(skill) + r'\b'
            texte = re.sub(pattern, placeholder, texte, flags=re.IGNORECASE)
            protected_terms[placeholder] = skill
    
    # ÉTAPE 1: Nettoyage préliminaire
    texte = re.sub(r'\\[a-zA-Z]+\{.*?\}', ' ', texte)  # Commandes LaTeX
    texte = re.sub(r'\d{4}-\d{4}', ' ', texte)  # Dates
    texte = re.sub(r'[^\w\s\-]', ' ', texte)  # Caractères spéciaux
    
    # ÉTAPE 2: Passage en minuscules
    texte_lower = texte.lower()
    
    # ÉTAPE 3: Suppression de la ponctuation (déjà fait partiellement ci-dessus)
    # On garde les tirets pour les mots composés
    translator = str.maketrans('', '', string.punctuation.replace('-', ''))
    texte_sans_ponctuation = texte_lower.translate(translator)
    
    # ÉTAPE 4: Tokenisation
    try:
        tokens = word_tokenize(texte_sans_ponctuation)
    except LookupError:
        # Fallback: téléchargement et retry
        logger.warning("Téléchargement punkt_tab en cours...")
        try:
            nltk.download('punkt_tab', quiet=False)
            tokens = word_tokenize(texte_sans_ponctuation)
        except:
            logger.warning("Erreur tokenisation: utilisation du split simple.")
            tokens = texte_sans_ponctuation.split()
    except Exception as e:
        logger.warning(f"Erreur tokenisation: {e}. Utilisation du split simple.")
        tokens = texte_sans_ponctuation.split()
    
    # ÉTAPE 5: Suppression des stopwords et tokens courts
    tokens_filtres = [
        token for token in tokens 
        if token not in stop_words 
        and len(token) > 2  # Mots de plus de 2 caractères
        and not token.isdigit()  # Pas de nombres purs
    ]
    
    # ÉTAPE 6: Lemmatisation
    tokens_lemmatises = []
    for token in tokens_filtres:
        try:
            lemme = lemmatizer.lemmatize(token, pos='v')  # Verbes
            lemme = lemmatizer.lemmatize(lemme, pos='n')  # Noms
            tokens_lemmatises.append(lemme)
        except Exception as e:
            tokens_lemmatises.append(token)
    
    # Restauration des compétences protégées
    tokens_finaux = []
    for token in tokens_lemmatises:
        if token in protected_terms:
            tokens_finaux.append(protected_terms[token])
        else:
            tokens_finaux.append(token)
    
    texte_pretraite = " ".join(tokens_finaux)
    
    return texte_pretraite, tokens_finaux


def pretraiter_competences(competences_list: List[str]) -> str:
    """
    Prétraite les compétences sans lemmatisation (pour préserver les noms techniques)
    
    Args:
        competences_list: Liste de compétences
        
    Returns:
        Chaîne de compétences normalisées
    """
    competences_normalisees = []
    
    for skill in competences_list:
        # Normalisation simple: minuscules et trim
        skill_norm = skill.lower().strip()
        
        # Suppression des caractères spéciaux sauf . et -
        skill_norm = re.sub(r'[^\w\s\.\-]', '', skill_norm)
        
        if skill_norm and len(skill_norm) > 1:
            competences_normalisees.append(skill_norm)
    
    return ",".join(competences_normalisees)


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
        return min(years, 50)
    
    # 2️⃣ Calcul depuis les dates
    total = 0
    dates = re.findall(
        r"(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(Present|Current|Aujourd'hui|Actuel|\w+\s+\d{4}|\d{4})",
        text
    )
    
    for start, end in dates:
        try:
            y1 = int(re.search(r"\d{4}", start).group())
            
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
    
    for skill in SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        
        if re.search(pattern, lower):
            found.add(skill)
            if re.search(pattern, skills_section_lower):
                found_in_skills_section.add(skill)
        else:
            for alias in SKILL_ALIASES.get(skill, []):
                alias_pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(alias_pattern, lower):
                    found.add(skill)
                    if re.search(alias_pattern, skills_section_lower):
                        found_in_skills_section.add(skill)
                    break
    
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
    """Fonction principale d'indexation des CV avec prétraitement NLP"""
    
    logger.info("="*120)
    logger.info("DÉBUT DE L'INDEXATION DES CV AVEC PRÉTRAITEMENT NLP")
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
            # Extraction du texte brut
            texte_brut = lire_pdf_propre(filepath)
            
            if not texte_brut:
                logger.warning(f"{i:02d}/{total_cvs} → ⚠️ CV vide: {filename}")
                error_count += 1
                continue
            
            # ✅ PRÉTRAITEMENT NLP COMPLET
            texte_pretraite, tokens = pretraiter_texte(texte_brut, preserve_skills=True)
            
            # Extraction des informations (sur texte brut pour meilleure précision)
            nom = get_nom(texte_brut)
            titre_profil = get_titre_profil(texte_brut)
            annees = get_annees(texte_brut)
            competences = get_competences(texte_brut)
            competences_pretraitees = pretraiter_competences(competences)
            projets = get_projets(texte_brut)
            loc = get_localisation(texte_brut)
            description_exp = get_description_experience(texte_brut)
            resume = get_resume_complet(texte_brut)
            
            # Indexation avec texte prétraité
            writer.add_document(
                doc_id=filename,
                nom=nom,
                titre_profil=titre_profil,
                localisation=loc,
                annees=annees,
                description_experience=description_exp,
                competences=competences_pretraitees,
                projets=projets,
                resume_complet=resume,
                texte_pretraite=texte_pretraite  # ✅ Nouveau champ
            )
            
            # Affichage
            skills_list = ", ".join(competences[:5]) + ("..." if len(competences) > 5 else "")
            projets_count = len([p for p in projets.split("|") if p.strip()])
            tokens_count = len(tokens)
            tokens_preview = " ".join(tokens[:10]) + ("..." if len(tokens) > 10 else "")
            
            print(f"\n{i:02d}/{total_cvs} {'='*100}")
            print(f"  👤 NOM:              {nom}")
            print(f"  💼 TITRE:            {titre_profil}")
            print(f"  📍 LOCALISATION:     {loc}")
            print(f"  📅 EXPÉRIENCE:       {annees} ans")
            print(f"  🛠️  COMPÉTENCES:      {len(competences)} skills → {skills_list}")
            print(f"  📌 PROJETS:          {projets_count} projets")
            print(f"  🔤 TOKENS NLP:       {tokens_count} tokens")
            print(f"  📝 PREVIEW TOKENS:   {tokens_preview}")
            
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
        logger.info(f"\n🔍 Prétraitement NLP appliqué:")
        logger.info(f"   ✓ Minuscules")
        logger.info(f"   ✓ Suppression ponctuation")
        logger.info(f"   ✓ Tokenisation")
        logger.info(f"   ✓ Suppression stopwords")
        logger.info(f"   ✓ Lemmatisation")
    except Exception as e:
        logger.error(f"❌ Erreur lors du commit: {e}")


# ========================================================
# EXÉCUTION
# ========================================================

if __name__ == "__main__":
    indexer_cvs()