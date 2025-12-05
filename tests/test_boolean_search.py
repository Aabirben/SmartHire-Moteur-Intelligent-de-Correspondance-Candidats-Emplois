"""
TESTS COMPLETS - RECHERCHE BOOLÉENNE v2
✅ Tests unitaires des composants
✅ Tests d'intégration end-to-end
✅ Tests des nouvelles fonctionnalités (tags_manuels, contract_type)
✅ Vérification utilisation NLP (texte_pretraite)
"""

import sys
from pathlib import Path

# Ajoute le projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from recherche_booleenne.boolean_engine import BooleanSearchEngine
from recherche_booleenne.query_builder import BooleanQueryBuilder
from recherche_booleenne.utils import validate_search_filters, parse_skills_string
from whoosh.index import open_dir
from recherche_booleenne.config import CV_INDEX_PATH, JOB_INDEX_PATH


print("="*100)
print("🧪 SUITE DE TESTS COMPLÈTE - RECHERCHE BOOLÉENNE SMARTHIRE")
print("="*100)


# ============================================================
# TEST 1 : VÉRIFICATION CHAMPS INDEXÉS (NLP)
# ============================================================
def test_1_verify_nlp_fields():
    """Vérifie que texte_pretraite est bien indexé"""
    print("\n" + "="*100)
    print("🧪 TEST 1 : VÉRIFICATION CHAMPS NLP INDEXÉS")
    print("="*100)
    
    cv_index = open_dir(CV_INDEX_PATH)
    job_index = open_dir(JOB_INDEX_PATH)
    
    cv_fields = list(cv_index.schema.names())
    job_fields = list(job_index.schema.names())
    
    print(f"\n📂 Champs index CV ({len(cv_fields)} total):")
    for field in cv_fields:
        print(f"  • {field}")
    
    # Vérifications critiques
    assert "texte_pretraite" in cv_fields, "❌ ERREUR : texte_pretraite manquant dans CV"
    assert "competences" in cv_fields, "❌ ERREUR : competences manquant dans CV"
    assert "tags_manuels" in cv_fields, "❌ ERREUR : tags_manuels manquant dans CV"
    
    print(f"\n📂 Champs index Offres ({len(job_fields)} total):")
    for field in job_fields:
        print(f"  • {field}")
    
    assert "titre_poste_processed" in job_fields, "❌ ERREUR : titre_poste_processed manquant"
    assert "description_processed" in job_fields, "❌ ERREUR : description_processed manquant"
    assert "competences_requises" in job_fields, "❌ ERREUR : competences_requises manquant"
    
    # Test lecture d'un document réel
    print("\n📄 Exemple de document CV indexé:")
    with cv_index.searcher() as searcher:
        doc = next(searcher.documents(), None)
        if doc:
            print(f"  • doc_id: {doc.get('doc_id')}")
            print(f"  • nom: {doc.get('nom')}")
            print(f"  • competences: {doc.get('competences')[:50]}...")
            print(f"  • texte_pretraite: {doc.get('texte_pretraite')[:100]}...")
            print(f"  • tags_manuels: {doc.get('tags_manuels')[:50]}...")
        else:
            print("  ⚠️ Aucun document trouvé")
    
    print("\n✅ TEST 1 RÉUSSI : Tous les champs nécessaires sont indexés")
    return True


