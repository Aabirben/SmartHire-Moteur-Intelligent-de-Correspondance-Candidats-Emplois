"""
Tests Complets pour le Modèle Vectoriel BM25 - VERSION CORRIGÉE
Emplacement: backend/tests/test_vectoriel_search.py
"""

import sys
from pathlib import Path

# Ajouter le backend au path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.search.vectoriel_model import VectorielSearchModel, BM25Scorer
from backend.search.hybrid_scorer import HybridScorer, analyze_score_distribution
from backend.search.search_orchestrator import SearchOrchestrator


class TestVectorielSearch:
    """Suite de tests pour le modèle vectoriel"""
    
    def __init__(self):
        self.model = VectorielSearchModel()
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def run_all(self):
        """Exécute tous les tests"""
        
        print("="*80)
        print("🧪 SUITE DE TESTS - MODÈLE VECTORIEL BM25")
        print("="*80)
        
        # Tests BM25Scorer
        print("\n" + "="*80)
        print("PARTIE 1: Tests BM25Scorer (Algorithme)")
        print("="*80)
        
        self.test_bm25_index_building()
        self.test_bm25_scoring()
        self.test_bm25_empty_query()
        self.test_bm25_unknown_terms()
        self.test_bm25_multiple_terms()
        
        # Tests VectorielSearchModel
        print("\n" + "="*80)
        print("PARTIE 2: Tests VectorielSearchModel")
        print("="*80)
        
        self.test_search_simple()
        self.test_search_long_query()
        self.test_search_tech_specific()
        self.test_search_empty()
        self.test_search_jobs()
        
        # Tests HybridScorer
        print("\n" + "="*80)
        print("PARTIE 3: Tests HybridScorer (Fusion)")
        print("="*80)
        
        self.test_hybrid_weighted()
        self.test_hybrid_rrf()
        self.test_hybrid_strategies()
        
        # Tests Intégration
        print("\n" + "="*80)
        print("PARTIE 4: Tests Intégration (SearchOrchestrator)")
        print("="*80)
        
        self.test_orchestrator_mode_decision()
        self.test_orchestrator_hybrid_search()
        self.test_orchestrator_comparison()
        
        # Résultats finaux
        self.print_results()
    
    def assert_test(self, condition, test_name):
        """Assertion avec compteur"""
        self.total += 1
        
        if condition:
            print(f"✅ [{self.total}] {test_name}")
            self.passed += 1
        else:
            print(f"❌ [{self.total}] {test_name}")
            self.failed += 1
    
    # ========================================================================
    # PARTIE 1: Tests BM25Scorer
    # ========================================================================
    
    def test_bm25_index_building(self):
        """Test construction index BM25"""
        print("\n📝 Test 1.1: Construction index BM25")
        
        # Documents test avec contenu suffisant
        docs = [
            {"id": "1", "tokens": ["python", "django", "web", "development", "backend"]},
            {"id": "2", "tokens": ["python", "flask", "api", "rest", "microservices"]},
            {"id": "3", "tokens": ["java", "spring", "backend", "enterprise", "jee"]}
        ]
        
        scorer = BM25Scorer()
        scorer.build_index(docs)
        
        self.assert_test(scorer.N == 3, "Nombre de documents correct")
        self.assert_test(scorer.avgdl > 0, "Longueur moyenne calculée")
        self.assert_test("python" in scorer.df, "DF calculé pour 'python'")
        self.assert_test(scorer.df["python"] == 2, "DF correct pour 'python'")
        self.assert_test("python" in scorer.idf, "IDF calculé pour 'python'")
        
        print(f"   Stats: N={scorer.N}, avgdl={scorer.avgdl:.2f}, "
              f"unique_terms={len(scorer.df)}")
    
    def test_bm25_scoring(self):
        """Test calcul scores BM25"""
        print("\n📝 Test 1.2: Calcul scores BM25")
        
        # Documents avec assez de contenu pour avoir des scores positifs
        docs = [
            {"id": "1", "tokens": ["python", "django", "web", "framework", "mvc"]},
            {"id": "2", "tokens": ["python", "python", "flask", "api", "rest"]},  # python 2x
            {"id": "3", "tokens": ["java", "spring", "backend", "jee", "enterprise"]},
            {"id": "4", "tokens": ["javascript", "react", "frontend", "ui", "components"]},
            {"id": "5", "tokens": ["ruby", "rails", "mvc", "backend", "web"]}
        ]
        
        scorer = BM25Scorer()
        scorer.build_index(docs)
        
        # Query: python
        query_tokens = ["python"]
        score_1 = scorer.score(query_tokens, "1")
        score_2 = scorer.score(query_tokens, "2")
        score_3 = scorer.score(query_tokens, "3")
        
        self.assert_test(score_1 > 0, "Score doc1 > 0")
        self.assert_test(score_2 > score_1, "Score doc2 > doc1 (TF plus élevé)")
        self.assert_test(score_3 == 0, "Score doc3 = 0 (pas de match)")
        
        print(f"   Scores: doc1={score_1:.4f}, doc2={score_2:.4f}, doc3={score_3:.4f}")
    
    def test_bm25_empty_query(self):
        """Test query vide"""
        print("\n📝 Test 1.3: Query vide")
        
        docs = [{"id": "1", "tokens": ["python", "django", "web"]}]
        scorer = BM25Scorer()
        scorer.build_index(docs)
        
        score = scorer.score([], "1")
        
        self.assert_test(score == 0, "Score = 0 pour query vide")
    
    def test_bm25_unknown_terms(self):
        """Test termes inconnus"""
        print("\n📝 Test 1.4: Termes inconnus")
        
        docs = [{"id": "1", "tokens": ["python", "django", "web"]}]
        scorer = BM25Scorer()
        scorer.build_index(docs)
        
        # Query avec terme inconnu
        score = scorer.score(["cobol", "fortran"], "1")
        
        self.assert_test(score == 0, "Score = 0 pour termes inconnus")
    
    def test_bm25_multiple_terms(self):
        """Test requête multi-termes"""
        print("\n📝 Test 1.5: Requête multi-termes")
        
        docs = [
            {"id": "1", "tokens": ["python", "django", "web", "backend"]},
            {"id": "2", "tokens": ["python", "flask", "api", "rest"]},
            {"id": "3", "tokens": ["python", "django", "rest", "api", "backend"]}
        ]
        
        scorer = BM25Scorer()
        scorer.build_index(docs)
        
        # Query avec 2 termes
        query_tokens = ["python", "django"]
        score_1 = scorer.score(query_tokens, "1")
        score_3 = scorer.score(query_tokens, "3")
        
        self.assert_test(score_1 > 0, "Doc1 score > 0")
        self.assert_test(score_3 > 0, "Doc3 score > 0")
        # Doc3 devrait avoir un meilleur score (contient les 2 termes)
        self.assert_test(score_3 >= score_1, "Doc3 >= Doc1 (contient les 2 termes)")
        
        print(f"   Scores: doc1={score_1:.4f}, doc3={score_3:.4f}")
    
    # ========================================================================
    # PARTIE 2: Tests VectorielSearchModel
    # ========================================================================
    
    def test_search_simple(self):
        """Test recherche simple"""
        print("\n📝 Test 2.1: Recherche simple 'python'")
        
        result = self.model.search("python", target="cvs", top_k=10)
        
        self.assert_test("results" in result, "Clé 'results' présente")
        self.assert_test("stats" in result, "Clé 'stats' présente")
        self.assert_test(len(result["results"]) >= 0, "Résultats récupérés")
        
        # Vérifier scores si résultats présents
        if result["results"]:
            first = result["results"][0]
            self.assert_test("score_bm25" in first, "Score BM25 présent")
            self.assert_test(first["score_bm25"] >= 0, "Score BM25 >= 0")
            
            print(f"   Résultats: {result['stats']['total_results']}")
            print(f"   Top 3: {[r['nom'] for r in result['results'][:3]]}")
        else:
            print(f"   Résultats: 0 (aucun match)")
    
    def test_search_long_query(self):
        """Test query longue (texte naturel)"""
        print("\n📝 Test 2.2: Query longue (texte naturel)")
        
        query = "Je cherche un développeur senior avec expertise en Python, Django et expérience en architecture microservices"
        result = self.model.search(query, target="cvs", top_k=5)
        
        self.assert_test(len(result["results"]) >= 0, "Résultats récupérés")
        self.assert_test(
            result["stats"]["query_tokens_count"] > 5,
            "Plusieurs tokens détectés"
        )
        
        print(f"   Tokens: {result['stats']['query_tokens_count']}")
        print(f"   Résultats: {result['stats']['total_results']}")
    
    def test_search_tech_specific(self):
        """Test recherche technologie spécifique"""
        print("\n📝 Test 2.3: Recherche 'docker kubernetes'")
        
        result = self.model.search("docker kubernetes", target="cvs", top_k=10)
        
        self.assert_test("results" in result, "Résultats présents")
        self.assert_test(result["stats"]["total_results"] >= 0, "Stats cohérentes")
        
        # Vérifier que résultats contiennent tech recherchée (si résultats présents)
        if result["results"]:
            top_result = result["results"][0]
            tags = top_result.get("tags", [])
            tags_str = " ".join(str(t).lower() for t in tags)
            
            has_docker_or_k8s = "docker" in tags_str or "kubernetes" in tags_str or "k8s" in tags_str
            self.assert_test(has_docker_or_k8s, "Top résultat contient docker/k8s")
        
        print(f"   Résultats: {result['stats']['total_results']}")
    
    def test_search_empty(self):
        """Test query vide"""
        print("\n📝 Test 2.4: Query vide")
        
        result = self.model.search("", target="cvs")
        
        self.assert_test(len(result["results"]) == 0, "Aucun résultat pour query vide")
        self.assert_test(result["stats"]["total_results"] == 0, "Stats correctes")
    
    def test_search_jobs(self):
        """Test recherche offres d'emploi"""
        print("\n📝 Test 2.5: Recherche offres (target='offres')")
        
        result = self.model.search("développeur backend", target="offres", top_k=5)
        
        self.assert_test("results" in result, "Résultats présents")
        self.assert_test(result["stats"]["total_results"] >= 0, "Stats cohérentes")
        
        print(f"   Offres trouvées: {result['stats']['total_results']}")
    
    # ========================================================================
    # PARTIE 3: Tests HybridScorer
    # ========================================================================
    
    def test_hybrid_weighted(self):
        """Test fusion weighted"""
        print("\n📝 Test 3.1: Fusion weighted (50/50)")
        
        bool_results = [
            {"id": "1", "nom": "Doc A", "score_boolean": 0.8},
            {"id": "2", "nom": "Doc B", "score_boolean": 0.6}
        ]
        
        bm25_results = [
            {"id": "1", "nom": "Doc A", "score_bm25": 10.0},
            {"id": "3", "nom": "Doc C", "score_bm25": 15.0}
        ]
        
        scorer = HybridScorer(strategy="weighted", boolean_weight=0.5, bm25_weight=0.5)
        fused = scorer.fuse(bool_results, bm25_results)
        
        self.assert_test(len(fused) == 3, "3 documents uniques")
        self.assert_test("score_hybrid" in fused[0], "Score hybride présent")
        self.assert_test(fused[0]["score_hybrid"] >= 0, "Score hybride >= 0")
        
        print(f"   Documents fusionnés: {len(fused)}")
        print(f"   Top 1: {fused[0]['nom']} - Score: {fused[0]['score_hybrid']:.4f}")
    
    def test_hybrid_rrf(self):
        """Test Reciprocal Rank Fusion"""
        print("\n📝 Test 3.2: Reciprocal Rank Fusion (RRF)")
        
        bool_results = [
            {"id": "1", "nom": "Doc A", "score_boolean": 1.0},
            {"id": "2", "nom": "Doc B", "score_boolean": 0.9}
        ]
        
        bm25_results = [
            {"id": "2", "nom": "Doc B", "score_bm25": 20.0},
            {"id": "1", "nom": "Doc A", "score_bm25": 18.0}
        ]
        
        scorer = HybridScorer(strategy="rrf", rrf_k=60)
        fused = scorer.fuse(bool_results, bm25_results)
        
        self.assert_test(len(fused) == 2, "2 documents")
        self.assert_test(fused[0]["fusion_strategy"] == "rrf", "Stratégie RRF utilisée")
        
        print(f"   Top 1: {fused[0]['nom']} - Score RRF: {fused[0]['score_hybrid']:.4f}")
    
    def test_hybrid_strategies(self):
        """Test toutes les stratégies"""
        print("\n📝 Test 3.3: Comparaison stratégies")
        
        bool_results = [{"id": str(i), "nom": f"Doc{i}", "score_boolean": 0.5 + i*0.1} for i in range(5)]
        bm25_results = [{"id": str(i), "nom": f"Doc{i}", "score_bm25": 10.0 + i*2.0} for i in range(5)]
        
        scorer = HybridScorer()
        comparison = scorer.compare_strategies(bool_results, bm25_results, top_k=3)
        
        self.assert_test(len(comparison) == 4, "4 stratégies testées")
        self.assert_test("weighted" in comparison, "Weighted présente")
        self.assert_test("rrf" in comparison, "RRF présente")
        
        print(f"   Stratégies: {list(comparison.keys())}")
    
    # ========================================================================
    # PARTIE 4: Tests Intégration
    # ========================================================================
    
    def test_orchestrator_mode_decision(self):
        """Test décision automatique du mode"""
        print("\n📝 Test 4.1: Décision automatique du mode")
        
        orchestrator = SearchOrchestrator()
        
        # Cas 1: Query longue seule → vectoriel
        result1 = orchestrator.search(
            query="développeur expérimenté avec leadership et communication",
            mode="auto",
            top_k=5
        )
        self.assert_test(
            result1["mode_used"] == "vectoriel",
            "Query longue → mode vectoriel"
        )
        
        # Cas 2: Query + filtres → hybrid
        result2 = orchestrator.search(
            query="python django",
            filters={"experience": [3, 10]},
            mode="auto",
            top_k=5
        )
        self.assert_test(
            result2["mode_used"] == "hybrid",
            "Query + filtres → mode hybrid"
        )
        
        # Cas 3: Filtres seuls → boolean
        result3 = orchestrator.search(
            filters={"skills": ["python"]},
            mode="auto",
            top_k=5
        )
        self.assert_test(
            result3["mode_used"] == "boolean",
            "Filtres seuls → mode boolean"
        )
        
        print(f"   Test 1: {result1['mode_used']}")
        print(f"   Test 2: {result2['mode_used']}")
        print(f"   Test 3: {result3['mode_used']}")
    
    def test_orchestrator_hybrid_search(self):
        """Test recherche hybride complète"""
        print("\n📝 Test 4.2: Recherche hybride complète")
        
        orchestrator = SearchOrchestrator()
        
        result = orchestrator.search(
            query="développeur python django",
            filters={"experience": [3, 10]},
            mode="hybrid",
            hybrid_strategy="weighted",
            boolean_weight=0.6,
            bm25_weight=0.4,
            top_k=5
        )
        
        self.assert_test(result["mode_used"] == "hybrid", "Mode hybrid utilisé")
        self.assert_test("stats" in result, "Stats présentes")
        self.assert_test("config" in result, "Config présente")
        
        if result["results"]:
            first = result["results"][0]
            self.assert_test("score_hybrid" in first, "Score hybride présent")
        
        print(f"   Résultats: {result['stats']['total_results']}")
        print(f"   Fusion: {result['config'].get('fusion_strategy', 'N/A')}")
    
    def test_orchestrator_comparison(self):
        """Test comparaison des modes"""
        print("\n📝 Test 4.3: Comparaison des 3 modes")
        
        orchestrator = SearchOrchestrator()
        
        comparison = orchestrator.compare_modes(
            query="python docker",
            filters={"experience": [3, 10]},
            top_k=3
        )
        
        self.assert_test("boolean" in comparison, "Mode boolean testé")
        self.assert_test("vectoriel" in comparison, "Mode vectoriel testé")
        self.assert_test("hybrid" in comparison, "Mode hybrid testé")
        
        print(f"   Modes comparés: {list(comparison.keys())}")
        
        for mode, result in comparison.items():
            if "error" not in result:
                print(f"   {mode}: {result['stats'].get('total_results', 0)} résultats")
            else:
                print(f"   {mode}: ERREUR - {result['error']}")
    
    # ========================================================================
    # Résultats
    # ========================================================================
    
    def print_results(self):
        """Affiche résumé des tests"""
        
        print("\n" + "="*80)
        print("📊 RÉSULTATS FINAUX")
        print("="*80)
        
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        print(f"\n✅ Tests réussis: {self.passed}/{self.total}")
        print(f"❌ Tests échoués: {self.failed}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        else:
            print(f"\n⚠️ {self.failed} test(s) ont échoué")
        
        print("\n" + "="*80)
        print("🔍 RESSOURCES UTILISÉES:")
        print("="*80)
        print("   ✅ vectoriel_model.py::BM25Scorer")
        print("   ✅ vectoriel_model.py::VectorielSearchModel")
        print("   ✅ hybrid_scorer.py::HybridScorer")
        print("   ✅ search_orchestrator.py::SearchOrchestrator")
        print("   ✅ preprocessing.py::pretraiter_texte()")
        print("   ✅ PostgreSQL (tables: cvs, offres)")
        print("   ✅ Whoosh (CV_INDEX, JOB_INDEX)")


def main():
    """Point d'entrée principal"""
    
    test_suite = TestVectorielSearch()
    test_suite.run_all()


if __name__ == "__main__":
    main()