"""
============================================================================
SMARTHIRE - Tests EXHAUSTIFS du Modèle Booléen
✅ Tous les cas limites + scénarios complexes
============================================================================
"""

import sys
import logging
from pathlib import Path

# Path setup
CURRENT_FILE = Path(__file__).resolve()
current = CURRENT_FILE
while current.parent != current:
    if (current / "backend").exists():
        PROJECT_ROOT = current
        sys.path.insert(0, str(PROJECT_ROOT))
        break
    current = current.parent

from backend.search.search_orchestrator import search
from backend.search.query_processor import SearchQueryProcessor
from backend.search.filter_processor import FilterProcessor
from backend.search.boolean_search import BooleanSearchModel

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestBooleanSearchComplete:
    """Tests exhaustifs avec tous les cas limites"""
    
    def __init__(self):
        self.query_processor = SearchQueryProcessor()
        self.filter_processor = FilterProcessor()
        self.boolean_model = BooleanSearchModel()
        self.results = {"passed": 0, "failed": 0, "errors": []}
    
    # ========================================================
    # TEST 1: Opérateurs NOT
    # ========================================================
    def test_not_operator(self):
        """Test exclusion de compétences"""
        print("\n" + "="*80)
        print("TEST 1: OPÉRATEUR NOT")
        print("="*80)
        
        try:
            print("\n[1.1] Exclure PHP")
            results = self.boolean_model.search(
                query_terms={
                    "must_have": ["python"],
                    "must_not_have": ["php"]
                },
                target="cvs"
            )
            
            print(f"   ✅ Résultats sans PHP: {len(results)}")
            
            # Vérifier qu'aucun résultat ne contient PHP
            has_php = any("php" in r.get("tags", []) for r in results)
            assert not has_php, "❌ Résultats contiennent PHP malgré NOT"
            
            print(f"   ✅ Aucun résultat ne contient PHP")
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"NOT operator: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"NOT operator erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 2: Compétences required/optional
    # ========================================================
    def test_required_optional_skills(self):
        """Test skills required (AND) + optional (OR)"""
        print("\n" + "="*80)
        print("TEST 2: COMPÉTENCES REQUIRED/OPTIONAL")
        print("="*80)
        
        try:
            print("\n[2.1] Required: Python, Optional: Docker/K8s")
            
            filters = {
                "skills": {
                    "required": ["python"],
                    "optional": ["docker", "kubernetes"]
                }
            }
            
            processed = self.filter_processor.process(filters)
            
            assert "skills_and" in processed["boolean_filters"], "❌ skills_and manquant"
            assert "skills_or" in processed["boolean_filters"], "❌ skills_or manquant"
            assert "python" in processed["boolean_filters"]["skills_and"], "❌ Python pas requis"
            
            print(f"   ✅ Required (AND): {processed['boolean_filters']['skills_and']}")
            print(f"   ✅ Optional (OR): {processed['boolean_filters']['skills_or']}")
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Required/Optional: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Required/Optional erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 3: IDs invalides
    # ========================================================
    def test_invalid_ids(self):
        """Test matching avec IDs invalides"""
        print("\n" + "="*80)
        print("TEST 3: GESTION IDS INVALIDES")
        print("="*80)
        
        try:
            print("\n[3.1] CV inexistant")
            result1 = self.boolean_model.match_cv_to_job(
                cv_id=99999,
                job_id=52
            )
            assert "error" in result1, "❌ Devrait retourner erreur"
            print(f"   ✅ Erreur détectée: {result1['error']}")
            
            print("\n[3.2] IDs vides")
            result2 = self.boolean_model.match_cv_to_job(
                cv_id="",
                job_id=""
            )
            assert "error" in result2, "❌ Devrait retourner erreur"
            print(f"   ✅ Erreur détectée: {result2['error']}")
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Invalid IDs: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Invalid IDs erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 4: Filtres vides
    # ========================================================
    def test_empty_filters(self):
        """Test query vide + filtres vides"""
        print("\n" + "="*80)
        print("TEST 4: FILTRES/QUERY VIDES")
        print("="*80)
        
        try:
            print("\n[4.1] Query vide + Filtres vides")
            result = search(query="", filters={})
            
            # Devrait retourner mode booléen avec 0 résultats ou tous
            print(f"   ✅ Mode: {result['mode_used']}")
            print(f"   ✅ Résultats: {result['stats']['total']}")
            
            self.results["passed"] += 1
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Empty filters: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 5: Expérience exacte
    # ========================================================
    def test_exact_experience(self):
        """Test expérience exacte (pas range)"""
        print("\n" + "="*80)
        print("TEST 5: EXPÉRIENCE EXACTE")
        print("="*80)
        
        try:
            print("\n[5.1] Exactement 5 ans")
            filters = {"experience": 5}
            processed = self.filter_processor.process(filters)
            
            # Devrait transformer en range [5, 100]
            assert "experience" in processed["range_filters"], "❌ Range non créé"
            exp_range = processed["range_filters"]["experience"]
            assert exp_range[0] == 5, "❌ Min incorrect"
            
            print(f"   ✅ Range créé: {exp_range}")
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Exact experience: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Exact experience erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 6: Combinaisons complexes
    # ========================================================
    def test_complex_filters(self):
        """Test combinaisons multiples de filtres"""
        print("\n" + "="*80)
        print("TEST 6: COMBINAISONS COMPLEXES")
        print("="*80)
        
        try:
            print("\n[6.1] 4 filtres avec OR multiples")
            
            filters = {
                "skills": ["python", "django", "flask"],
                "location": ["casablanca", "rabat", "marrakech"],
                "level": ["senior", "expert"],
                "contract_type": ["cdi", "cdd"]
            }
            
            result = search(filters=filters)
            
            print(f"   ✅ Mode: {result['mode_used']}")
            print(f"   ✅ Résultats: {result['stats']['total']}")
            
            self.results["passed"] += 1
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Complex filters: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 7: Unicode/Accents
    # ========================================================
    def test_unicode_handling(self):
        """Test caractères spéciaux et accents"""
        print("\n" + "="*80)
        print("TEST 7: UNICODE/ACCENTS")
        print("="*80)
        
        try:
            print("\n[7.1] Query avec accents")
            query = "développeur français spécialisé en données"
            
            processed = self.query_processor.process(query)
            
            print(f"   ✅ Tokens extraits: {len(processed['tokens'])}")
            print(f"   ✅ Skills détectés: {processed['skills']}")
            
            self.results["passed"] += 1
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Unicode: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 8: Query très longue
    # ========================================================
    def test_long_query(self):
        """Test query très longue (>500 chars)"""
        print("\n" + "="*80)
        print("TEST 8: QUERY TRÈS LONGUE")
        print("="*80)
        
        try:
            print("\n[8.1] Query 600 caractères")
            
            query = "python " * 100  # 700 chars
            
            processed = self.query_processor.process(query)
            
            print(f"   ✅ Query length: {len(query)} chars")
            print(f"   ✅ Tokens: {len(processed['tokens'])}")
            
            self.results["passed"] += 1
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Long query: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 9: Validation filtres invalides
    # ========================================================
    def test_invalid_filters(self):
        """Test validation filtres multiples invalides"""
        print("\n" + "="*80)
        print("TEST 9: VALIDATION FILTRES INVALIDES")
        print("="*80)
        
        try:
            print("\n[9.1] Expérience négative")
            is_valid, errors = self.filter_processor.validate({
                "experience": [-5, 10]
            })
            assert not is_valid, "❌ Devrait être invalide"
            print(f"   ✅ Erreurs: {errors}")
            
            print("\n[9.2] Filtre non supporté")
            is_valid, errors = self.filter_processor.validate({
                "invalid_filter": ["test"]
            })
            assert not is_valid, "❌ Devrait être invalide"
            print(f"   ✅ Erreurs: {errors}")
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Invalid filters: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Invalid filters erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # TEST 10: Performance
    # ========================================================
    def test_performance(self):
        """Test recherche retournant beaucoup de résultats"""
        print("\n" + "="*80)
        print("TEST 10: PERFORMANCE")
        print("="*80)
        
        try:
            print("\n[10.1] Recherche large (tous CVs Python)")
            
            import time
            start = time.time()
            
            result = search(filters={"skills": ["python"]})
            
            elapsed = time.time() - start
            
            print(f"   ✅ Résultats: {result['stats']['total']}")
            print(f"   ✅ Temps: {elapsed:.3f}s")
            
            assert elapsed < 5.0, f"❌ Trop lent: {elapsed}s"
            
            self.results["passed"] += 1
            
        except AssertionError as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Performance: {e}")
            print(f"\n❌ {e}")
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Performance erreur: {e}")
            print(f"\n❌ Erreur: {e}")
    
    # ========================================================
    # RAPPORT FINAL
    # ========================================================
    def print_report(self):
        """Rapport final détaillé"""
        print("\n" + "="*80)
        print("📊 RAPPORT FINAL - TESTS EXHAUSTIFS")
        print("="*80)
        
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n✅ Tests réussis: {self.results['passed']}")
        print(f"❌ Tests échoués: {self.results['failed']}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n⚠️ Erreurs:")
            for error in self.results["errors"]:
                print(f"   • {error}")
        
        print("\n" + "="*80)
        print("✅ CAS TESTÉS:")
        print("="*80)
        print("   1. Opérateurs NOT")
        print("   2. Compétences required/optional")
        print("   3. IDs invalides")
        print("   4. Filtres/query vides")
        print("   5. Expérience exacte")
        print("   6. Combinaisons complexes")
        print("   7. Unicode/accents")
        print("   8. Query très longue")
        print("   9. Validation filtres invalides")
        print("   10. Performance")


def main():
    """Point d'entrée"""
    print("="*80)
    print("🚀 TESTS EXHAUSTIFS DU MODÈLE BOOLÉEN")
    print("="*80)
    
    tester = TestBooleanSearchComplete()
    
    tester.test_not_operator()
    tester.test_required_optional_skills()
    tester.test_invalid_ids()
    tester.test_empty_filters()
    tester.test_exact_experience()
    tester.test_complex_filters()
    tester.test_unicode_handling()
    tester.test_long_query()
    tester.test_invalid_filters()
    tester.test_performance()
    
    tester.print_report()
    
    return 0 if tester.results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())