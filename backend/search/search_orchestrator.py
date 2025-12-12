"""
============================================================================
SMARTHIRE - Search Orchestrator (VECTORIEL + BOOLÉEN + HYBRIDE)
============================================================================
"""

import logging
from typing import Dict, List, Optional

from search.boolean_search import BooleanSearchModel
from search.vectoriel_model import VectorielSearchModel
from search.hybrid_scorer import HybridScorer, analyze_score_distribution
from search.filter_processor import FilterProcessor
from search.query_processor import SearchQueryProcessor

logger = logging.getLogger(__name__)


# ========================================================
# ORCHESTRATEUR COMPLET
# ========================================================
class SearchOrchestrator:
    """
    Chef d'orchestre de la recherche SmartHire
    Gère 3 modes : Booléen, Vectoriel (BM25), Hybride
    """
    
    def __init__(self):
        """Initialise tous les modèles"""
        logger.info("🔧 Initialisation SearchOrchestrator...")
        
        # Modules de base
        self.query_processor = SearchQueryProcessor()
        self.filter_processor = FilterProcessor()
        
        # Modèles de recherche
        self.boolean_model = BooleanSearchModel()
        self.vectoriel_model = VectorielSearchModel()
        
        # Scorer hybride par défaut
        self.hybrid_scorer = HybridScorer(
            strategy="weighted",
            boolean_weight=0.5,
            bm25_weight=0.5
        )
        
        logger.info("✅ SearchOrchestrator initialisé (booléen + vectoriel + hybride)")
    
    def search(
        self,
        query: str = "",
        filters: Dict = None,
        target: str = "cvs",
        mode: str = "auto",
        top_k: int = 20,
        auto_extract: bool = True,
        hybrid_strategy: str = "weighted",
        boolean_weight: float = 0.5,
        bm25_weight: float = 0.5
    ) -> Dict:
        """
        Point d'entrée principal de la recherche
        
        Args:
            query: Texte de recherche libre
            filters: Dictionnaire de filtres {"skills": [...], "location": [...], ...}
            target: "cvs" ou "offres"
            mode: "auto", "boolean", "vectoriel", ou "hybrid"
            top_k: Nombre de résultats à retourner
            auto_extract: Extraire automatiquement filtres depuis query
            hybrid_strategy: "weighted", "rrf", "max", "multiplicative"
            boolean_weight: Poids booléen (si weighted)
            bm25_weight: Poids BM25 (si weighted)
            
        Returns:
            {
                "mode_used": str,
                "results": List[Dict],
                "stats": Dict,
                "config": Dict
            }
        """
        
        logger.info(f"🔍 Recherche: query='{query}', filters={filters}, mode={mode}")
        
        # 1. PRÉTRAITEMENT
        processed_query = {}
        enriched_filters = filters or {}
        
        if query:
            processed_query = self.query_processor.process(query)
            logger.info(f"   Query processed: tokens={processed_query.get('tokens', [])[:5]}")
            
            # Auto-extraction
            if auto_extract:
                enriched_filters = self._merge_query_into_filters(
                    processed_query,
                    enriched_filters
                )
                logger.info(f"   Filters enrichis: {enriched_filters}")
        
        # 2. DÉCISION MODE
        if mode == "auto":
            mode = self._decide_mode(query, processed_query, enriched_filters)
        
        logger.info(f"   Mode sélectionné: {mode.upper()}")
        
        # 3. CONFIGURATION HYBRIDE
        if mode == "hybrid":
            self.hybrid_scorer = HybridScorer(
                strategy=hybrid_strategy,
                boolean_weight=boolean_weight,
                bm25_weight=bm25_weight
            )
        
        # 4. EXÉCUTION
        if mode == "boolean":
            return self._search_boolean(
                processed_query, enriched_filters, target, top_k
            )
        
        elif mode == "vectoriel":
            return self._search_vectoriel(
                query, target, top_k
            )
        
        elif mode == "hybrid":
            return self._search_hybrid(
                query, processed_query, enriched_filters, target, top_k
            )
        
        else:
            raise ValueError(f"Mode inconnu: {mode}")
    
    def _decide_mode(
        self,
        query: str,
        processed_query: Dict,
        filters: Dict
    ) -> str:
        """
        Décide automatiquement le mode optimal
        
        Règles:
        1. Filtres seuls (pas de query) → BOOLEAN
        2. Query courte (≤3 tokens) + pas de filtres → BOOLEAN
        3. Query longue (>3 tokens) + pas de filtres → VECTORIEL
        4. Query + Filtres → HYBRID
        """
        
        has_query = bool(query and query.strip())
        has_filters = bool(filters and len(filters) > 0)
        
        # Règle 1: Filtres seuls
        if has_filters and not has_query:
            return "boolean"
        
        # Règles 2 & 3: Query seule
        if has_query and not has_filters:
            nb_tokens = len(processed_query.get("tokens", []))
            
            if nb_tokens <= 3:
                return "boolean"
            else:
                return "vectoriel"
        
        # Règle 4: Query + Filtres
        if has_query and has_filters:
            return "hybrid"
        
        # Défaut
        return "boolean"
    
    def _merge_query_into_filters(
        self,
        processed_query: Dict,
        filters: Dict
    ) -> Dict:
        """
        Enrichit automatiquement les filtres avec ce qui est extrait de la query
        """
        enriched = dict(filters)
        
        # 1. Compétences
        detected_skills = processed_query.get("skills", [])
        if detected_skills:
            if "skills" in enriched:
                existing = set(enriched["skills"])
                existing.update(detected_skills)
                enriched["skills"] = list(existing)
            else:
                enriched["skills"] = detected_skills
        
        # 2. Localisations
        detected_locations = processed_query.get("locations", [])
        if detected_locations:
            if "location" in enriched:
                existing = set(enriched["location"])
                existing.update(detected_locations)
                enriched["location"] = list(existing)
            else:
                enriched["location"] = detected_locations
        
        # 3. Niveaux
        detected_levels = processed_query.get("levels", [])
        if detected_levels:
            if "level" in enriched:
                existing = set(enriched["level"])
                existing.update(detected_levels)
                enriched["level"] = list(existing)
            else:
                enriched["level"] = detected_levels
        
        return enriched
    
    def _search_boolean(
        self,
        processed_query: Dict,
        filters: Dict,
        target: str,
        top_k: int
    ) -> Dict:
        """Mode booléen pur"""
        
        logger.info("🔍 Exécution: BOOLÉEN")
        
        # Construire query_terms depuis processed_query
        query_terms = {}
        
        if processed_query.get("skills"):
            query_terms["must_have"] = processed_query["skills"]
        
        if processed_query.get("tokens"):
            # Utiliser tokens comme should_have
            query_terms["should_have"] = processed_query.get("tokens", [])
        
        # Recherche booléenne
        results = self.boolean_model.search(
            query_terms=query_terms,
            filters=filters,
            target=target
        )
        
        # Top K
        top_results = results[:top_k]
        
        # Statistiques
        stats = {
            "mode": "boolean",
            "total_results": len(results),
            "top_k": top_k,
            "filters_applied": filters,
            "query_terms": query_terms,
            "source_breakdown": self._count_sources(results)
        }
        
        return {
            "mode_used": "boolean",
            "results": top_results,
            "stats": stats,
            "config": {"target": target}
        }
    
    def _search_vectoriel(
        self,
        query: str,
        target: str,
        top_k: int
    ) -> Dict:
        """Mode vectoriel pur (BM25)"""
        
        logger.info("🔍 Exécution: VECTORIEL")
        
        result = self.vectoriel_model.search(
            query=query,
            target=target,
            top_k=top_k
        )
        
        # Enrichir stats
        result["stats"]["mode"] = "vectoriel"
        
        return {
            "mode_used": "vectoriel",
            "results": result["results"],
            "stats": result["stats"],
            "config": {"target": target}
        }
    
    def _search_hybrid(
        self,
        query: str,
        processed_query: Dict,
        filters: Dict,
        target: str,
        top_k: int
    ) -> Dict:
        """Mode hybride: Booléen + Vectoriel fusionnés"""
        
        logger.info("🔍 Exécution: HYBRIDE")
        
        # 1. Recherche booléenne
        query_terms = {}
        if processed_query.get("skills"):
            query_terms["must_have"] = processed_query["skills"]
        
        boolean_results = self.boolean_model.search(
            query_terms=query_terms,
            filters=filters,
            target=target
        )
        
        # 2. Recherche vectorielle
        vectoriel_result = self.vectoriel_model.search(
            query=query,
            target=target,
            top_k=100  # Prendre plus pour fusion
        )
        vectoriel_results = vectoriel_result["results"]
        
        # 3. Fusion hybride
        fused_results = self.hybrid_scorer.fuse(
            boolean_results=boolean_results,
            bm25_results=vectoriel_results,
            deduplicate=True
        )
        
        # 4. Top K
        top_results = fused_results[:top_k]
        
        # 5. Statistiques
        stats = {
            "mode": "hybrid",
            "total_results": len(fused_results),
            "top_k": top_k,
            "query": query,
            "query_tokens": processed_query.get("tokens", []),
            "filters_applied": filters,
            "boolean_count": len(boolean_results),
            "vectoriel_count": len(vectoriel_results),
            "fusion_strategy": self.hybrid_scorer.strategy,
            "fusion_config": self.hybrid_scorer.get_config(),
            "source_breakdown": self._count_sources(fused_results),
            "overlap_stats": self._analyze_overlap(boolean_results, vectoriel_results)
        }
        
        return {
            "mode_used": "hybrid",
            "results": top_results,
            "stats": stats,
            "config": {
                "target": target,
                "fusion_strategy": self.hybrid_scorer.strategy,
                "weights": {
                    "boolean": self.hybrid_scorer.boolean_weight,
                    "bm25": self.hybrid_scorer.bm25_weight
                }
            }
        }
    
    def _count_sources(self, results: List[Dict]) -> Dict:
        """Compte résultats par source"""
        counts = {"systeme": 0, "uploaded": 0}
        
        for r in results:
            source_type = r.get("source_type", "unknown")
            if source_type in counts:
                counts[source_type] += 1
        
        return counts
    
    def _analyze_overlap(
        self,
        boolean_results: List[Dict],
        vectoriel_results: List[Dict]
    ) -> Dict:
        """Analyse le chevauchement entre résultats booléen et vectoriel"""
        
        bool_ids = {str(r.get("id") or r.get("doc_id")) for r in boolean_results}
        vec_ids = {str(r.get("id") or r.get("doc_id")) for r in vectoriel_results}
        
        intersection = bool_ids & vec_ids
        union = bool_ids | vec_ids
        
        return {
            "boolean_only": len(bool_ids - vec_ids),
            "vectoriel_only": len(vec_ids - bool_ids),
            "both": len(intersection),
            "jaccard_similarity": round(len(intersection) / len(union), 3) if union else 0
        }
    
    def compare_modes(
        self,
        query: str,
        filters: Dict = None,
        target: str = "cvs",
        top_k: int = 10
    ) -> Dict:
        """
        Compare les 3 modes pour une même requête
        """
        
        results = {}
        
        # Mode booléen
        try:
            results["boolean"] = self.search(
                query=query,
                filters=filters,
                target=target,
                mode="boolean",
                top_k=top_k,
                auto_extract=False
            )
        except Exception as e:
            results["boolean"] = {"error": str(e)}
            logger.error(f"Erreur mode boolean: {e}")
        
        # Mode vectoriel
        try:
            results["vectoriel"] = self.search(
                query=query,
                filters=filters,
                target=target,
                mode="vectoriel",
                top_k=top_k,
                auto_extract=False
            )
        except Exception as e:
            results["vectoriel"] = {"error": str(e)}
            logger.error(f"Erreur mode vectoriel: {e}")
        
        # Mode hybride
        try:
            results["hybrid"] = self.search(
                query=query,
                filters=filters,
                target=target,
                mode="hybrid",
                top_k=top_k,
                auto_extract=True
            )
        except Exception as e:
            results["hybrid"] = {"error": str(e)}
            logger.error(f"Erreur mode hybrid: {e}")
        
        return results
    
    def get_system_stats(self) -> Dict:
        """Retourne statistiques globales du système"""
        
        return {
            "boolean_model": {
                "status": "active"
            },
            "vectoriel_model": {
                "status": "active",
                "bm25_indices": self.vectoriel_model.get_index_stats()
            },
            "hybrid_scorer": {
                "default_strategy": self.hybrid_scorer.strategy,
                "available_strategies": list(HybridScorer.STRATEGIES.keys())
            }
        }


