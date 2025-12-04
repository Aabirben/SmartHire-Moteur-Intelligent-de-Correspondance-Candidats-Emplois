"""
CONFIGURATION - CHEMINS ADAPTÉS À VOTRE STRUCTURE
"""
import os
import json
from pathlib import Path

# ============================================================
# CHEMINS DE BASE
# ============================================================
# Récupère le dossier racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# CHEMINS DES INDEX WHOOSH
# ============================================================
INDEX_DIR = BASE_DIR / "SmartHire_INDEX_VRAI"
CV_INDEX_PATH = str(INDEX_DIR / "cv")
JOB_INDEX_PATH = str(INDEX_DIR / "jobs")

# ============================================================
# CHEMINS DES DONNÉES
# ============================================================
INDEX_MANUELLE_DIR = BASE_DIR / "index-manuelle"
RESULTATS_FINALS_DIR = INDEX_MANUELLE_DIR / "resultats_finals"

MAPPING_FILE = str(RESULTATS_FINALS_DIR / "mapping_ids.json")
CVS_ENRICHIES_FILE = str(RESULTATS_FINALS_DIR / "cvs_enrichies.json")
OFFRES_ENRICHIES_FILE = str(RESULTATS_FINALS_DIR / "offres_enrichies.json")
TAXONOMIE_FILE = str(INDEX_MANUELLE_DIR / "taxonomie.json")
SKILLS_FILE = str(BASE_DIR / "skills_json_file.json")

# ============================================================
# MAPPING POSTGRESQL (IDs système → IDs PostgreSQL)
# ============================================================
def load_mapping():
    """Charge le mapping des IDs depuis JSON"""
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cv_mapping = data.get("cvs", {})
        job_mapping = data.get("offres", {})
        
        print(f"✅ Mapping chargé: {len(cv_mapping)} CVs, {len(job_mapping)} offres")
        return cv_mapping, job_mapping
        
    except FileNotFoundError:
        print(f"⚠️ Fichier mapping introuvable: {MAPPING_FILE}")
        return {}, {}
    except Exception as e:
        print(f"❌ Erreur chargement mapping: {e}")
        return {}, {}

CV_MAPPING, JOB_MAPPING = load_mapping()

# ============================================================
# SCHÉMAS WHOOSH (issus de indexation_cv.py et indexation_offres.py)
# ============================================================
CV_SCHEMA_FIELDS = {
    "doc_id": "ID",              # ex: "cv_cv_01_amine_tazi"
    "nom": "TEXT",
    "titre_profil": "TEXT",
    "localisation": "TEXT",
    "annees": "NUMERIC",         # Années d'expérience
    "description_experience": "TEXT",
    "competences": "KEYWORD",    # Format: "python,django,react"
    "projets": "TEXT",
    "resume_complet": "TEXT",
    "texte_pretraite": "TEXT"    # Texte NLP (lemmatisé, sans stopwords)
}

JOB_SCHEMA_FIELDS = {
    "job_id": "ID",              # ex: "offre_job-0001-2025"
    "titre_poste": "TEXT",
    "description": "TEXT",
    "titre_poste_processed": "TEXT",      # Version NLP
    "description_processed": "TEXT",       # Version NLP
    "competences_requises": "KEYWORD",     # Format: "python,django,react"
    "localisation": "TEXT",
    "niveau_souhaite": "ID",               # junior/senior/expert
    "domaine": "ID",
    "annees_min": "NUMERIC",
    "annees_max": "NUMERIC",
    "entreprise": "TEXT",
    "type_contrat": "TEXT",
    "mode_travail": "TEXT",
    "nb_tokens_original": "NUMERIC",
    "nb_tokens_processed": "NUMERIC"
}

# ============================================================
# PARAMÈTRES DE RECHERCHE
# ============================================================
SEARCH_CONFIG = {
    "default_limit": 10,
    "max_limit": 50,
    "use_processed_text": True,  # Utiliser texte NLP
    "min_score": 0.0             # Score minimum Whoosh (0 = tout)
}

# ============================================================
# VÉRIFICATION AU CHARGEMENT
# ============================================================
def verify_setup():
    """Vérifie que tout est prêt"""
    errors = []
    warnings = []
    
    # Vérification index
    if not os.path.exists(CV_INDEX_PATH):
        errors.append(f"❌ Index CV manquant: {CV_INDEX_PATH}")
    else:
        print(f"✅ Index CV trouvé: {CV_INDEX_PATH}")
    
    if not os.path.exists(JOB_INDEX_PATH):
        errors.append(f"❌ Index offres manquant: {JOB_INDEX_PATH}")
    else:
        print(f"✅ Index offres trouvé: {JOB_INDEX_PATH}")
    
    # Vérification mapping
    if not CV_MAPPING:
        warnings.append(f"⚠️ Mapping CV vide (fichier: {MAPPING_FILE})")
    else:
        print(f"✅ Mapping CV: {len(CV_MAPPING)} documents")
    
    if not JOB_MAPPING:
        warnings.append(f"⚠️ Mapping offres vide")
    else:
        print(f"✅ Mapping offres: {len(JOB_MAPPING)} documents")
    
    # Affichage des erreurs/warnings
    if errors:
        print("\n" + "\n".join(errors))
        print("\n💡 Exécutez d'abord:")
        print("   1. python indexation_cv.py")
        print("   2. python indexation_offre.py")
        return False
    
    if warnings:
        print("\n" + "\n".join(warnings))
    
    print("\n✅ Configuration validée!")
    return True

# Vérification au chargement du module
if __name__ != "__main__":
    verify_setup()