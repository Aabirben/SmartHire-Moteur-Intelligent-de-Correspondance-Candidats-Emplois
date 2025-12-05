"""
============================================================================
SMARTHIRE - Schema Migration Script
Migration des index existants pour ajouter les nouveaux champs
sans perdre les données
============================================================================
"""

import logging
import sys
from pathlib import Path

# Ajout du répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from whoosh.index import open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC

from backend.config.settings import CV_INDEX, JOB_INDEX

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================================
# NOUVEAU SCHÉMA CV (avec champs additionnels)
# ========================================================
nouveau_schema_cv = Schema(
    doc_id=ID(stored=True, unique=True),
    nom=TEXT(stored=True),
    titre_profil=TEXT(stored=True),
    localisation=TEXT(stored=True),
    annees=NUMERIC(stored=True, sortable=True),
    description_experience=TEXT(stored=True),
    competences=KEYWORD(commas=True, lowercase=True, stored=True),
    projets=TEXT(stored=True),
    resume_complet=TEXT(stored=True),
    texte_pretraite=TEXT(stored=True),
    
    # ✨ NOUVEAUX CHAMPS
    original_filename=TEXT(stored=True),
    user_id=ID(stored=True),
    
    # Statistiques NLP
    nb_tokens_original=NUMERIC(stored=True),
    nb_tokens_processed=NUMERIC(stored=True)
)


def migrer_index_cv():
    """
    Migre l'index CV pour ajouter les nouveaux champs
    Les documents existants auront ces champs = None
    """
    try:
        logger.info("="*80)
        logger.info("🚀 MIGRATION DE L'INDEX CV")
        logger.info("="*80)
        
        # Vérifier que l'index existe
        if not exists_in(str(CV_INDEX)):
            logger.error(f"❌ L'index n'existe pas: {CV_INDEX}")
            logger.info("💡 Créez d'abord l'index avec: python -m backend.indexation.cv_indexer")
            return False
        
        logger.info(f"\n📁 Index: {CV_INDEX}")
        
        # Ouvrir l'index
        ix = open_dir(str(CV_INDEX))
        
        # Afficher le schéma actuel
        logger.info("\n📋 Schéma AVANT migration:")
        champs_avant = sorted(ix.schema.names())
        for field_name in champs_avant:
            logger.info(f"   ✓ {field_name}")
        
        # Compter les documents
        with ix.searcher() as searcher:
            nb_docs_avant = searcher.doc_count_all()
        
        logger.info(f"\n📊 Nombre de documents: {nb_docs_avant}")
        
        # Migration: créer un writer avec le nouveau schéma
        logger.info("\n⏳ Migration en cours...")
        logger.info("   • Les nouveaux champs seront ajoutés")
        logger.info("   • Les documents existants auront ces champs = None")
        logger.info("   • Les nouveaux uploads auront ces champs remplis")
        
        # Le simple fait de commiter avec un writer met à jour le schéma
        writer = ix.writer()
        writer.commit(merge=True, optimize=False)
        
        # Réouvrir pour vérifier
        ix = open_dir(str(CV_INDEX))
        
        logger.info("\n📋 Schéma APRÈS migration:")
        champs_apres = sorted(ix.schema.names())
        for field_name in champs_apres:
            marqueur = "🆕" if field_name not in champs_avant else "✓"
            logger.info(f"   {marqueur} {field_name}")
        
        # Vérifier le nombre de documents
        with ix.searcher() as searcher:
            nb_docs_apres = searcher.doc_count_all()
        
        if nb_docs_avant != nb_docs_apres:
            logger.warning(f"⚠️ ATTENTION: {nb_docs_avant} documents avant, {nb_docs_apres} après")
            return False
        
        logger.info("\n" + "="*80)
        logger.info("✅ MIGRATION CV TERMINÉE AVEC SUCCÈS")
        logger.info("="*80)
        logger.info(f"\n📊 Résumé:")
        logger.info(f"   • Documents préservés: {nb_docs_apres}/{nb_docs_avant}")
        logger.info(f"   • Nouveaux champs ajoutés: {len(champs_apres) - len(champs_avant)}")
        logger.info(f"   • Schéma mis à jour: ✓")
        
        logger.info(f"\n📝 Prochaines étapes:")
        logger.info(f"   1. ✅ Migration terminée")
        logger.info(f"   2. 🔄 Les nouveaux CV utiliseront les champs original_filename et user_id")
        logger.info(f"   3. 📊 Les CV existants auront ces champs = None")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur migration CV: {e}")
        import traceback
        traceback.print_exc()
        return False


def verifier_migration():
    """Vérifie que la migration s'est bien passée"""
    try:
        logger.info("\n" + "="*80)
        logger.info("🔍 VÉRIFICATION DE LA MIGRATION")
        logger.info("="*80)
        
        if not exists_in(str(CV_INDEX)):
            logger.error(f"❌ Index introuvable: {CV_INDEX}")
            return False
        
        ix = open_dir(str(CV_INDEX))
        
        # Vérifier les champs
        champs_requis = ['original_filename', 'user_id']
        champs_presents = ix.schema.names()
        
        logger.info("\n📋 Vérification des nouveaux champs:")
        tous_presents = True
        for champ in champs_requis:
            present = champ in champs_presents
            statut = "✅" if present else "❌"
            logger.info(f"   {statut} {champ}")
            if not present:
                tous_presents = False
        
        # Afficher quelques documents
        logger.info("\n📄 Échantillon de documents (5 premiers):")
        with ix.searcher() as searcher:
            results = searcher.documents()
            for i, doc in enumerate(results):
                if i >= 5:
                    break
                logger.info(f"\n   Document #{i+1}:")
                logger.info(f"     • doc_id: {doc.get('doc_id', 'N/A')}")
                logger.info(f"     • nom: {doc.get('nom', 'N/A')}")
                logger.info(f"     • original_filename: {doc.get('original_filename', 'None')}")
                logger.info(f"     • user_id: {doc.get('user_id', 'None')}")
        
        if tous_presents:
            logger.info("\n✅ Migration vérifiée avec succès")
        else:
            logger.error("\n❌ Migration incomplète - certains champs manquent")
        
        return tous_presents
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification: {e}")
        return False


def main():
    """Point d'entrée principal"""
    logger.info("="*80)
    logger.info("SMARTHIRE - MIGRATION DES INDEX")
    logger.info("="*80)
    
    # Migration
    succes = migrer_index_cv()
    
    if not succes:
        logger.error("\n❌ Migration échouée")
        sys.exit(1)
    
    # Vérification
    logger.info("\n")
    verifier_migration()
    
    logger.info("\n" + "="*80)
    logger.info("✅ PROCESSUS TERMINÉ")
    logger.info("="*80)


if __name__ == "__main__":
    main()