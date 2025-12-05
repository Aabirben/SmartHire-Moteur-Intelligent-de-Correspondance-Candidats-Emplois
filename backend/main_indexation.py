"""
============================================================================
SMARTHIRE - Main Indexation Script
Script principal pour indexer les CV et les offres d'emploi
Usage:
    python main_indexation.py              # Indexe tout
    python main_indexation.py --cv         # Indexe uniquement les CV
    python main_indexation.py --jobs       # Indexe uniquement les offres
    python main_indexation.py --force      # Recrée les index complètement
============================================================================
"""

import sys
import argparse
from pathlib import Path

# Ajout du répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.utils.logger import setup_logging, get_logger, log_section
from indexation.cv_indexer import indexer_cvs_automatique
from indexation.job_indexer import indexer_offres_automatique
from backend.config.settings import create_directories

logger = get_logger(__name__)

# ========================================================
# FONCTIONS PRINCIPALES
# ========================================================
def indexer_tout(force: bool = False):
    """Indexe les CV et les offres"""
    log_section(logger, "INDEXATION COMPLÈTE DU SYSTÈME SMARTHIRE")
    
    logger.info("🔄 Étape 1/2: Indexation des CV...")
    indexer_cvs_automatique(force=force)
    
    logger.info("\n🔄 Étape 2/2: Indexation des offres d'emploi...")
    indexer_offres_automatique(force=force)
    
    log_section(logger, "✅ INDEXATION COMPLÈTE TERMINÉE")


def afficher_statistiques():
    """Affiche les statistiques des index"""
    from whoosh.index import open_dir, exists_in
    from backend.config.settings import CV_INDEX, JOB_INDEX
    
    log_section(logger, "STATISTIQUES DES INDEX")
    
    # Statistiques CV
    if exists_in(str(CV_INDEX)):
        try:
            ix_cv = open_dir(str(CV_INDEX))
            with ix_cv.searcher() as searcher:
                nb_cv = searcher.doc_count_all()
                logger.info(f"📊 Index CV:")
                logger.info(f"   • Nombre de CV indexés: {nb_cv}")
                logger.info(f"   • Emplacement: {CV_INDEX}")
        except Exception as e:
            logger.error(f"❌ Erreur lecture index CV: {e}")
    else:
        logger.warning(f"⚠️ Index CV introuvable: {CV_INDEX}")
    
    # Statistiques Offres
    if exists_in(str(JOB_INDEX)):
        try:
            ix_job = open_dir(str(JOB_INDEX))
            with ix_job.searcher() as searcher:
                nb_jobs = searcher.doc_count_all()
                logger.info(f"\n📊 Index Offres:")
                logger.info(f"   • Nombre d'offres indexées: {nb_jobs}")
                logger.info(f"   • Emplacement: {JOB_INDEX}")
        except Exception as e:
            logger.error(f"❌ Erreur lecture index offres: {e}")
    else:
        logger.warning(f"⚠️ Index offres introuvable: {JOB_INDEX}")
    
    logger.info("\n" + "="*80)


# ========================================================
# INTERFACE EN LIGNE DE COMMANDE
# ========================================================
def parse_arguments():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(
        description="SmartHire - Système d'indexation automatique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main_indexation.py              # Indexe tout (CV + offres)
  python main_indexation.py --cv         # Indexe uniquement les CV
  python main_indexation.py --jobs       # Indexe uniquement les offres
  python main_indexation.py --force      # Recrée complètement les index
  python main_indexation.py --stats      # Affiche les statistiques
  python main_indexation.py --cv --force # Recrée l'index des CV uniquement
        """
    )
    
    parser.add_argument(
        '--cv',
        action='store_true',
        help='Indexe uniquement les CV'
    )
    
    parser.add_argument(
        '--jobs',
        action='store_true',
        help='Indexe uniquement les offres d\'emploi'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force la recréation complète des index'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Affiche les statistiques des index'
    )
    
    return parser.parse_args()


# ========================================================
# POINT D'ENTRÉE PRINCIPAL
# ========================================================
def main():
    """Point d'entrée principal du script"""
    # Configuration du logging
    setup_logging(log_file=True, console=True)
    
    # Création des dossiers nécessaires
    create_directories()
    
    # Parse des arguments
    args = parse_arguments()
    
    # Affichage des statistiques uniquement
    if args.stats:
        afficher_statistiques()
        return
    
    # Détermination de ce qu'il faut indexer
    indexer_cv = args.cv or (not args.cv and not args.jobs)
    indexer_job = args.jobs or (not args.cv and not args.jobs)
    
    # Indexation
    try:
        if indexer_cv and indexer_job:
            # Indexation complète
            indexer_tout(force=args.force)
        elif indexer_cv:
            # CV uniquement
            log_section(logger, "INDEXATION DES CV UNIQUEMENT")
            indexer_cvs_automatique(force=args.force)
        elif indexer_job:
            # Offres uniquement
            log_section(logger, "INDEXATION DES OFFRES UNIQUEMENT")
            indexer_offres_automatique(force=args.force)
        
        # Affichage des statistiques finales
        logger.info("\n")
        afficher_statistiques()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Indexation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()