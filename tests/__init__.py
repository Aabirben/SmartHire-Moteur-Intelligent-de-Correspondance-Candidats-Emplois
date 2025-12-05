# ============================================================
# tests/__init__.py
# ============================================================
"""Package de tests SmartHire"""

# ============================================================
# tests/test_0_database.py - TEST DATABASE
# ============================================================
"""
TEST 1 : VÉRIFICATION DATABASE
Vérifie la connexion PostgreSQL et les tables
"""
import sys
from pathlib import Path

# Ajoute le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db_connection

def test_database_connection():
    """Test connexion PostgreSQL"""
    print("\n" + "="*80)
    print("🧪 TEST 1 : CONNEXION DATABASE")
    print("="*80)
    
    conn = get_db_connection()
    
    assert conn is not None, "❌ Connexion échouée"
    
    cur = conn.cursor()
    
    # Vérifie version PostgreSQL
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✅ PostgreSQL: {version.split(',')[0]}")
    
    # Vérifie tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cur.fetchall()]
    
    expected_tables = ['users', 'cvs', 'offres', 'matching_results', 'candidatures']
    
    for table in expected_tables:
        assert table in tables, f"❌ Table manquante: {table}"
        print(f"✅ Table '{table}' existe")
    
    # Compte documents
    cur.execute("SELECT COUNT(*) FROM cvs")
    cv_count = cur.fetchone()[0]
    print(f"📊 {cv_count} CV en base")
    
    cur.execute("SELECT COUNT(*) FROM offres")
    offre_count = cur.fetchone()[0]
    print(f"📊 {offre_count} offres en base")
    
    cur.close()
    conn.close()
    
    print("\n✅ TEST DATABASE RÉUSSI")
    print("="*80)

if __name__ == "__main__":
    test_database_connection()


# ============================================================
# tests/test_1_indexation.py - TEST INDEXATION
# ============================================================
"""
TEST 2 : VÉRIFICATION INDEXATION WHOOSH
Vérifie les index CV et Offres
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from whoosh.index import open_dir
from recherche_booleenne.config import (
    CV_INDEX_PATH,
    JOB_INDEX_PATH,
    CV_MAPPING,
    JOB_MAPPING
)

def test_indexation():
    """Test index Whoosh"""
    print("\n" + "="*80)
    print("🧪 TEST 2 : INDEXATION WHOOSH")
    print("="*80)
    
    # Test index CV
    print("\n📂 Index CV:")
    try:
        cv_index = open_dir(CV_INDEX_PATH)
        with cv_index.searcher() as searcher:
            cv_doc_count = searcher.doc_count_all()
            print(f"✅ Index CV ouvert: {cv_doc_count} documents")
            
            # Vérifie schéma
            schema_fields = list(cv_index.schema.names())
            print(f"✅ Champs: {', '.join(schema_fields[:5])}...")
            
            # Test recherche simple
            from whoosh.qparser import QueryParser
            parser = QueryParser("competences", schema=cv_index.schema)
            query = parser.parse("python")
            results = searcher.search(query, limit=5)
            print(f"✅ Test recherche 'python': {len(results)} résultats")
            
    except Exception as e:
        print(f"❌ Erreur index CV: {e}")
        raise
    
    # Test index Offres
    print("\n📂 Index Offres:")
    try:
        job_index = open_dir(JOB_INDEX_PATH)
        with job_index.searcher() as searcher:
            job_doc_count = searcher.doc_count_all()
            print(f"✅ Index offres ouvert: {job_doc_count} documents")
            
            schema_fields = list(job_index.schema.names())
            print(f"✅ Champs: {', '.join(schema_fields[:5])}...")
            
            parser = QueryParser("competences_requises", schema=job_index.schema)
            query = parser.parse("python")
            results = searcher.search(query, limit=5)
            print(f"✅ Test recherche 'python': {len(results)} résultats")
            
    except Exception as e:
        print(f"❌ Erreur index offres: {e}")
        raise
    
    # Test mapping
    print(f"\n📊 Mapping:")
    print(f"✅ {len(CV_MAPPING)} CV mappés")
    print(f"✅ {len(JOB_MAPPING)} offres mappées")
    
    print("\n✅ TEST INDEXATION RÉUSSI")
    print("="*80)

if __name__ == "__main__":
    test_indexation()


# ============================================================
# tests/test_2_boolean_search.py - TEST RECHERCHE BOOLÉENNE
# ============================================================
"""
TEST 3 : MOTEUR DE RECHERCHE BOOLÉEN
Tests unitaires et d'intégration
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from recherche_booleenne.boolean_engine import BooleanSearchEngine

