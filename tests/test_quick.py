"""
TEST RAPIDE - VÉRIFICATION EN 2 MINUTES
✅ Test connexion indexes
✅ Test recherche simple
✅ Test comptage documents
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "="*80)
print("⚡ TEST RAPIDE - RECHERCHE BOOLÉENNE")
print("="*80)

# TEST 1: Import modules
print("\n1️⃣ Test imports...")
try:
    from recherche_booleenne.boolean_engine import BooleanSearchEngine
    print("   ✅ Import BooleanSearchEngine OK")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# TEST 2: Initialisation moteur
print("\n2️⃣ Test initialisation moteur...")
try:
    engine = BooleanSearchEngine()
    print("   ✅ Moteur initialisé")
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# TEST 3: Comptage documents
print("\n3️⃣ Test comptage documents...")
from whoosh.index import open_dir
from recherche_booleenne.config import CV_INDEX_PATH, JOB_INDEX_PATH

try:
    cv_index = open_dir(CV_INDEX_PATH)
    job_index = open_dir(JOB_INDEX_PATH)
    
    with cv_index.searcher() as searcher:
        cv_count = searcher.doc_count_all()
        print(f"   ✅ {cv_count} CV indexés")
    
    with job_index.searcher() as searcher:
        job_count = searcher.doc_count_all()
        print(f"   ✅ {job_count} offres indexées")
    
    assert cv_count > 0, "Aucun CV indexé"
    assert job_count > 0, "Aucune offre indexée"
    
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# TEST 4: Recherche simple "python"
print("\n4️⃣ Test recherche 'python'...")
try:
    results = engine.search_jobs_for_candidate(
        query_text="python",
        limit=5
    )
    
    print(f"   ✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        job = results['results'][0]
        print(f"   🔹 Exemple: {job['titre']} - {job['entreprise']}")
    
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# TEST 5: Recherche avec filtres
print("\n5️⃣ Test recherche avec filtres...")
try:
    results = engine.search_jobs_for_candidate(
        filters={
            "skills": ["python"],
            "location": "casablanca"
        },
        limit=5
    )
    
    print(f"   ✅ {results['total']} offres (python + casablanca)")
    
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# TEST 6: Recherche CV
print("\n6️⃣ Test recherche CV...")
try:
    results = engine.search_cvs_for_recruiter(
        filters={"skills": ["react"]},
        limit=5
    )
    
    print(f"   ✅ {results['total']} CV trouvés (react)")
    
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    sys.exit(1)

# RÉSUMÉ
print("\n" + "="*80)
print("🎉 TOUS LES TESTS RAPIDES RÉUSSIS")
print("="*80)
print("\n💡 Pour tests détaillés:")
print("   python tests/test_boolean_search_complete.py")
print("\n✅ Système opérationnel !")
print("="*80 + "\n")