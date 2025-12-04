# Corrected test_3_api.py (Version with Engine Calls - Demo/Integration Test)
# Added sys.path to fix import from root. This is a demo script to test engine directly (not full HTTP API test).
import sys
from pathlib import Path

# Add project root to PYTHONPATH to fix 'No module named recherche_booleenne'
sys.path.insert(0, str(Path(__file__).parent.parent))

from recherche_booleenne.boolean_engine import BooleanSearchEngine

engine = BooleanSearchEngine()

# 1. Recherche textuelle simple (utilise NLP)
results = engine.search_jobs_for_candidate(
    query_text="python developer backend"
)

# 2. Recherche avec filtres complets
results = engine.search_jobs_for_candidate(
    query_text="python",
    filters={
        "skills": ["python", "django"],
        "boolean_operator": "AND",  # Doit avoir python ET django
        "location": "casablanca",
        "level": "senior",
        "experience_min": 5,
        "contract_type": "cdi",
        "tags": ["backend_developer"]  # ✅ NOUVEAU
    },
    limit=10
)

# 3. Recherche par tags uniquement (indexation semi-auto)
results = engine.search_by_tags(
    tags=["python", "senior", "casablanca"],
    is_cv=False,  # Recherche offres
    operator="OR"  # Au moins un tag matche
)

# 4. Recherche CV pour recruteur
results = engine.search_cvs_for_recruiter(
    filters={
        "skills": ["react", "typescript"],
        "boolean_operator": "OR",
        "experience_min": 3,
        "experience_max": 7
    }
)