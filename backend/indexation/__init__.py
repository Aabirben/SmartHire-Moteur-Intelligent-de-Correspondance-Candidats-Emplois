"""
============================================================================
SMARTHIRE - Indexation Package (CORRIGÉ)
Module d'indexation automatique avec preprocessing NLP pour CV, offres et requêtes
============================================================================
"""

from .preprocessing import (
    pretraiter_texte,
    pretraiter_competences,
    nettoyer_texte_brut,
    compter_tokens,
    calculer_reduction,
    init_nltk
)

from .cv_indexer import (
    CVIndexer,
    indexer_cvs_automatique,
    indexer_cv_depuis_texte,
    mettre_a_jour_cv,
    supprimer_cv,
    cv_schema
)

from .job_indexer import (
    JobIndexer,
    indexer_offres_automatique,
    job_schema
)

# ✅ CORRECTION: Importer la classe au lieu des fonctions inexistantes
from .query_indexer import (
    QueryIndexSchema,      # ✅ Classe qui existe
    QueryIndexManager,     # ✅ Classe qui existe
    QueryValidator,        # ✅ Classe qui existe
    QueryCorrector,        # ✅ Classe qui existe
    QueryProcessor as QueryIndexProcessor,  # ✅ Renommé pour éviter conflit
    QueryIndexer,          # ✅ Classe principale
    indexer_requete,       # ✅ Fonction qui existe
    prepare_query_for_search,  # ✅ Fonction qui existe
)

__all__ = [
    # Preprocessing
    'pretraiter_texte',
    'pretraiter_competences',
    'nettoyer_texte_brut',
    'compter_tokens',
    'calculer_reduction',
    'init_nltk',
    
    # CV Indexer
    'CVIndexer',
    'indexer_cvs_automatique',
    'indexer_cv_depuis_texte',
    'mettre_a_jour_cv',
    'supprimer_cv',
    'cv_schema',
    
    # Job Indexer
    'JobIndexer',
    'indexer_offres_automatique',
    'job_schema',
    
    # Query Indexer (CORRIGÉ)
    'QueryIndexSchema',
    'QueryIndexManager',
    'QueryValidator',
    'QueryCorrector',
    'QueryIndexProcessor',
    'QueryIndexer',
    'indexer_requete',
    'prepare_query_for_search',
]

__version__ = '1.0.0'
__author__ = 'SmartHire Team'
