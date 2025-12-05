"""
============================================================================
SMARTHIRE - CV Indexer Module (FIXED)
Indexation automatique des CV avec preprocessing NLP
============================================================================
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.writing import AsyncWriter

from backend.config.settings import CV_FOLDER, CV_INDEX
from backend.extraction.pdf_reader import lire_pdf
from backend.extraction.skills_extractor import extraire_competences, get_skills_database
from backend.extraction.info_extractor import extraire_toutes_infos
from backend.indexation.preprocessing import (
    pretraiter_texte,
    pretraiter_competences,
    nettoyer_texte_brut
)

logger = logging.getLogger(__name__)

# ========================================================
# UTILITIES - Token Management & Validation
# ========================================================

def compter_tokens(text: str) -> int:
    """
    Compte le nombre de tokens dans un texte.
    Simple approximation: divise par espaces et ponctuation.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Nombre approximatif de tokens
    """
    if not text or not isinstance(text, str):
        return 0
    
    import re
    # Divise sur les espaces et ponctuation
    tokens = re.findall(r'\b\w+\b', text.lower())
    return len(tokens)


def calculer_reduction(tokens_original: int, tokens_processed: int) -> float:
    """
    Calcule le pourcentage de réduction de tokens après preprocessing.
    
    Args:
        tokens_original: Nombre de tokens avant preprocessing
        tokens_processed: Nombre de tokens après preprocessing
        
    Returns:
        Pourcentage de réduction (0.0 à 100.0)
    """
    if tokens_original == 0:
        return 0.0
    
    reduction = ((tokens_original - tokens_processed) / tokens_original) * 100
    return max(0.0, min(100.0, reduction))  # Clamp entre 0 et 100


def valider_cv_id(cv_id: any) -> Tuple[bool, str]:
    """
    Valide que cv_id est présent et non vide.
    
    Args:
        cv_id: L'ID à valider
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not cv_id:
        return False, "cv_id manquant ou vide"
    
    cv_id_str = str(cv_id).strip()
    if not cv_id_str:
        return False, "cv_id ne peut pas être vide après conversion en chaîne"
    
    return True, ""


