"""
============================================================================
SMARTHIRE - Search Orchestrator (CORRIGÉ)
✅ Imports corrigés
✅ Utilise SearchQueryProcessor
============================================================================
"""

import logging
from typing import Dict, List, Optional

from backend.search.boolean_search import BooleanSearchModel
from backend.search.filter_processor import FilterProcessor
from backend.search.query_processor import SearchQueryProcessor  # ✅ CORRIGÉ

logger = logging.getLogger(__name__)

# ========================================================
# ORCHESTRATEUR
# ========================================================
class SearchOrchestrator:
    """Décide automatiquement quel modèle utiliser"""
    
    def __init__(self):
        self.boolean_model = BooleanSearchModel()
        self.query_processor = SearchQueryProcessor()  # ✅ CORRIGÉ
        self.filter_processor = FilterProcessor()
    
    def search(
        self,
        query: str = "",
        filters: Dict = None,
        target: str = "cvs",
        mode: str = "auto",
        auto_extract: bool = True
    ) -> Dict:
        """
        Point d'entrée principal
        
        Args:
            query: "python django senior casablanca"
            filters: {"experience": [5,10]}
            target: "cvs" ou "offres"
            mode: "auto", "boolean", "vectoriel", "hybrid"
            auto_extract: Si True, extrait skills/locations depuis query
            
        Returns:
            {
                "mode_used": "boolean",
                "results": [...],
                "stats": {...}
            }
        """
        logger.info(f"🔍 Recherche: query='{query}', filters={filters}")
        
        # 1️⃣ PRÉTRAITEMENT QUERY
        processed_query = {}
        enriched_filters = filters or {}
        
        if query:
            processed_query = self.query_processor.process(query)
            logger.info(f"   Query processed:")
            logger.info(f"     • Tokens: {processed_query['tokens'][:5]}")
            logger.info(f"     • Skills: {processed_query['skills']}")
            logger.info(f"     • Locations: {processed_query['locations']}")
            
            # 2️⃣ AUTO-EXTRACTION
            if auto_extract:
                enriched_filters = self._merge_query_into_filters(
                    processed_query,
                    enriched_filters
                )
                logger.info(f"   Filters enrichis: {enriched_filters}")
        
        # 3️⃣ DÉCISION MODE
        if mode == "auto":
            mode = self._decide_mode(query, processed_query, enriched_filters)
        
        logger.info(f"   Mode sélectionné: {mode.upper()}")
        
        # 4️⃣ EXÉCUTION
        if mode == "boolean":
            return self._search_boolean(processed_query, enriched_filters, target)
        elif mode == "vectoriel":
            return self._search_vectoriel(query, target)
        elif mode == "hybrid":
            return self._search_hybrid(query, processed_query, enriched_filters, target)
        else:
            raise ValueError(f"Mode inconnu: {mode}")
    
    def _merge_query_into_filters(
        self,
        processed_query: Dict,
        filters: Dict
    ) -> Dict:
        """Fusionne skills/locations détectés dans query avec filters"""
        enriched = dict(filters)
        
        # 1. Skills
        detected_skills = processed_query.get("skills", [])
        if detected_skills:
            if "skills" in enriched:
                existing = set(enriched["skills"])
                existing.update(detected_skills)
                enriched["skills"] = list(existing)
            else:
                enriched["skills"] = detected_skills
        
        # 2. Locations
        detected_locations = processed_query.get("locations", [])
        if detected_locations:
            if "location" in enriched:
                existing = set(enriched["location"])
                existing.update(detected_locations)
                enriched["location"] = list(existing)
            else:
                enriched["location"] = detected_locations
        
        # 3. Levels
        detected_levels = processed_query.get("levels", [])
        if detected_levels:
            if "level" in enriched:
                existing = set(enriched["level"])
                existing.update(detected_levels)
                enriched["level"] = list(existing)
            else:
                enriched["level"] = detected_levels
        
        return enriched
    
    def _decide_mode(
        self,
        query: str,
        processed_query: Dict,
        filters: Dict
    ) -> str:
        """Décide automatiquement le mode"""
        has_query = bool(query and query.strip())
        has_filters = bool(filters and len(filters) > 0)
        
        if has_query and has_filters:
            logger.info("→ Détection: Query + Filtres → HYBRIDE")
            return "hybrid"
        
        if has_filters and not has_query:
            logger.info("→ Détection: Filtres seuls → BOOLÉEN")
            return "boolean"
        
        if has_query and not has_filters:
            nb_tokens = len(processed_query.get("tokens", []))
            
            if nb_tokens <= 3:
                logger.info(f"→ Détection: Query courte ({nb_tokens} tokens) → BOOLÉEN")
                return "boolean"
            else:
                logger.info(f"→ Détection: Query longue ({nb_tokens} tokens) → VECTORIEL")
                return "vectoriel"
        
        logger.info("→ Détection: Par défaut → BOOLÉEN")
        return "boolean"
    
    def _search_boolean(
        self,
        processed_query: Dict,
        filters: Dict,
        target: str
    ) -> Dict:
        """Recherche booléenne pure"""
        logger.info("🔍 Exécution: BOOLÉEN")
        
        query_terms = {
            "must_have": processed_query.get("tokens", []),
            "should_have": [],
            "must_not_have": []
        }
        
        results = self.boolean_model.search(
            query_terms=query_terms,
            filters=filters or {},
            target=target
        )
        
        return {
            "mode_used": "boolean",
            "results": results,
            "stats": {
                "total": len(results),
                "source_breakdown": self._count_sources(results),
                "query_terms": query_terms,
                "filters_applied": filters
            }
        }
    
    def _search_vectoriel(self, query: str, target: str) -> Dict:
        """Recherche vectorielle pure (TF-IDF)"""
        logger.info("🔍 Exécution: VECTORIEL")
        
        return {
            "mode_used": "vectoriel",
            "results": [],
            "stats": {
                "total": 0,
                "note": "Vectoriel à implémenter"
            }
        }
    
    def _search_hybrid(
        self,
        query: str,
        processed_query: Dict,
        filters: Dict,
        target: str
    ) -> Dict:
        """Recherche hybride: Booléen (filtre) + Vectoriel (classe)"""
        logger.info("🔍 Exécution: HYBRIDE")
        
        boolean_results = self._search_boolean(
            processed_query,
            filters,
            target
        )["results"]
        
        if not boolean_results:
            logger.warning("⚠️ Aucun résultat après filtrage booléen")
            return {
                "mode_used": "hybrid",
                "results": [],
                "stats": {"total": 0, "note": "Filtres trop stricts"}
            }
        
        return {
            "mode_used": "hybrid",
            "results": boolean_results,
            "stats": {
                "total": len(boolean_results),
                "note": "Hybride simplifié (vectoriel à implémenter)"
            }
        }
    
    def _count_sources(self, results: List[Dict]) -> Dict:
        """Compte les sources des résultats"""
        counts = {"systeme": 0, "uploaded": 0}
        for r in results:
            if r.get("source_type") == "systeme":
                counts["systeme"] += 1
            elif r.get("source_type") == "uploaded":
                counts["uploaded"] += 1
        return counts


# ========================================================
# API PUBLIQUE
# ========================================================
def search(
    query: str = "",
    filters: Dict = None,
    target: str = "cvs",
    mode: str = "auto"
) -> Dict:
    """API publique de recherche"""
    orchestrator = SearchOrchestrator()
    return orchestrator.search(query, filters, target, mode)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🚀 TEST ORCHESTRATEUR")
    print("="*80)
    
    result1 = search(
        filters={
            "skills": ["python", "java"],
            "location": ["casablanca"],
            "experience": [5, 10]
        }
    )
    print(f"   Mode: {result1['mode_used']}")
    print(f"   Résultats: {result1['stats']['total']}")
    
    print("\n✅ Tests terminés!")