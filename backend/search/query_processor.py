"""
============================================================================
SMARTHIRE - Search Query Processor (RENOMMÉ)
Normalisation et prétraitement des requêtes de recherche
============================================================================
"""

import re
import logging
from typing import List, Dict, Set, Optional

# ✅ CORRECTION: Éviter conflit avec QueryProcessor de query_indexer
from backend.config.settings import MOROCCAN_CITIES, CUSTOM_STOPWORDS
from backend.extraction.skills_extractor import get_skills_database, extraire_competences
from backend.indexation.preprocessing import pretraiter_texte, nettoyer_texte_brut

logger = logging.getLogger(__name__)

# ========================================================
# CLASSE RENOMMÉE POUR ÉVITER CONFLIT
# ========================================================
class SearchQueryProcessor:  # ✅ Renommé de QueryProcessor
    """
    Normalise et prépare les requêtes de RECHERCHE
    
    ⚠️ Différent de QueryIndexProcessor (indexation des requêtes)
    """
    
    def __init__(self):
        self.skills_db = get_skills_database()
        self.aliases = self.skills_db.aliases
        self.skills_set = self.skills_db.get_skills_set()
        self.cities = MOROCCAN_CITIES
        self.custom_stopwords = CUSTOM_STOPWORDS
        
        logger.info(f"✅ SearchQueryProcessor initialisé")
    
    def normalize(self, text: str) -> str:
        """Normalise via nettoyer_texte_brut() EXISTANT"""
        if not text:
            return ""
        return nettoyer_texte_brut(text)
    
    def preprocess_nlp(self, text: str, preserve_skills: bool = True) -> tuple:
        """Pipeline NLP complet via pretraiter_texte() EXISTANT"""
        if not text:
            return "", []
        
        texte_pretraite, tokens = pretraiter_texte(
            text,
            preserve_skills=preserve_skills,
            skills_list=self.skills_set
        )
        
        return texte_pretraite, tokens
    
    def extract_skills(self, text: str) -> List[str]:
        """Extrait compétences via extraire_competences() EXISTANT"""
        if not text:
            return []
        return extraire_competences(text, priorite_section_skills=False)
    
    def detect_cities(self, tokens: List[str]) -> List[str]:
        """Détecte villes marocaines via MOROCCAN_CITIES EXISTANT"""
        detected = []
        
        for token in tokens:
            token_lower = token.lower()
            if token_lower in self.cities:
                detected.append(self.cities[token_lower])
        
        return detected
    
    def expand_aliases(self, tokens: List[str]) -> List[str]:
        """Remplace aliases par formes principales"""
        expanded = []
        
        for token in tokens:
            token_lower = token.lower()
            found = False
            
            for main_skill, alias_list in self.aliases.items():
                if token_lower in [a.lower() for a in alias_list]:
                    expanded.append(main_skill.lower())
                    found = True
                    break
            
            if not found:
                expanded.append(token)
        
        return expanded
    
    def process(self, query: str) -> Dict:
        """Pipeline complet utilisant UNIQUEMENT le code existant"""
        if not query or not isinstance(query, str):
            return self._empty_result()
        
        # 1️⃣ NETTOYAGE (CODE EXISTANT)
        normalized = self.normalize(query)
        
        if not normalized:
            return self._empty_result()
        
        # 2️⃣ PIPELINE NLP (CODE EXISTANT)
        texte_pretraite, tokens_nlp = self.preprocess_nlp(
            normalized,
            preserve_skills=True
        )
        
        # 3️⃣ EXTRACTION SKILLS (CODE EXISTANT)
        skills_detected = self.extract_skills(normalized)
        
        # 4️⃣ EXPANSION ALIASES
        tokens_expanded = self.expand_aliases(tokens_nlp)
        
        # 5️⃣ DÉTECTION VILLES (CODE EXISTANT)
        cities_detected = self.detect_cities(tokens_nlp)
        
        # 6️⃣ DÉTECTION NIVEAUX
        levels_detected = self._detect_levels(tokens_nlp)
        
        return {
            "original": query,
            "normalized": normalized,
            "texte_pretraite": texte_pretraite,
            "tokens": tokens_nlp,
            "tokens_expanded": tokens_expanded,
            "skills": skills_detected,
            "locations": cities_detected,
            "levels": levels_detected,
            "has_skills": len(skills_detected) > 0,
            "has_location": len(cities_detected) > 0,
            "has_level": len(levels_detected) > 0
        }
    
    def _detect_levels(self, tokens: List[str]) -> List[str]:
        """Détecte niveaux d'expérience"""
        levels = {"junior", "mid-level", "intermediaire", "senior", "expert", "lead", "debutant"}
        detected = []
        
        for token in tokens:
            if token.lower() in levels:
                detected.append(token.lower())
        
        return detected
    
    def _empty_result(self) -> Dict:
        """Résultat vide"""
        return {
            "original": "",
            "normalized": "",
            "texte_pretraite": "",
            "tokens": [],
            "tokens_expanded": [],
            "skills": [],
            "locations": [],
            "levels": [],
            "has_skills": False,
            "has_location": False,
            "has_level": False
        }


# ========================================================
# API PUBLIQUE
# ========================================================
def process_query(query: str) -> Dict:
    """API simple pour prétraiter une requête de recherche"""
    processor = SearchQueryProcessor()
    return processor.process(query)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🔍 TEST SEARCH QUERY PROCESSOR")
    print("="*80)
    
    processor = SearchQueryProcessor()
    
    test1 = "Dev Senior Python Django, Casablanca"
    result1 = processor.process(test1)
    
    print(f"Input:           {result1['original']}")
    print(f"Normalized:      {result1['normalized']}")
    print(f"Skills détectés: {result1['skills']}")
    print(f"Locations:       {result1['locations']}")
    print(f"Levels:          {result1['levels']}")
    
    print("\n✅ Tests terminés!")