def valider_texte_cv(texte: str) -> Tuple[bool, str]:
    """
    Valide que le texte du CV est valide.
    
    Args:
        texte: Texte du CV
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not texte or not isinstance(texte, str):
        return False, "Texte du CV manquant ou invalide"
    
    texte_clean = texte.strip()
    if not texte_clean:
        return False, "Texte du CV vide"
    
    # Vérifier longueur minimale (au moins 100 caractères)
    if len(texte_clean) < 100:
        return False, "Texte du CV trop court (minimum 100 caractères)"
    
    return True, ""


# ========================================================
# SCHÉMA D'INDEXATION CV (avec champs additionnels)
# ========================================================
cv_schema = Schema(
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
    
    # Champs pour l'upload en temps réel
    original_filename=TEXT(stored=True),
    user_id=ID(stored=True),
    
    # Statistiques NLP
    nb_tokens_original=NUMERIC(stored=True),
    nb_tokens_processed=NUMERIC(stored=True)
)

# ========================================================
# CLASSE D'INDEXATION
# ========================================================
class CVIndexer:
    """Classe pour indexer les CV avec preprocessing NLP"""
    
    def __init__(self, cv_folder: Path = CV_FOLDER, index_dir: Path = CV_INDEX):
        self.cv_folder = cv_folder
        self.index_dir = index_dir
        self.skills_db = get_skills_database()
        
        # Statistiques
        self.total_cvs = 0
        self.success_count = 0
        self.error_count = 0
    
    def _creer_index(self, force: bool = False):
        """Crée ou recrée l'index"""
        if self.index_dir.exists() and force:
            shutil.rmtree(self.index_dir)
            logger.info(f"✅ Ancien index supprimé: {self.index_dir}")
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if not exists_in(str(self.index_dir)):
            create_in(str(self.index_dir), cv_schema)
            logger.info(f"✅ Nouvel index créé: {self.index_dir}")
    
    def _traiter_cv(self, filepath: Path) -> Optional[dict]:
        """
        Traite un CV et extrait toutes les informations
        
        Returns:
            Dictionnaire avec toutes les données ou None en cas d'erreur
        """
        try:
            # 1️⃣ Extraction du texte brut
            texte_brut = lire_pdf(filepath)
            
            if not texte_brut:
                logger.warning(f"⚠️ CV vide ou illisible: {filepath.name}")
                return None
            
            # 2️⃣ Nettoyage léger du texte brut
            texte_nettoye = nettoyer_texte_brut(texte_brut)
            
            # 3️⃣ Prétraitement NLP complet
            skills_set = self.skills_db.get_skills_set()
            texte_pretraite, tokens = pretraiter_texte(
                texte_nettoye,
                preserve_skills=True,
                skills_list=skills_set
            )
            
            # 4️⃣ Extraction des informations (sur texte nettoyé)
            infos = extraire_toutes_infos(texte_nettoye)
            
            # 5️⃣ Extraction des compétences
            competences = extraire_competences(texte_nettoye, priorite_section_skills=True)
            competences_str = pretraiter_competences(competences)
            
            # 6️⃣ Statistiques NLP - FIXED: utilise la fonction locale
            nb_tokens_original = compter_tokens(texte_nettoye)
            nb_tokens_processed = len(tokens)
            
            return {
                'doc_id': filepath.name,
                'nom': infos.get('nom', 'Inconnu'),
                'titre_profil': infos.get('titre_profil', 'Professional'),
                'localisation': infos.get('localisation', ''),
                'annees': infos.get('annees_experience', 0),
                'description_experience': infos.get('description_experience', ''),
                'competences': competences_str,
                'competences_list': competences,
                'projets': infos.get('projets', ''),
                'resume_complet': infos.get('resume', ''),
                'texte_pretraite': texte_pretraite,
                'original_filename': filepath.name,
                'user_id': "",  # Vide pour indexation batch
                'nb_tokens_original': nb_tokens_original,
                'nb_tokens_processed': nb_tokens_processed
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filepath.name}: {e}")
            return None
    
    def indexer_tous_les_cvs(self, force: bool = False):
        """
        Indexe tous les CV du dossier
        
        Args:
            force: Si True, recrée l'index complètement
        """
        logger.info("="*120)
        logger.info("DÉBUT DE L'INDEXATION AUTOMATIQUE DES CV")
        logger.info("="*120)
        
        # Création de l'index
        self._creer_index(force=force)
        
        # Récupération des fichiers PDF
        try:
            cv_files = sorted(self.cv_folder.glob("*.pdf"))
            self.total_cvs = len(cv_files)
            
            if self.total_cvs == 0:
                logger.warning(f"⚠️ Aucun CV trouvé dans {self.cv_folder}")
                return
            
            logger.info(f"📁 {self.total_cvs} CV trouvés dans {self.cv_folder}\n")
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture dossier: {e}")
            return
        
        # Ouverture de l'index pour écriture
        ix = open_dir(str(self.index_dir))
        writer = AsyncWriter(ix)
        
        # Traitement de chaque CV
        for i, filepath in enumerate(cv_files, 1):
            try:
                # Traitement du CV
                cv_data = self._traiter_cv(filepath)
                
                if cv_data is None:
                    self.error_count += 1
                    continue
                
                # Indexation
                writer.add_document(
                    doc_id=cv_data['doc_id'],
                    nom=cv_data['nom'],
                    titre_profil=cv_data['titre_profil'],
                    localisation=cv_data['localisation'],
                    annees=cv_data['annees'],
                    description_experience=cv_data['description_experience'],
                    competences=cv_data['competences'],
                    projets=cv_data['projets'],
                    resume_complet=cv_data['resume_complet'],
                    texte_pretraite=cv_data['texte_pretraite'],
                    original_filename=cv_data['original_filename'],
                    user_id=cv_data['user_id'],
                    nb_tokens_original=cv_data['nb_tokens_original'],
                    nb_tokens_processed=cv_data['nb_tokens_processed']
                )
                
                # Affichage du résumé
                self._afficher_resume_cv(i, cv_data)
                
                self.success_count += 1
                
            except Exception as e:
                logger.error(f"{i:02d}/{self.total_cvs} → ❌ ERREUR: {filepath.name} - {e}")
                self.error_count += 1
                continue
        
        # Commit des changements
        try:
            writer.commit()
            self._afficher_statistiques_finales()
        except Exception as e:
            logger.error(f"❌ Erreur lors du commit: {e}")
    
    def _afficher_resume_cv(self, index: int, cv_data: dict):
        """Affiche un résumé formaté du CV indexé"""
        # Preview des compétences
        skills_list = cv_data['competences_list']
        skills_preview = ", ".join(skills_list[:5])
        if len(skills_list) > 5:
            skills_preview += f" (+ {len(skills_list) - 5} autres)"
        
        # Nombre de projets
        projets = cv_data['projets']
        nb_projets = len([p for p in projets.split("|") if p.strip()]) if projets else 0
        
        # Réduction tokens
        reduction = calculer_reduction(
            cv_data['nb_tokens_original'],
            cv_data['nb_tokens_processed']
        )
        
        # Preview des tokens
        tokens_preview = " ".join(cv_data['texte_pretraite'].split()[:10]) + "..."
        
        print(f"\n{index:02d}/{self.total_cvs} {'='*100}")
        print(f"  👤 NOM:              {cv_data['nom']}")
        print(f"  💼 TITRE:            {cv_data['titre_profil']}")
        print(f"  📍 LOCALISATION:     {cv_data['localisation']}")
        print(f"  📅 EXPÉRIENCE:       {cv_data['annees']} ans")
        print(f"  🛠️  COMPÉTENCES:      {len(skills_list)} skills → {skills_preview}")
        print(f"  📌 PROJETS:          {nb_projets} projets")
        print(f"  🔤 TOKENS NLP:       {cv_data['nb_tokens_original']} → {cv_data['nb_tokens_processed']} (-{reduction:.1f}%)")
        print(f"  📝 PREVIEW:          {tokens_preview}")
    
    def _afficher_statistiques_finales(self):
        """Affiche les statistiques finales de l'indexation"""
        logger.info("\n" + "="*120)
        logger.info("✅ INDEXATION AUTOMATIQUE TERMINÉE AVEC SUCCÈS")
        logger.info("="*120)
        logger.info(f"\n📊 Résumé:")
        logger.info(f"   • CV indexés avec succès: {self.success_count}")
        logger.info(f"   • CV en erreur: {self.error_count}")
        logger.info(f"   • Total traité: {self.total_cvs}")
        logger.info(f"   • Taux de succès: {(self.success_count/self.total_cvs*100):.1f}%")
        logger.info(f"\n📁 Index sauvegardé: {self.index_dir}")
        logger.info(f"\n🔍 Pipeline NLP appliqué:")
        logger.info(f"   ✓ Extraction PDF")
        logger.info(f"   ✓ Nettoyage du texte")
        logger.info(f"   ✓ Minuscules")
        logger.info(f"   ✓ Suppression ponctuation")
        logger.info(f"   ✓ Tokenisation (NLTK)")
        logger.info(f"   ✓ Suppression stopwords (EN + FR)")
        logger.info(f"   ✓ Lemmatisation (WordNet)")
        logger.info(f"   ✓ Préservation des compétences techniques")