# ========================================================
# API PUBLIQUE (pour compatibilité)
# ========================================================
def search(
    query: str = "",
    filters: Dict = None,
    target: str = "cvs",
    mode: str = "auto"
) -> Dict:
    """
    API publique simplifiée
    """
    orchestrator = SearchOrchestrator()
    return orchestrator.search(query, filters, target, mode)


# ========================================================
# TESTS
# ========================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🚀 TEST ORCHESTRATEUR COMPLET")
    print("="*80)
    
    orchestrator = SearchOrchestrator()
    
    # Test 1: Mode auto avec filtres → Boolean
    print("\n📝 Test 1: Filtres seuls (mode auto)")
    result1 = orchestrator.search(
        filters={"skills": ["python", "java"], "experience": [5, 10]},
        mode="auto"
    )
    print(f"   Mode: {result1['mode_used']}")
    print(f"   Résultats: {result1['stats']['total_results']}")
    
    # Test 2: Mode vectoriel explicite
    print("\n📝 Test 2: Mode vectoriel explicite")
    result2 = orchestrator.search(
        query="développeur python django senior",
        mode="vectoriel",
        top_k=5
    )
    print(f"   Mode: {result2['mode_used']}")
    print(f"   Résultats: {result2['stats']['total_results']}")
    
    # Test 3: Mode hybride
    print("\n📝 Test 3: Mode hybride (query + filtres)")
    result3 = orchestrator.search(
        query="python django",
        filters={"experience": [3, 10]},
        mode="hybrid",
        top_k=5
    )
    print(f"   Mode: {result3['mode_used']}")
    print(f"   Résultats: {result3['stats']['total_results']}")
    
    # Test 4: Comparaison des modes
    print("\n📝 Test 4: Comparaison des 3 modes")
    comparison = orchestrator.compare_modes(
        query="python docker",
        filters={"experience": [5, 10]},
        top_k=3
    )
    
    for mode, result in comparison.items():
        if "error" not in result:
            print(f"   {mode}: {result['stats']['total_results']} résultats")
    
    print("\n✅ Tous les tests terminés!")