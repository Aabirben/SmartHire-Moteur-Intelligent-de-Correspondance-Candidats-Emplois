"""
============================================================================
SMARTHIRE - Configuration Centralisée
Tous les paramètres du système en un seul endroit
============================================================================
"""

import os
from pathlib import Path

# ========================================================
# CHEMINS DE BASE
# ========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Dossiers de données
CV_FOLDER = DATA_DIR / "cvs"
JOB_FOLDER = DATA_DIR / "jobs"
INDEX_DIR = DATA_DIR / "index"
SKILLS_FILE = DATA_DIR / "skills.json"

# Dossiers d'index
CV_INDEX = INDEX_DIR / "cv_index"
JOB_INDEX = INDEX_DIR / "job_index"
QUERY_INDEX = INDEX_DIR / "query_index"

# ========================================================
# CONFIGURATION NLTK
# ========================================================
NLTK_DOWNLOADS = [
    'punkt',
    'punkt_tab',
    'stopwords',
    'wordnet',
    'omw-1.4',
    'averaged_perceptron_tagger'
]

# Stopwords personnalisés
CUSTOM_STOPWORDS = {
    'cv', 'resume', 'curriculum', 'vitae', 'email', 'phone',
    'mobile', 'address', 'page', 'http', 'https', 'www',
    'etc', 'via', 'plus', 'moins', 'tres', 'beaucoup'
}

# ========================================================
# VILLES MAROCAINES
# ========================================================
MOROCCAN_CITIES = {
    "casablanca": "Casablanca",
    "rabat": "Rabat",
    "marrakech": "Marrakech",
    "fes": "Fès",
    "fès": "Fès",
    "tangier": "Tanger",
    "tanger": "Tanger",
    "agadir": "Agadir",
    "meknes": "Meknès",
    "meknès": "Meknès",
    "sale": "Salé",
    "salé": "Salé",
    "kenitra": "Kénitra",
    "kénitra": "Kénitra",
    "oujda": "Oujda",
    "tetouan": "Tétouan",
    "tétouan": "Tétouan",
    "safi": "Safi",
    "mohammedia": "Mohammedia",
    "el jadida": "El Jadida",
    "beni mellal": "Beni Mellal",
    "nador": "Nador",
}

# ========================================================
# NIVEAUX D'EXPÉRIENCE
# ========================================================
NIVEAU_MAPPING = {
    "Junior": (0, 2),
    "Mid-Level": (3, 5),
    "Senior": (6, 10),
    "Expert": (11, 20)
}

# ========================================================
# LOGGING
# ========================================================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S'
}

# ========================================================
# CRÉATION DES DOSSIERS
# ========================================================
def create_directories():
    """Crée tous les dossiers nécessaires"""
    directories = [
        CV_FOLDER,
        JOB_FOLDER,
        CV_INDEX,
        JOB_INDEX,
        QUERY_INDEX
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    create_directories()
    print("✅ Dossiers créés avec succès")