# ========================================================
# FONCTION PRINCIPALE
# ========================================================
def indexer_cvs_automatique(force: bool = False):
    """
    Point d'entrée principal pour l'indexation automatique
    
    Args:
        force: Si True, recrée l'index complètement
    """
    indexer = CVIndexer()
    indexer.indexer_tous_les_cvs(force=force)


# ========================================================
# INDEXATION EN TEMPS RÉEL (UPLOAD) - FIXED
# ========================================================
def indexer_cv_depuis_texte(
    cv_id: str,
    texte: str,
    filename: str = "",
    user_id: str = ""
) -> bool:
    """
    Indexe un CV en temps réel après upload
    
    FIXED:
    - Validation robuste de cv_id et texte
    - Gestion des doublons (suppression avant ajout)
    - Gestion d'erreurs complète
    
    Args:
        cv_id: ID du CV dans PostgreSQL (devient doc_id dans Whoosh)
        texte: Contenu texte du CV
        filename: Nom du fichier original
        user_id: ID de l'utilisateur propriétaire
        
    Returns:
        True si succès, False sinon
    """
    # FIXED: Validations robustes
    is_valid_id, error_msg_id = valider_cv_id(cv_id)
    if not is_valid_id:
        logger.error(f"❌ Validation cv_id échouée: {error_msg_id}")
        return False
    
    is_valid_texte, error_msg_texte = valider_texte_cv(texte)
    if not is_valid_texte:
        logger.error(f"❌ Validation texte échouée: {error_msg_texte}")
        return False
    
    cv_id_str = str(cv_id).strip()
    
    try:
        # Vérification que l'index existe
        if not exists_in(str(CV_INDEX)):
            logger.error(f"❌ Index introuvable: {CV_INDEX}")
            logger.error(f"💡 Lancez d'abord: python -m backend.indexation.cv_indexer")
            return False
        
        # Nettoyage + NLP
        texte_net = nettoyer_texte_brut(texte)
        
        # Prétraitement avec préservation des skills
        skills_db = get_skills_database()
        skills_set = skills_db.get_skills_set()
        texte_pretraite, tokens = pretraiter_texte(
            texte_net,
            preserve_skills=True,
            skills_list=skills_set
        )
        
        # Extraction des informations
        infos = extraire_toutes_infos(texte_net)
        competences = extraire_competences(texte_net, priorite_section_skills=True)
        competences_str = pretraiter_competences(competences)
        
        # Statistiques - FIXED: utilise les fonctions locales
        nb_tokens_original = compter_tokens(texte_net)
        nb_tokens_processed = len(tokens)
        
        # FIXED: Suppression du doublon si existant
        ix = open_dir(str(CV_INDEX))
        
        try:
            with ix.searcher() as searcher:
                from whoosh.qparser import QueryParser
                query_parser = QueryParser("doc_id", ix.schema)
                query = query_parser.parse(cv_id_str)
                results = searcher.search(query)
                
                if len(results) > 0:
                    logger.info(f"⚠️ CV #{cv_id_str} existe déjà. Suppression avant réindexation.")
                    
                    # Suppression via AsyncWriter
                    with ix.writer() as writer:
                        writer.delete_by_term("doc_id", cv_id_str)
        except Exception as e:
            logger.warning(f"⚠️ Vérification doublon échouée: {e}. Continuant l'indexation...")
        
        # Indexation Whoosh (nouveau writer après suppression)
        writer = AsyncWriter(ix)
        
        try:
            writer.add_document(
                doc_id=cv_id_str,
                nom=infos.get('nom', 'Inconnu'),
                titre_profil=infos.get('titre_profil', 'Professional'),
                localisation=infos.get('localisation', ''),
                annees=infos.get('annees_experience', 0),
                description_experience=infos.get('description_experience', ''),
                competences=competences_str,
                projets=infos.get('projets', ''),
                resume_complet=infos.get('resume', ''),
                texte_pretraite=texte_pretraite,
                original_filename=filename or f"cv_upload_{cv_id_str}.pdf",
                user_id=str(user_id),
                nb_tokens_original=nb_tokens_original,
                nb_tokens_processed=nb_tokens_processed
            )
            
            writer.commit()
            
            logger.info(f"✅ CV #{cv_id_str} indexé en temps réel par l'utilisateur {user_id}")
            logger.info(f"   • Nom: {infos.get('nom', 'Inconnu')}")
            logger.info(f"   • Compétences: {len(competences)} skills")
            logger.info(f"   • Tokens: {nb_tokens_original} → {nb_tokens_processed}")
            
            return True
        
        except Exception as e:
            writer.cancel()
            logger.error(f"❌ Erreur lors de l'ajout du document CV #{cv_id_str}: {e}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Échec indexation CV #{cv_id_str}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================================================
# MISE À JOUR D'UN CV EXISTANT - FIXED
# ========================================================
def mettre_a_jour_cv(cv_id: str, texte: str, filename: str = "", user_id: str = "") -> bool:
    """
    Met à jour un CV existant dans l'index
    
    FIXED:
    - Validations robustes
    - Suppression atomique + réindexation
    
    Args:
        cv_id: ID du CV
        texte: Nouveau contenu
        filename: Nouveau nom de fichier
        user_id: ID utilisateur
        
    Returns:
        True si succès
    """
    is_valid_id, error_msg = valider_cv_id(cv_id)
    if not is_valid_id:
        logger.error(f"❌ Validation cv_id échouée: {error_msg}")
        return False
    
    try:
        if not exists_in(str(CV_INDEX)):
            logger.error(f"❌ Index introuvable: {CV_INDEX}")
            return False
        
        cv_id_str = str(cv_id).strip()
        
        ix = open_dir(str(CV_INDEX))
        writer = ix.writer()
        
        # Supprimer l'ancien document
        deleted = writer.delete_by_term('doc_id', cv_id_str)
        writer.commit()
        
        logger.info(f"✅ Ancien CV #{cv_id_str} supprimé ({deleted} document(s))")
        
        # Réindexer avec les nouvelles données
        return indexer_cv_depuis_texte(cv_id, texte, filename, user_id)
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour CV #{cv_id}: {e}")
        return False


# ========================================================
# SUPPRESSION D'UN CV - FIXED
# ========================================================
def supprimer_cv(cv_id: str) -> bool:
    """
    Supprime un CV de l'index
    
    FIXED:
    - Validation robuste de cv_id
    
    Args:
        cv_id: ID du CV à supprimer
        
    Returns:
        True si succès
    """
    is_valid_id, error_msg = valider_cv_id(cv_id)
    if not is_valid_id:
        logger.error(f"❌ Validation cv_id échouée: {error_msg}")
        return False
    
    try:
        if not exists_in(str(CV_INDEX)):
            logger.error(f"❌ Index introuvable: {CV_INDEX}")
            return False
        
        cv_id_str = str(cv_id).strip()
        
        ix = open_dir(str(CV_INDEX))
        writer = ix.writer()
        
        # Supprimer le document
        deleted = writer.delete_by_term('doc_id', cv_id_str)
        writer.commit()
        
        logger.info(f"✅ CV #{cv_id_str} supprimé de l'index ({deleted} document(s))")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur suppression CV #{cv_id}: {e}")
        return False


if __name__ == "__main__":
    import sys
    from backend.utils.logger import setup_logging
    
    # Configuration du logging
    setup_logging()
    
    # Indexation automatique
    force_recreate = "--force" in sys.argv
    
    if force_recreate:
        logger.info("🔄 Mode FORCE: L'index sera complètement recréé")
    
    indexer_cvs_automatique(force=force_recreate)