def test_search_jobs_python():
    """Test recherche offres Python"""
    print("\n" + "="*80)
    print("🧪 TEST 3.1 : RECHERCHE OFFRES 'PYTHON'")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_jobs_for_candidate(
        query_text="python",
        filters={"skills": ["python"]},
        limit=10
    )
    
    print(f"\n✅ {results['total']} offres trouvées")
    
    assert results['total'] > 0, "❌ Aucune offre trouvée"
    
    for i, job in enumerate(results['results'][:3], 1):
        print(f"\n{i}. {job['titre']} - {job['entreprise']}")
        print(f"   Compétences: {', '.join(job['competences'][:5])}")
        assert 'python' in job['competences'], f"❌ Python manquant dans offre {i}"
    
    print("\n✅ TEST RÉUSSI")

def test_search_jobs_casablanca():
    """Test recherche offres Casablanca"""
    print("\n" + "="*80)
    print("🧪 TEST 3.2 : RECHERCHE OFFRES 'CASABLANCA'")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_jobs_for_candidate(
        filters={"location": "casablanca"},
        limit=10
    )
    
    print(f"\n✅ {results['total']} offres trouvées")
    
    assert results['total'] > 0, "❌ Aucune offre trouvée"
    
    for job in results['results'][:2]:
        print(f"• {job['titre']} - {job['localisation']}")
        assert 'casablanca' in job['localisation'].lower(), "❌ Localisation incorrecte"
    
    print("\n✅ TEST RÉUSSI")

def test_search_jobs_senior():
    """Test recherche offres senior"""
    print("\n" + "="*80)
    print("🧪 TEST 3.3 : RECHERCHE OFFRES 'SENIOR'")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_jobs_for_candidate(
        filters={"level": "senior"},
        limit=10
    )
    
    print(f"\n✅ {results['total']} offres trouvées")
    
    assert results['total'] > 0, "❌ Aucune offre trouvée"
    
    for job in results['results'][:2]:
        print(f"• {job['titre']} - Niveau: {job['niveau']}")
        assert job['niveau'] == 'senior', "❌ Niveau incorrect"
    
    print("\n✅ TEST RÉUSSI")

def test_search_cvs_react():
    """Test recherche CV React"""
    print("\n" + "="*80)
    print("🧪 TEST 3.4 : RECHERCHE CV 'REACT'")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_cvs_for_recruiter(
        filters={"skills": ["react"]},
        limit=10
    )
    
    print(f"\n✅ {results['total']} CV trouvés")
    
    assert results['total'] > 0, "❌ Aucun CV trouvé"
    
    for i, cv in enumerate(results['results'][:3], 1):
        print(f"\n{i}. {cv['nom']} - {cv['titre']}")
        print(f"   Compétences: {', '.join(cv['competences'][:5])}")
        assert 'react' in cv['competences'], f"❌ React manquant dans CV {i}"
    
    print("\n✅ TEST RÉUSSI")

