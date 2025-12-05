"""
============================================================================
SMARTHIRE - Skills Extractor Module
Extraction intelligente des compétences techniques depuis les CV et offres
============================================================================
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple

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
        
        self.skills = default_skills
        self.aliases = default_aliases
        
        for skill in default_skills:
            self.skills_lower_map[skill.lower()] = skill
        
        logger.warning(f"⚠️ Utilisation de {len(default_skills)} compétences par défaut")
    
    def get_all_skills(self) -> List[str]:
        """Retourne toutes les compétences"""
        return self.skills
    
    def get_skills_set(self) -> Set[str]:
        """Retourne un set de toutes les compétences (pour préservation)"""
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
# EXTRACTION DE COMPÉTENCES
# ========================================================
def extraire_competences(texte: str, priorite_section_skills: bool = True) -> List[str]:
    """
    Extrait les compétences techniques d'un texte
    
    Args:
        texte: Texte à analyser
        priorite_section_skills: Si True, priorise les skills de la section "Skills"
        
    Returns:
        Liste ordonnée de compétences trouvées
    """
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
        match = re.search(
            r"(?:skills|compétences|technical\s+skills|expertise)\s*[:\-]?\s*(.*?)(?:Projects|Education|Experience|Languages|Certifications|$)",
            texte,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            skills_section = match.group(1)
            skills_section_lower = skills_section.lower()
    
    # Recherche des compétences
    found = set()
    found_in_skills_section = set()
    
    for skill in skills_list:
        # Pattern avec word boundaries
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        
        # Recherche dans le texte complet
        if re.search(pattern, lower_text):
            found.add(skill)
            
            # Recherche dans la section Skills
            if skills_section_lower and re.search(pattern, skills_section_lower):
                found_in_skills_section.add(skill)
        else:
            # Recherche via aliases
            for alias in aliases.get(skill, []):
                alias_pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(alias_pattern, lower_text):
                    found.add(skill)
                    if skills_section_lower and re.search(alias_pattern, skills_section_lower):
                        found_in_skills_section.add(skill)
                    break
    
    # Retourner: skills de la section d'abord, puis les autres
    result = list(found_in_skills_section) + list(found - found_in_skills_section)
    
    return result


def extraire_competences_avec_stats(texte: str) -> Dict:
    """
    Extrait les compétences avec statistiques détaillées
    
    Returns:
        Dictionnaire avec compétences et statistiques
    """
    competences = extraire_competences(texte, priorite_section_skills=True)
    
    # Détecte si une section Skills existe
    has_skills_section = bool(re.search(
        r"(?:skills|compétences|technical\s+skills)\s*[:\-]",
        texte,
        re.IGNORECASE
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
    """Vérifie si une compétence existe dans la base"""
    db = get_skills_database()
    return skill.lower() in db.skills_lower_map


def normaliser_competence(skill: str) -> str:
    """Normalise une compétence (casse correcte)"""
    db = get_skills_database()
    return db.skills_lower_map.get(skill.lower(), skill)


if __name__ == "__main__":
    # Test du module
    texte_test = """
    SKILLS
    Programming Languages: Python, Java, JavaScript, TypeScript
    Web Frameworks: React, Angular, Django, Flask, Spring Boot
    Databases: PostgreSQL, MongoDB, Redis
    DevOps: Docker, Kubernetes, AWS, Jenkins
    Machine Learning: TensorFlow, PyTorch, scikit-learn
    
    EXPERIENCE
    Developed microservices using Node.js and Express
    Implemented CI/CD pipelines with GitLab CI
    """
    
    print("="*80)
    print("TEST DU MODULE SKILLS EXTRACTOR")
    print("="*80)
    
    # Extraction simple
    print("\n1️⃣ EXTRACTION SIMPLE:")
    competences = extraire_competences(texte_test)
    print(f"   Trouvé: {len(competences)} compétences")
    print(f"   Liste: {', '.join(competences[:10])}")
    
    # Extraction avec stats
    print("\n2️⃣ EXTRACTION AVEC STATISTIQUES:")
    stats = extraire_competences_avec_stats(texte_test)
    print(f"   Nombre: {stats['nb_competences']}")
    print(f"   Section Skills détectée: {stats['has_skills_section']}")
    print(f"   Preview: {stats['preview']}")
    
    # Catégorisation
    print("\n3️⃣ CATÉGORISATION:")
    categories = categoriser_competences(competences)
    for cat, skills in categories.items():
        print(f"   {cat}: {len(skills)} skills")
    
    # Validation
    print("\n4️⃣ VALIDATION:")
    test_skills = ["python", "react", "fakeSkill123"]
    for skill in test_skills:
        valid = valider_competence(skill)
        print(f"   {skill}: {'✅ Valide' if valid else '❌ Invalide'}")