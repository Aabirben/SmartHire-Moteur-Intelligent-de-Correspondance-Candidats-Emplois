"""
Module de Scoring Hybride pour SmartHire
Emplacement: backend/search/hybrid_scorer.py

Combine les scores booléens et BM25 pour un classement optimal
"""

from typing import Dict, List, Tuple
import statistics


class HybridScorer:
    """
    Combine scores booléen et BM25 avec pondérations configurables
    
    Stratégies disponibles:
    1. WEIGHTED: Score = w1*booléen + w2*bm25 (défaut)
    2. RECIPROCAL_RANK_FUSION: Fusionne classements (RRF)
    3. MAX: Prend le max des deux scores
    4. MULTIPLICATIVE: Score = booléen * bm25
    """
    
    STRATEGIES = {
        "weighted": "Moyenne pondérée",
        "rrf": "Reciprocal Rank Fusion",
        "max": "Score maximum",
        "multiplicative": "Produit des scores"
    }
    
    def __init__(
        self,
        strategy: str = "weighted",
        boolean_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rrf_k: int = 60
    ):
        """
        Args:
            strategy: Stratégie de fusion (voir STRATEGIES)
            boolean_weight: Poids du score booléen (0-1)
            bm25_weight: Poids du score BM25 (0-1)
            rrf_k: Paramètre k pour RRF (défaut: 60)
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Stratégie inconnue: {strategy}. "
                           f"Utiliser: {list(self.STRATEGIES.keys())}")
        
        self.strategy = strategy
        self.boolean_weight = boolean_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k
        
        # Validation poids
        if strategy == "weighted":
            total = boolean_weight + bm25_weight
            if abs(total - 1.0) > 0.01:
                print(f"⚠️ Poids ne somment pas à 1.0 ({total}), normalisation...")
                self.boolean_weight = boolean_weight / total
                self.bm25_weight = bm25_weight / total
    
    def fuse(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        deduplicate: bool = True
    ) -> List[Dict]:
        """
        Fusionne deux listes de résultats
        
        Args:
            boolean_results: Résultats booléens avec 'score_boolean'
            bm25_results: Résultats BM25 avec 'score_bm25'
            deduplicate: Dédupliquer sur 'id' ou 'doc_id'
            
        Returns:
            Liste fusionnée triée par score hybride DESC
        """
        
        if self.strategy == "weighted":
            return self._fuse_weighted(boolean_results, bm25_results, deduplicate)
        elif self.strategy == "rrf":
            return self._fuse_rrf(boolean_results, bm25_results, deduplicate)
        elif self.strategy == "max":
            return self._fuse_max(boolean_results, bm25_results, deduplicate)
        elif self.strategy == "multiplicative":
            return self._fuse_multiplicative(boolean_results, bm25_results, deduplicate)
    
    def _normalize_scores(self, results: List[Dict], score_key: str) -> List[Dict]:
        """
        Normalise les scores entre 0 et 1 (min-max normalization)
        """
        if not results:
            return results
        
        scores = [r[score_key] for r in results if score_key in r]
        
        if not scores:
            return results
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # Tous les scores identiques
            for r in results:
                if score_key in r:
                    r[f"{score_key}_norm"] = 1.0
        else:
            for r in results:
                if score_key in r:
                    r[f"{score_key}_norm"] = (
                        (r[score_key] - min_score) / (max_score - min_score)
                    )
        
        return results
    
    def _fuse_weighted(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        deduplicate: bool
    ) -> List[Dict]:
        """
        Fusion par moyenne pondérée
        Score = w1 * score_bool_norm + w2 * score_bm25_norm
        """
        
        # 1. Normaliser les scores
        boolean_results = self._normalize_scores(boolean_results, "score_boolean")
        bm25_results = self._normalize_scores(bm25_results, "score_bm25")
        
        # 2. Indexer par ID
        bool_map = {}
        for r in boolean_results:
            key = r.get("id") or r.get("doc_id")
            if key:
                bool_map[str(key)] = r
        
        bm25_map = {}
        for r in bm25_results:
            key = r.get("id") or r.get("doc_id")
            if key:
                bm25_map[str(key)] = r
        
        # 3. Combiner
        all_ids = set(bool_map.keys()) | set(bm25_map.keys())
        
        fused = []
        for doc_id in all_ids:
            bool_res = bool_map.get(doc_id, {})
            bm25_res = bm25_map.get(doc_id, {})
            
            # Scores normalisés (0 si absent)
            score_bool_norm = bool_res.get("score_boolean_norm", 0.0)
            score_bm25_norm = bm25_res.get("score_bm25_norm", 0.0)
            
            # Score hybride
            score_hybrid = (
                self.boolean_weight * score_bool_norm +
                self.bm25_weight * score_bm25_norm
            )
            
            # Prendre les infos du résultat le plus complet
            base_result = bool_res if bool_res else bm25_res
            
            fused.append({
                **base_result,
                "score_boolean": bool_res.get("score_boolean", 0.0),
                "score_bm25": bm25_res.get("score_bm25", 0.0),
                "score_boolean_norm": score_bool_norm,
                "score_bm25_norm": score_bm25_norm,
                "score_hybrid": round(score_hybrid, 4),
                "fusion_strategy": "weighted",
                "in_boolean": doc_id in bool_map,
                "in_bm25": doc_id in bm25_map
            })
        
        # 4. Trier
        fused.sort(key=lambda x: x["score_hybrid"], reverse=True)
        
        return fused
    
    def _fuse_rrf(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        deduplicate: bool
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion
        RRF(d) = Σ 1/(k + rank_i(d))
        
        k = 60 est la valeur recommandée (Cormack et al. 2009)
        """
        
        # Calculer RRF
        rrf_scores = {}
        
        # Rangs booléens
        for rank, r in enumerate(boolean_results, start=1):
            doc_id = str(r.get("id") or r.get("doc_id"))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (self.rrf_k + rank)
        
        # Rangs BM25
        for rank, r in enumerate(bm25_results, start=1):
            doc_id = str(r.get("id") or r.get("doc_id"))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (self.rrf_k + rank)
        
        # Créer index par ID
        all_results_map = {}
        for r in boolean_results + bm25_results:
            doc_id = str(r.get("id") or r.get("doc_id"))
            if doc_id not in all_results_map:
                all_results_map[doc_id] = r
        
        # Construire résultats fusionnés
        fused = []
        for doc_id, rrf_score in rrf_scores.items():
            result = all_results_map[doc_id].copy()
            result["score_hybrid"] = round(rrf_score, 4)
            result["fusion_strategy"] = "rrf"
            fused.append(result)
        
        # Trier
        fused.sort(key=lambda x: x["score_hybrid"], reverse=True)
        
        return fused
    
    def _fuse_max(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        deduplicate: bool
    ) -> List[Dict]:
        """Prend le score maximum après normalisation"""
        
        boolean_results = self._normalize_scores(boolean_results, "score_boolean")
        bm25_results = self._normalize_scores(bm25_results, "score_bm25")
        
        # Même logique que weighted mais score = max
        bool_map = {str(r.get("id") or r.get("doc_id")): r for r in boolean_results}
        bm25_map = {str(r.get("id") or r.get("doc_id")): r for r in bm25_results}
        
        all_ids = set(bool_map.keys()) | set(bm25_map.keys())
        
        fused = []
        for doc_id in all_ids:
            bool_res = bool_map.get(doc_id, {})
            bm25_res = bm25_map.get(doc_id, {})
            
            score_bool_norm = bool_res.get("score_boolean_norm", 0.0)
            score_bm25_norm = bm25_res.get("score_bm25_norm", 0.0)
            
            score_hybrid = max(score_bool_norm, score_bm25_norm)
            
            base_result = bool_res if bool_res else bm25_res
            
            fused.append({
                **base_result,
                "score_boolean": bool_res.get("score_boolean", 0.0),
                "score_bm25": bm25_res.get("score_bm25", 0.0),
                "score_hybrid": round(score_hybrid, 4),
                "fusion_strategy": "max"
            })
        
        fused.sort(key=lambda x: x["score_hybrid"], reverse=True)
        return fused
    
    def _fuse_multiplicative(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        deduplicate: bool
    ) -> List[Dict]:
        """Score = score_bool_norm * score_bm25_norm"""
        
        boolean_results = self._normalize_scores(boolean_results, "score_boolean")
        bm25_results = self._normalize_scores(bm25_results, "score_bm25")
        
        bool_map = {str(r.get("id") or r.get("doc_id")): r for r in boolean_results}
        bm25_map = {str(r.get("id") or r.get("doc_id")): r for r in bm25_results}
        
        # Seulement docs présents dans les DEUX listes
        common_ids = set(bool_map.keys()) & set(bm25_map.keys())
        
        fused = []
        for doc_id in common_ids:
            bool_res = bool_map[doc_id]
            bm25_res = bm25_map[doc_id]
            
            score_bool_norm = bool_res.get("score_boolean_norm", 0.0)
            score_bm25_norm = bm25_res.get("score_bm25_norm", 0.0)
            
            score_hybrid = score_bool_norm * score_bm25_norm
            
            fused.append({
                **bool_res,
                "score_boolean": bool_res.get("score_boolean", 0.0),
                "score_bm25": bm25_res.get("score_bm25", 0.0),
                "score_hybrid": round(score_hybrid, 4),
                "fusion_strategy": "multiplicative"
            })
        
        fused.sort(key=lambda x: x["score_hybrid"], reverse=True)
        return fused
    
    def compare_strategies(
        self,
        boolean_results: List[Dict],
        bm25_results: List[Dict],
        top_k: int = 10
    ) -> Dict:
        """
        Compare toutes les stratégies de fusion
        
        Returns:
            {
                "weighted": [...],
                "rrf": [...],
                "max": [...],
                "multiplicative": [...]
            }
        """
        comparison = {}
        
        for strategy in self.STRATEGIES.keys():
            scorer = HybridScorer(
                strategy=strategy,
                boolean_weight=self.boolean_weight,
                bm25_weight=self.bm25_weight,
                rrf_k=self.rrf_k
            )
            
            fused = scorer.fuse(boolean_results, bm25_results)
            comparison[strategy] = fused[:top_k]
        
        return comparison
    
    def get_config(self) -> Dict:
        """Retourne configuration actuelle"""
        return {
            "strategy": self.strategy,
            "strategy_name": self.STRATEGIES[self.strategy],
            "boolean_weight": self.boolean_weight,
            "bm25_weight": self.bm25_weight,
            "rrf_k": self.rrf_k if self.strategy == "rrf" else None
        }