def test_search_cvs_experience():
    """Test recherche CV par expérience"""
    print("\n" + "="*80)
    print("🧪 TEST 3.5 : RECHERCHE CV 'EXPÉRIENCE 3-10 ANS'")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_cvs_for_recruiter(
        filters={"experience": [3, 10]},
        limit=10
    )
    
    print(f"\n✅ {results['total']} CV trouvés")
    
    assert results['total'] > 0, "❌ Aucun CV trouvé"
    
    for cv in results['results'][:3]:
        print(f"• {cv['nom']} - {cv['experience']} ans d'expérience")
        assert 3 <= cv['experience'] <= 10, f"❌ Expérience hors plage: {cv['experience']}"
    
    print("\n✅ TEST RÉUSSI")

def test_complex_query():
    """Test requête complexe (multi-filtres)"""
    print("\n" + "="*80)
    print("🧪 TEST 3.6 : REQUÊTE COMPLEXE (Python + Casablanca + Senior)")
    print("="*80)
    
    engine = BooleanSearchEngine()
    
    results = engine.search_jobs_for_candidate(
        filters={
            "skills": ["python"],
            "location": "casablanca",
            "level": "senior"
        },
        limit=10
    )
    
    print(f"\n✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        for job in results['results'][:2]:
            print(f"\n• {job['titre']}")
            print(f"  Compétences: {', '.join(job['competences'][:3])}")
            print(f"  Lieu: {job['localisation']}")
            print(f"  Niveau: {job['niveau']}")
            
            assert 'python' in job['competences'], "❌ Python manquant"
            assert 'casablanca' in job['localisation'].lower(), "❌ Localisation incorrecte"
            assert job['niveau'] == 'senior', "❌ Niveau incorrect"
    
    print("\n✅ TEST RÉUSSI")

if __name__ == "__main__":
    test_search_jobs_python()
    test_search_jobs_casablanca()
    test_search_jobs_senior()
    test_search_cvs_react()
    test_search_cvs_experience()
    test_complex_query()


# ============================================================
# tests/test_3_api.py - TEST API FLASK
# ============================================================
"""
TEST 4 : API FLASK
Test endpoints HTTP
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json

BASE_URL = "http://localhost:5000"

def test_api_health():
    """Test endpoint /health"""
    print("\n" + "="*80)
    print("🧪 TEST 4.1 : API HEALTH")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/health")
    
    assert response.status_code == 200, f"❌ Status code: {response.status_code}"
    
    data = response.json()
    print(f"✅ Status: {data['status']}")
    print(f"✅ Version: {data['version']}")
    
    print("\n✅ TEST RÉUSSI")

def test_api_search_jobs():
    """Test endpoint POST /api/search/jobs"""
    print("\n" + "="*80)
    print("🧪 TEST 4.2 : API SEARCH JOBS")
    print("="*80)
    
    payload = {
        "query": "python developer",
        "filters": {
            "skills": ["python"],
            "location": "casablanca"
        },
        "limit": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/search/jobs",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200, f"❌ Status code: {response.status_code}"
    
    data = response.json()
    print(f"✅ {data['total']} offres trouvées")
    
    if data['results']:
        job = data['results'][0]
        print(f"✅ Exemple: {job['titre']} - {job['entreprise']}")
    
    print("\n✅ TEST RÉUSSI")

def test_api_search_cvs():
    """Test endpoint POST /api/search/cvs"""
    print("\n" + "="*80)
    print("🧪 TEST 4.3 : API SEARCH CVS")
    print("="*80)
    
    payload = {
        "filters": {
            "skills": ["react"],
            "experience": [3, 10]
        },
        "limit": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/search/cvs",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200, f"❌ Status code: {response.status_code}"
    
    data = response.json()
    print(f"✅ {data['total']} CV trouvés")
    
    if data['results']:
        cv = data['results'][0]
        print(f"✅ Exemple: {cv['nom']} - {cv['titre']}")
    
    print("\n✅ TEST RÉUSSI")

if __name__ == "__main__":
    print("\n⚠️  Assurez-vous que l'API Flask tourne (python run_api.py)\n")
    
    try:
        test_api_health()
        test_api_search_jobs()
        test_api_search_cvs()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS API RÉUSSIS")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: L'API ne répond pas")
        print("💡 Démarrez l'API avec: python run_api.py")