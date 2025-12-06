"""
============================================================================
SMARTHIRE - Skills Extractor Module (PRODUCTION HARDENED)
Extraction robuste des compétences - Gère tous les cas limites
============================================================================
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

from backend.config.settings import SKILLS_FILE

logger = logging.getLogger(__name__)

# ========================================================
# CHARGEMENT DE LA BASE DE COMPÉTENCES
# ========================================================
class SkillsDatabase:
    """Gestion de la base de données de compétences"""
    
    def __init__(self, skills_file: Path = SKILLS_FILE):
        self.skills_file = skills_file
        self.skills: List[str] = []
        self.aliases: Dict[str, List[str]] = {}
        self.skills_lower_map: Dict[str, str] = {}
        
        self._load_skills()
    
    def _load_skills(self):
        """Charge les compétences depuis le fichier JSON"""
        try:
            if not self.skills_file.exists():
                logger.error(f"❌ Fichier skills introuvable: {self.skills_file}")
                self._load_default_skills()
                return
            
            with open(self.skills_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Aplatir toutes les catégories
            all_skills = []
            for category, skills in data.items():
                if category != "aliases" and isinstance(skills, list):
                    all_skills.extend(skills)
            
            # Récupérer les aliases
            self.aliases = data.get("aliases", {})
            
            # Créer le mapping lowercase
            for skill in all_skills:
                self.skills_lower_map[skill.lower()] = skill
            
            self.skills = all_skills
            
            logger.info(f"✅ {len(self.skills)} compétences chargées depuis {self.skills_file.name}")
            logger.info(f"✅ {len(self.aliases)} aliases chargés")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur format JSON: {e}")
            self._load_default_skills()
        except Exception as e:
            logger.error(f"❌ Erreur chargement skills: {e}")
            self._load_default_skills()
    
    def _load_default_skills(self):
        """Charge une liste minimale par défaut"""
        default_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
            "React", "Angular", "Vue.js", "Svelte", "jQuery",
            "Node.js", "Django", "Flask", "FastAPI", "Spring", "Spring Boot", "Laravel", "Express",
            ".NET", "ASP.NET",
            "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI",
            "AWS", "Azure", "GCP", "Terraform", "Ansible",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Oracle", "SQL Server",
            "Git", "SVN", "Mercurial",
            "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy",
            "REST API", "GraphQL", "gRPC", "WebSockets",
            "Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "Microservices", "Machine Learning",
            "Data Science", "Big Data", "Cloud Computing"
        ]
        
        default_aliases = {
            "JavaScript": ["JavaScript", "JS", "javascript"],
            "TypeScript": ["TypeScript", "TS", "typescript"],
            "Node.js": ["Node.js", "Node", "NodeJS", "nodejs"],
            "Kubernetes": ["Kubernetes", "k8s", "K8s"],

            "PostgreSQL": ["PostgreSQL", "Postgres", "postgres"],
            "MongoDB": ["MongoDB", "Mongo", "mongo"],
            "Machine Learning": ["Machine Learning", "ML", "ml"],
            "Artificial Intelligence": ["Artificial Intelligence", "AI", "ai"]
        }
        
        self.skills = default_skills
        self.aliases = default_aliases
        
        for skill in default_skills:
            self.skills_lower_map[skill.lower()] = skill
        
        logger.warning(f"⚠️ Utilisation de {len(default_skills)} compétences par défaut")
    
    def get_all_skills(self) -> List[str]:
        """Retourne toutes les compétences"""
        return self.skills
    
    def get_skills_set(self) -> Set[str]:
        """Retourne un set de toutes les compétences"""
        return set(self.skills)


# Instance globale
_skills_db = None

def get_skills_database() -> SkillsDatabase:
    """Retourne l'instance singleton de la base de compétences"""
    global _skills_db
    if _skills_db is None:
        _skills_db = SkillsDatabase()
    return _skills_db


# ========================================================
# PRÉTRAITEMENT DU TEXTE
# ========================================================
def pretraiter_texte(texte: str) -> str:
    """
    Nettoie et normalise le texte pour l'extraction
    
    Args:
        texte: Texte brut
        
    Returns:
        Texte nettoyé
    """
    if not texte:
        return ""
    
    # Remplace les tabulations par des espaces
    texte = texte.replace('\t', ' ')
    
    # Normalise les retours à la ligne
    texte = re.sub(r'\r\n', '\n', texte)
    
    # Supprime les espaces multiples (mais préserve les retours à la ligne)
    texte = re.sub(r' +', ' ', texte)
    
    # Supprime les retours à la ligne multiples
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    
    return texte.strip()


