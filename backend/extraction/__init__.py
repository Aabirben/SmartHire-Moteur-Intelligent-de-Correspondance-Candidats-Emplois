"""
============================================================================
SMARTHIRE - Extraction Package
Modules pour extraire les données des CV et offres d'emploi
============================================================================
"""

from .pdf_reader import (
    lire_pdf,
    lire_pdf_avec_info,
    valider_pdf,
    compter_pdfs,
    lister_pdfs
)

from .skills_extractor import (
    SkillsDatabase,
    get_skills_database,
    extraire_competences,
    extraire_competences_avec_stats,
    categoriser_competences,
    valider_competence,
    normaliser_competence,
    comparer_competences
)

from .info_extractor import (
    extraire_nom,
    extraire_titre_profil,
    extraire_annees_experience,
    extraire_localisation,
    extraire_resume,
    extraire_description_experience,
    extraire_projets,
    extraire_toutes_infos
)

__all__ = [
    # PDF Reader
    'lire_pdf',
    'lire_pdf_avec_info',
    'valider_pdf',
    'compter_pdfs',
    'lister_pdfs',
    
    # Skills Extractor
    'SkillsDatabase',
    'get_skills_database',
    'extraire_competences',
    'extraire_competences_avec_stats',
    'categoriser_competences',
    'valider_competence',
    'normaliser_competence',
    'comparer_competences',
    
    # Info Extractor
    'extraire_nom',
    'extraire_titre_profil',
    'extraire_annees_experience',
    'extraire_localisation',
    'extraire_resume',
    'extraire_description_experience',
    'extraire_projets',
    'extraire_toutes_infos'
]

__version__ = '1.0.0'
__author__ = 'SmartHire Team'