def analyze_score_distribution(results: List[Dict], score_key: str = "score_hybrid") -> Dict:
    """
    Analyse la distribution des scores
    
    Returns:
        Statistiques descriptives (mean, median, std, min, max, quartiles)
    """
    if not results:
        return {}
    
    scores = [r[score_key] for r in results if score_key in r]
    
    if not scores:
        return {}
    
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    
    return {
        "count": n,
        "mean": round(statistics.mean(scores), 4),
        "median": round(statistics.median(scores), 4),
        "stdev": round(statistics.stdev(scores), 4) if n > 1 else 0,
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "q1": round(scores_sorted[n // 4], 4) if n >= 4 else None,
        "q3": round(scores_sorted[3 * n // 4], 4) if n >= 4 else None,
        "range": round(max(scores) - min(scores), 4)
    }


# Test unitaire
if __name__ == "__main__":
    print("="*80)
    print("TEST HYBRID SCORER")
    print("="*80)
    
    # Données de test
    boolean_results = [
        {"id": "1", "nom": "Doc A", "score_boolean": 0.9},
        {"id": "2", "nom": "Doc B", "score_boolean": 0.7},
        {"id": "3", "nom": "Doc C", "score_boolean": 0.5}
    ]
    
    bm25_results = [
        {"id": "1", "nom": "Doc A", "score_bm25": 12.5},
        {"id": "2", "nom": "Doc B", "score_bm25": 8.3},
        {"id": "4", "nom": "Doc D", "score_bm25": 15.2}
    ]
    
    # Test stratégie weighted
    scorer = HybridScorer(strategy="weighted", boolean_weight=0.6, bm25_weight=0.4)
    fused = scorer.fuse(boolean_results, bm25_results)
    
    print("\n✅ Résultats fusion weighted (0.6 bool + 0.4 bm25):")
    for r in fused[:5]:
        print(f"   {r['nom']}: hybrid={r['score_hybrid']:.4f} "
              f"(bool={r['score_boolean']:.3f}, bm25={r['score_bm25']:.3f})")
    
    # Analyse distribution
    print("\n📊 Distribution des scores:")
    stats = analyze_score_distribution(fused)
    for k, v in stats.items():
        print(f"   {k}: {v}")