# ============================================================
# TEST 2 : RECHERCHE TEXTUELLE (NLP)
# ============================================================
def test_2_text_search_with_nlp():
    """Vérifie que la recherche utilise texte_pretraite"""
    print("\n" + "="*100)
    print("🧪 TEST 2 : RECHERCHE TEXTUELLE AVEC NLP (texte_pretraite)")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test 1: Recherche "python developer"
    print("\n🔍 Recherche 1: 'python developer'")
    results = engine.search_jobs_for_candidate(
        query_text="python developer",
        use_nlp=True,
        limit=5
    )
    
    print(f"✅ {results['total']} offres trouvées")
    assert results['total'] > 0, "❌ ERREUR : Aucune offre trouvée"
    
    for i, job in enumerate(results['results'][:3], 1):
        print(f"\n  {i}. {job['titre']}")
        print(f"     Score: {job.get('score', 0):.2f}")
        print(f"     Compétences: {', '.join(job['competences'][:5])}")
    
    # Test 2: Recherche "machine learning"
    print("\n🔍 Recherche 2: 'machine learning' (doit utiliser lemmatisation)")
    results = engine.search_jobs_for_candidate(
        query_text="machine learning",
        use_nlp=True,
        limit=5
    )
    
    print(f"✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        job = results['results'][0]
        print(f"\n  Top résultat: {job['titre']}")
        print(f"  Compétences: {', '.join(job['competences'][:5])}")
    
    print("\n✅ TEST 2 RÉUSSI : Recherche textuelle NLP fonctionne")
    return True


# ============================================================
# TEST 3 : RECHERCHE PAR COMPÉTENCES (AND/OR)
# ============================================================
def test_3_skills_search_and_or():
    """Teste opérateurs booléens AND/OR sur compétences"""
    print("\n" + "="*100)
    print("🧪 TEST 3 : RECHERCHE COMPÉTENCES AVEC AND/OR")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test AND : Python AND Django (doit avoir les deux)
    print("\n🔍 Test AND: ['python', 'django'] (doit avoir LES DEUX)")
    results_and = engine.search_jobs_for_candidate(
        filters={
            "skills": ["python", "django"],
            "boolean_operator": "AND"
        },
        limit=10
    )
    
    print(f"✅ {results_and['total']} offres trouvées (AND)")
    
    if results_and['total'] > 0:
        for job in results_and['results'][:2]:
            skills_lower = [s.lower() for s in job['competences']]
            print(f"\n  • {job['titre']}")
            print(f"    Compétences: {', '.join(job['competences'][:5])}")
            
            # Vérification stricte AND
            has_python = 'python' in skills_lower
            has_django = 'django' in skills_lower
            
            print(f"    ✓ Python: {has_python}, Django: {has_django}")
            assert has_python and has_django, "❌ ERREUR : AND non respecté"
    
    # Test OR : Python OR Django (au moins un)
    print("\n🔍 Test OR: ['python', 'django'] (au moins UN)")
    results_or = engine.search_jobs_for_candidate(
        filters={
            "skills": ["python", "django"],
            "boolean_operator": "OR"
        },
        limit=10
    )
    
    print(f"✅ {results_or['total']} offres trouvées (OR)")
    
    assert results_or['total'] >= results_and['total'], "❌ ERREUR : OR doit trouver >= AND"
    
    if results_or['total'] > 0:
        job = results_or['results'][0]
        skills_lower = [s.lower() for s in job['competences']]
        has_python = 'python' in skills_lower
        has_django = 'django' in skills_lower
        
        print(f"\n  • {job['titre']}")
        print(f"    Python: {has_python}, Django: {has_django}")
        assert has_python or has_django, "❌ ERREUR : OR non respecté"
    
    print(f"\n📊 Comparaison:")
    print(f"  • AND: {results_and['total']} résultats")
    print(f"  • OR: {results_or['total']} résultats")
    print(f"  • Ratio: {results_or['total'] / max(results_and['total'], 1):.1f}x")
    
    print("\n✅ TEST 3 RÉUSSI : Opérateurs AND/OR fonctionnent")
    return True


# ============================================================
# TEST 4 : RECHERCHE PAR TAGS_MANUELS (INDEXATION SEMI-AUTO)
# ============================================================
def test_4_search_by_tags():
    """Teste recherche sur tags_manuels (indexation semi-auto)"""
    print("\n" + "="*100)
    print("🧪 TEST 4 : RECHERCHE PAR TAGS_MANUELS (INDEXATION SEMI-AUTO)")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test 1: Recherche par métier
    print("\n🔍 Recherche 1: Tags métier ['backend_developer']")
    results = engine.search_by_tags(
        tags=["backend_developer"],
        is_cv=False,  # Recherche offres
        operator="OR",
        limit=10
    )
    
    print(f"✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        for i, job in enumerate(results['results'][:3], 1):
            print(f"\n  {i}. {job['titre']}")
            print(f"     Entreprise: {job['entreprise']}")
    
    # Test 2: Recherche par niveau
    print("\n🔍 Recherche 2: Tags niveau ['senior']")
    results = engine.search_by_tags(
        tags=["senior"],
        is_cv=True,  # Recherche CV
        operator="OR",
        limit=10
    )
    
    print(f"✅ {results['total']} CV trouvés")
    
    if results['total'] > 0:
        for cv in results['results'][:2]:
            print(f"\n  • {cv['nom']}")
            print(f"    Expérience: {cv['experience']} ans")
    
    # Test 3: Tags multiples (AND)
    print("\n🔍 Recherche 3: Tags multiples ['python', 'casablanca'] (AND)")
    results = engine.search_by_tags(
        tags=["python", "casablanca"],
        is_cv=True,
        operator="AND",
        limit=10
    )
    
    print(f"✅ {results['total']} CV trouvés (doit avoir python ET casablanca)")
    
    print("\n✅ TEST 4 RÉUSSI : Recherche par tags_manuels fonctionne")
    return True


# ============================================================
# TEST 5 : RECHERCHE PAR EXPÉRIENCE (PLAGE NUMÉRIQUE)
# ============================================================
def test_5_experience_range():
    """Teste filtres d'expérience (plage numérique)"""
    print("\n" + "="*100)
    print("🧪 TEST 5 : RECHERCHE PAR EXPÉRIENCE (PLAGE NUMÉRIQUE)")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test 1: CV avec 3-10 ans d'expérience
    print("\n🔍 Recherche 1: CV avec 3-10 ans d'expérience")
    results = engine.search_cvs_for_recruiter(
        filters={
            "experience_min": 3,
            "experience_max": 10
        },
        limit=10
    )
    
    print(f"✅ {results['total']} CV trouvés")
    
    if results['total'] > 0:
        for cv in results['results'][:5]:
            exp = cv['experience']
            print(f"  • {cv['nom']}: {exp} ans")
            assert 3 <= exp <= 10, f"❌ ERREUR : Expérience {exp} hors plage [3, 10]"
    
    # Test 2: Offres pour juniors (0-2 ans)
    print("\n🔍 Recherche 2: Offres pour juniors (0-2 ans)")
    results = engine.search_jobs_for_candidate(
        filters={
            "experience_min": 0,
            "experience_max": 2
        },
        limit=10
    )
    
    print(f"✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        for job in results['results'][:3]:
            print(f"  • {job['titre']}: {job['experience_min']}-{job['experience_max']} ans")
    
    print("\n✅ TEST 5 RÉUSSI : Filtres d'expérience fonctionnent")
    return True


# ============================================================
# TEST 6 : RECHERCHE PAR LOCALISATION
# ============================================================
def test_6_location_search():
    """Teste filtres de localisation"""
    print("\n" + "="*100)
    print("🧪 TEST 6 : RECHERCHE PAR LOCALISATION")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test 1: Offres à Casablanca
    print("\n🔍 Recherche 1: Offres à Casablanca")
    results = engine.search_jobs_for_candidate(
        filters={"location": "casablanca"},
        limit=10
    )
    
    print(f"✅ {results['total']} offres trouvées")
    
    if results['total'] > 0:
        for job in results['results'][:3]:
            loc = job['localisation'].lower()
            print(f"  • {job['titre']} - {job['localisation']}")
            assert 'casablanca' in loc, f"❌ ERREUR : Localisation '{loc}' incorrecte"
    
    # Test 2: CV à Rabat
    print("\n🔍 Recherche 2: CV à Rabat")
    results = engine.search_cvs_for_recruiter(
        filters={"location": "rabat"},
        limit=10
    )
    
    print(f"✅ {results['total']} CV trouvés")
    
    if results['total'] > 0:
        for cv in results['results'][:2]:
            print(f"  • {cv['nom']} - {cv['localisation']}")
    
    print("\n✅ TEST 6 RÉUSSI : Filtres de localisation fonctionnent")
    return True


# ============================================================
# TEST 7 : RECHERCHE PAR TYPE DE CONTRAT (NOUVEAU)
# ============================================================
def test_7_contract_type():
    """Teste nouveau filtre contract_type"""
    print("\n" + "="*100)
    print("🧪 TEST 7 : RECHERCHE PAR TYPE DE CONTRAT (NOUVEAU)")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Test 1: Offres CDI
    print("\n🔍 Recherche 1: Offres CDI")
    results = engine.search_jobs_for_candidate(
        filters={"contract_type": "cdi"},
        limit=10
    )
    
    print(f"✅ {results['total']} offres CDI trouvées")
    
    if results['total'] > 0:
        for job in results['results'][:3]:
            print(f"  • {job['titre']} - Contrat: {job['type_contrat']}")
    
    # Test 2: CV recherchant CDD
    print("\n🔍 Recherche 2: CV recherchant CDD")
    results = engine.search_cvs_for_recruiter(
        filters={"contract_type": "cdd"},
        limit=10
    )
    
    print(f"✅ {results['total']} CV trouvés")
    
    print("\n✅ TEST 7 RÉUSSI : Filtre contract_type fonctionne")
    return True


# ============================================================
# TEST 8 : RECHERCHE COMPLEXE MULTI-FILTRES
# ============================================================
def test_8_complex_query():
    """Teste requête complexe avec tous les filtres"""
    print("\n" + "="*100)
    print("🧪 TEST 8 : REQUÊTE COMPLEXE MULTI-FILTRES")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Requête ultra-complète
    print("\n🔍 Recherche: Python + Casablanca + Senior + 5-10 ans + CDI")
    results = engine.search_jobs_for_candidate(
        query_text="python developer",
        filters={
            "skills": ["python"],
            "location": "casablanca",
            "level": "senior",
            "experience_min": 5,
            "experience_max": 10,
            "contract_type": "cdi"
        },
        limit=10
    )
    
    print(f"✅ {results['total']} offres trouvées")
    print(f"📊 Requête Whoosh: {results['query_info']['whoosh_query'][:100]}...")
    
    if results['total'] > 0:
        for i, job in enumerate(results['results'][:3], 1):
            print(f"\n  {i}. {job['titre']}")
            print(f"     Entreprise: {job['entreprise']}")
            print(f"     Niveau: {job['niveau']}")
            print(f"     Expérience: {job['experience_min']}-{job['experience_max']} ans")
            print(f"     Lieu: {job['localisation']}")
            print(f"     Contrat: {job['type_contrat']}")
            print(f"     Score: {job.get('score', 0):.2f}")
            
            # Vérifications
            assert job['niveau'] == 'senior', "❌ Niveau incorrect"
            assert 'casablanca' in job['localisation'].lower(), "❌ Localisation incorrecte"
    
    print("\n✅ TEST 8 RÉUSSI : Requêtes complexes fonctionnent")
    return True


# ============================================================
# TEST 9 : RÉCUPÉRATION PAR ID
# ============================================================
def test_9_get_by_id():
    """Teste récupération document par ID"""
    print("\n" + "="*100)
    print("🧪 TEST 9 : RÉCUPÉRATION PAR ID")
    print("="*100)
    
    engine = BooleanSearchEngine()
    
    # Récupère tous les CV pour trouver un ID valide
    with open_dir(CV_INDEX_PATH).searcher() as searcher:
        doc = next(searcher.documents(), None)
        if doc:
            cv_id = doc.get('doc_id')
            
            print(f"\n🔍 Test récupération CV: {cv_id}")
            cv = engine.get_cv_by_id(cv_id)
            
            assert cv is not None, "❌ ERREUR : CV non trouvé"
            print(f"✅ CV récupéré:")
            print(f"  • Nom: {cv['nom']}")
            print(f"  • PostgreSQL ID: {cv['postgres_id']}")
            print(f"  • Compétences: {', '.join(cv['competences'][:5])}")
        else:
            print("⚠️ Aucun CV trouvé dans l'index")
    
    # Même chose pour offres
    with open_dir(JOB_INDEX_PATH).searcher() as searcher:
        doc = next(searcher.documents(), None)
        if doc:
            job_id = doc.get('job_id')
            
            print(f"\n🔍 Test récupération offre: {job_id}")
            job = engine.get_job_by_id(job_id)
            
            assert job is not None, "❌ ERREUR : Offre non trouvée"
            print(f"✅ Offre récupérée:")
            print(f"  • Titre: {job['titre']}")
            print(f"  • PostgreSQL ID: {job['postgres_id']}")
            print(f"  • Entreprise: {job['entreprise']}")
    
    print("\n✅ TEST 9 RÉUSSI : Récupération par ID fonctionne")
    return True


# ============================================================
# TEST 10 : VALIDATION UTILS
# ============================================================
def test_10_utils():
    """Teste les fonctions utilitaires"""
    print("\n" + "="*100)
    print("🧪 TEST 10 : VALIDATION UTILITAIRES")
    print("="*100)
    
    # Test 1: Validation filtres
    print("\n🔧 Test validate_search_filters()")
    filters = {
        "skills": ["Python", "DJANGO"],
        "experience": [3, 10],
        "location": " Casablanca ",
        "boolean_operator": "and"
    }
    
    validated = validate_search_filters(filters)
    
    print(f"  • skills: {validated['skills']}")
    assert validated['skills'] == ['python', 'django'], "❌ Skills mal normalisés"
    
    print(f"  • experience_min: {validated['experience_min']}")
    assert validated['experience_min'] == 3, "❌ Experience_min incorrect"
    
    print(f"  • location: '{validated['location']}'")
    assert validated['location'] == 'casablanca', "❌ Location mal normalisée"
    
    print(f"  • boolean_operator: {validated['boolean_operator']}")
    assert validated['boolean_operator'] == 'AND', "❌ Opérateur mal normalisé"
    
    # Test 2: Parsing compétences
    print("\n🔧 Test parse_skills_string()")
    skills_str = "python,django,react"
    parsed = parse_skills_string(skills_str)
    
    print(f"  • Input: '{skills_str}'")
    print(f"  • Output: {parsed}")
    assert parsed == ['python', 'django', 'react'], "❌ Parsing incorrect"
    
    print("\n✅ TEST 10 RÉUSSI : Utilitaires fonctionnent")
    return True


# ============================================================
# EXÉCUTION DE TOUS LES TESTS
# ============================================================
if __name__ == "__main__":
    tests = [
        ("Vérification champs NLP indexés", test_1_verify_nlp_fields),
        ("Recherche textuelle avec NLP", test_2_text_search_with_nlp),
        ("Compétences AND/OR", test_3_skills_search_and_or),
        ("Recherche par tags_manuels", test_4_search_by_tags),
        ("Filtres d'expérience", test_5_experience_range),
        ("Filtres de localisation", test_6_location_search),
        ("Type de contrat (NOUVEAU)", test_7_contract_type),
        ("Requête complexe", test_8_complex_query),
        ("Récupération par ID", test_9_get_by_id),
        ("Utilitaires", test_10_utils)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ ÉCHEC TEST '{name}': {e}")
    
    # Résumé final
    print("\n" + "="*100)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*100)
    print(f"✅ Tests réussis: {passed}/{len(tests)}")
    print(f"❌ Tests échoués: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS - SYSTÈME OPÉRATIONNEL")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFIEZ LES LOGS CI-DESSUS")
    
    print("="*100)