# ========================================================
# EXTRACTION DE COMPÉTENCES
# ========================================================
def extraire_competences(texte: str, priorite_section_skills: bool = True) -> List[str]:
    """
    Extrait les compétences techniques d'un texte de manière robuste
    
    Args:
        texte: Texte à analyser
        priorite_section_skills: Si True, priorise les skills de la section "Skills"
        
    Returns:
        Liste ordonnée de compétences trouvées
    """
    if not texte or not isinstance(texte, str):
        return []
    
    # Prétraitement
    texte = pretraiter_texte(texte)
    
    if not texte:
        return []
    
    db = get_skills_database()
    skills_list = db.get_all_skills()
    aliases = db.aliases
    
    lower_text = texte.lower()
    
    # Extraction de la section Skills si demandé
    skills_section = ""
    skills_section_lower = ""
    
    if priorite_section_skills:
        # Patterns multiples pour détecter la section Skills
        patterns = [
            r"\b(?:SKILLS?|COMPÉTENCES?|TECHNICAL\s+SKILLS?|EXPERTISE|TECHNOLOGIES)\b\s*[:\-]?\s*\n(.*?)(?:\n\s*\b(?:PROJECTS?|EDUCATION|EXPERIENCE|EXPÉRIENCE|LANGUAGES?|CERTIFICATIONS?|FORMATION|ACHIEVEMENTS?|RÉALISATIONS?)\b|$)",
            r"\b(?:SKILLS?|COMPÉTENCES?)\b\s*[:\-]?\s*\n(.*?)(?:\n\s*[A-Z]{2,}|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texte, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            if match:
                skills_section = match.group(1)
                skills_section_lower = skills_section.lower()
                break
    
    # Recherche des compétences
    found = set()
    found_in_skills_section = set()
    
    for skill in skills_list:
        skill_lower = skill.lower()
        
        # Pattern avec word boundaries pour éviter les faux positifs
        # Gère aussi les cas avec points (Node.js, Vue.js, etc.)
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        
        try:
            # Recherche dans le texte complet
            if re.search(pattern, lower_text):
                found.add(skill)
                
                # Recherche dans la section Skills
                if skills_section_lower and re.search(pattern, skills_section_lower):
                    found_in_skills_section.add(skill)
                continue
            
            # Recherche via aliases
            for alias in aliases.get(skill, []):
                alias_pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(alias_pattern, lower_text):
                    found.add(skill)
                    if skills_section_lower and re.search(alias_pattern, skills_section_lower):
                        found_in_skills_section.add(skill)
                    break
                    
        except re.error as e:
            logger.warning(f"⚠️ Erreur regex pour '{skill}': {e}")
            continue
    
    # Retourner: skills de la section d'abord, puis les autres (ordre préservé)
    if priorite_section_skills and found_in_skills_section:
        try:
            # Préserver l'ordre d'apparition dans le texte
            result = sorted(list(found_in_skills_section), 
                           key=lambda s: lower_text.find(s.lower()) if s.lower() in lower_text else 999999)
            
            other_skills = sorted(list(found - found_in_skills_section),
                                 key=lambda s: lower_text.find(s.lower()) if s.lower() in lower_text else 999999)
            
            result.extend(other_skills)
            return result
        except Exception as e:
            logger.warning(f"⚠️ Erreur tri: {e}")
            return list(found)
    
    # Si pas de section Skills, retourner par ordre d'apparition
    try:
        return sorted(list(found), 
                     key=lambda s: lower_text.find(s.lower()) if s.lower() in lower_text else 999999)
    except Exception as e:
        logger.warning(f"⚠️ Erreur tri final: {e}")
        return list(found)


def extraire_competences_avec_stats(texte: str) -> Dict:
    """
    Extrait les compétences avec statistiques détaillées
    
    Returns:
        Dictionnaire avec compétences et statistiques
    """
    if not texte or not isinstance(texte, str):
        return {
            'competences': [],
            'nb_competences': 0,
            'has_skills_section': False,
            'preview': ''
        }
    
    competences = extraire_competences(texte, priorite_section_skills=True)
    
    # Détecte si une section Skills existe (pattern robuste)
    # Utilise un contexte plus strict pour éviter les faux positifs
    has_skills_section = bool(re.search(
        r"(?:^|\n)\s*(?:SKILLS?|COMPÉTENCES?|TECHNICAL\s+SKILLS?|EXPERTISE|TECHNOLOGIES)\s*[:\-]?",
        texte,
        re.IGNORECASE | re.MULTILINE
    ))
    
    return {
        'competences': competences,
        'nb_competences': len(competences),
        'has_skills_section': has_skills_section,
        'preview': ', '.join(competences[:5]) + ('...' if len(competences) > 5 else '')
    }


def categoriser_competences(competences: List[str]) -> Dict[str, List[str]]:
    """
    Catégorise les compétences par type
    
    Returns:
        Dictionnaire {categorie: [competences]}
    """
    if not competences:
        return {}
    
    db = get_skills_database()
    
    # Charger les catégories depuis le JSON
    categories = {}
    try:
        with open(db.skills_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for category, skills in data.items():
            if category != "aliases" and isinstance(skills, list):
                for skill in competences:
                    if skill.lower() in [s.lower() for s in skills]:
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(skill)
    except Exception as e:
        logger.warning(f"⚠️ Impossible de catégoriser: {e}")
    
    return categories


# ========================================================
# VALIDATION DE COMPÉTENCES
# ========================================================
def valider_competence(skill: str) -> bool:
    """
    Vérifie si une compétence existe dans la base
    
    Args:
        skill: Nom de la compétence
        
    Returns:
        True si valide
    """
    if not skill or not isinstance(skill, str):
        return False
    
    db = get_skills_database()
    
    # Vérifie en lowercase
    skill_lower = skill.lower().strip()
    
    if skill_lower in db.skills_lower_map:
        return True
    
    # Vérifie dans les aliases
    for main_skill, alias_list in db.aliases.items():
        if skill_lower in [a.lower() for a in alias_list]:
            return True
    
    return False




def normaliser_competence(skill: str) -> str:
    """
    Normalise une compétence (casse correcte)
    Convertit les aliases vers le nom principal
    
    Args:
        skill: Nom de la compétence (peut être un alias comme 'k8s')
        
    Returns:
        Nom normalisé (ex: 'k8s' → 'Kubernetes')
    """
    if not skill or not isinstance(skill, str):
        return skill
    
    db = get_skills_database()
    skill_lower = skill.lower().strip()
    
    # 1️⃣ Recherche directe dans le mapping principal
    if skill_lower in db.skills_lower_map:
        return db.skills_lower_map[skill_lower]
    
    # 2️⃣ Recherche dans les aliases
    for main_skill, alias_list in db.aliases.items():
        for alias in alias_list:
            if skill_lower == alias.lower():
                # Retourner le nom correctement formaté
                main_skill_lower = main_skill.lower()
                if main_skill_lower in db.skills_lower_map:
                    return db.skills_lower_map[main_skill_lower]
                return main_skill
    
    # 3️⃣ Pas trouvé, retourner tel quel
    return skill


# ========================================================
# FONCTIONS D'ANALYSE AVANCÉES
# ========================================================
def comparer_competences(skills_cv: List[str], skills_offre: List[str]) -> Dict:
    """
    Compare les compétences d'un CV avec celles d'une offre
    
    Args:
        skills_cv: Compétences du CV
        skills_offre: Compétences de l'offre
        
    Returns:
        Dictionnaire avec match, manquantes, extras
    """
    if not skills_cv:
        skills_cv = []
    if not skills_offre:
        skills_offre = []
    
    set_cv = set(s.lower().strip() for s in skills_cv if s)
    set_offre = set(s.lower().strip() for s in skills_offre if s)
    
    match = set_cv & set_offre
    manquantes = set_offre - set_cv
    extras = set_cv - set_offre
    
    taux_match = (len(match) / len(set_offre) * 100) if set_offre else 0
    
    return {
        'match': sorted(list(match)),
        'nb_match': len(match),
        'manquantes': sorted(list(manquantes)),
        'nb_manquantes': len(manquantes),
        'extras': sorted(list(extras)),
        'nb_extras': len(extras),
        'taux_match': round(taux_match, 2)
    }