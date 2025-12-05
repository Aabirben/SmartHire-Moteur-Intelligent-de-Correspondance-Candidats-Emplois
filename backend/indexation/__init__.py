"""
============================================================================
SMARTHIRE - Indexation Package
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

from .query_indexer import (
    get_query_schema,
    init_query_index,
    pretraiter_requete_avec_bool,
    pretraiter_requete_simple,
    detect_search_mode,
    indexer_requete,
    rechercher_historique,
    statistiques_filtres,
    tendances_recherches,
    filtres_combines_populaires,
    statistiques_globales,
    nettoyer_requetes_anciennes
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
    
    # Query Indexer
    'get_query_schema',
    'init_query_index',
    'pretraiter_requete_avec_bool',
    'pretraiter_requete_simple',
    'detect_search_mode',
    'indexer_requete',
    'rechercher_historique',
    'statistiques_filtres',
    'tendances_recherches',
    'filtres_combines_populaires',
    'statistiques_globales',
    'nettoyer_requetes_anciennes'
]

__version__ = '1.0.0'
__author__ = 'SmartHire Team'