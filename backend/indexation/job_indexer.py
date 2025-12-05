"""
============================================================================
SMARTHIRE - Job Indexer Module (FIXED)
Indexation automatique des offres d'emploi avec preprocessing NLP
============================================================================
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.writing import AsyncWriter

from backend.config.settings import JOB_FOLDER, JOB_INDEX, NIVEAU_MAPPING
from backend.extraction.skills_extractor import get_skills_database
from backend.indexation.preprocessing import (
    pretraiter_texte,
    pretraiter_competences
)

logger = logging.getLogger(__name__)

# ========================================================
# UTILITIES - Token Management
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


def extraire_localisation(job_json: dict) -> str:
    """
    Extrait la localisation de manière robuste à partir des données JSON.
    Essaie plusieurs chemins pour la trouver.
    
    Args:
        job_json: Dictionnaire JSON de l'offre
        
    Returns:
        Localisation extraite ou chaîne vide
    """
    # Chemin 1: localisation directe
    localisation = job_json.get("location", "").strip()
    if localisation:
        return localisation
    
    # Chemin 2: depuis l'objet company
    company = job_json.get("company", {})
    
    if isinstance(company, dict):
        # Essayer city d'abord
        city = company.get("city", "").strip()
        if city:
            # Ajouter le pays si disponible
            country = company.get("country", "").strip()
            return f"{city}, {country}" if country else city
        
        # Fallback: location depuis company
        loc = company.get("location", "").strip()
        if loc:
            return loc
    
    elif isinstance(company, str):
        # Si company est directement une chaîne, l'utiliser comme location
        return company.strip()
    
    return ""


def valider_job_id(job_id: any) -> Tuple[bool, str]:
    """
    Valide que job_id est présent et non vide.
    
    Args:
        job_id: L'ID à valider
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not job_id:
        return False, "job_id manquant ou vide"
    
    job_id_str = str(job_id).strip()
    if not job_id_str:
        return False, "job_id ne peut pas être vide après conversion en chaîne"
    
    return True, ""


# ========================================================
# SCHÉMA D'INDEXATION OFFRES
# ========================================================
job_schema = Schema(
    job_id=ID(stored=True, unique=True),
    titre_poste=TEXT(stored=True, field_boost=2.0),
    description=TEXT(stored=True),
    titre_poste_processed=TEXT(stored=True),
    description_processed=TEXT(stored=True),
    competences_requises=KEYWORD(commas=True, lowercase=True, stored=True, field_boost=1.5),
    localisation=TEXT(stored=True),
    niveau_souhaite=ID(stored=True),
    domaine=ID(stored=True),
    annees_min=NUMERIC(stored=True),
    annees_max=NUMERIC(stored=True),
    entreprise=TEXT(stored=True),
    type_contrat=TEXT(stored=True),
    mode_travail=TEXT(stored=True),
    
    # Statistiques NLP
    nb_tokens_original=NUMERIC(stored=True),
    nb_tokens_processed=NUMERIC(stored=True)
)

# ========================================================
# CLASSE D'INDEXATION
# ========================================================
class JobIndexer:
    """Classe pour indexer les offres d'emploi avec preprocessing NLP"""
    
    def __init__(self, job_folder: Path = JOB_FOLDER, index_dir: Path = JOB_INDEX):
        self.job_folder = job_folder
        self.index_dir = index_dir
        self.skills_db = get_skills_database()
        
        # Statistiques
        self.total_jobs = 0
        self.success_count = 0
        self.error_count = 0
    
    def _creer_index(self, force: bool = False):
        """Crée ou recrée l'index"""
        if self.index_dir.exists() and force:
            shutil.rmtree(self.index_dir)
            logger.info(f"✅ Ancien index supprimé: {self.index_dir}")
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if not exists_in(str(self.index_dir)):
            create_in(str(self.index_dir), job_schema)
            logger.info(f"✅ Nouvel index créé: {self.index_dir}")
    
    def _charger_json(self, filepath: Path) -> Optional[dict]:
        """Charge un fichier JSON d'offre"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur JSON dans {filepath.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lecture {filepath.name}: {e}")
            return None
    
    def _extraire_donnees_offre(self, job_json: dict) -> Optional[dict]:
        """
        Extrait et structure les données d'une offre avec preprocessing
        
        Returns:
            Dictionnaire avec toutes les données ou None en cas d'erreur
        """
        try:
            # 1️⃣ Extraction des champs de base
            job_id = job_json.get("job_id", "")
            titre_poste = job_json.get("title", "")
            
            # 2️⃣ Description complète
            description_text = job_json.get("description", "")
            responsibilities = job_json.get("responsibilities", [])
            if responsibilities:
                description_text += " " + " ".join(responsibilities)
            
            # 3️⃣ Compétences requises
            required_skills = job_json.get("required_skills", [])
            preferred_skills = job_json.get("preferred_skills", [])
            all_skills = required_skills + preferred_skills
            competences_list = [skill.lower() for skill in all_skills]
            competences_str = pretraiter_competences(competences_list)
            
            # 4️⃣ Prétraitement NLP
            skills_set = self.skills_db.get_skills_set()
            
            titre_processed, _ = pretraiter_texte(
                titre_poste,
                preserve_skills=True,
                skills_list=skills_set
            )
            
            description_processed, _ = pretraiter_texte(
                description_text,
                preserve_skills=True,
                skills_list=skills_set
            )
            
            # 5️⃣ Statistiques NLP - FIXED: utilise la fonction locale
            nb_tokens_original = compter_tokens(titre_poste + " " + description_text)
            nb_tokens_processed = compter_tokens(titre_processed + " " + description_processed)
            
            # 6️⃣ Autres champs - FIXED: utilise la fonction robuste d'extraction
            localisation = extraire_localisation(job_json)
            
            niveau_souhaite = job_json.get("experience_level", "Mid-Level")
            annees_min, annees_max = NIVEAU_MAPPING.get(niveau_souhaite, (0, 5))
            
            domaine = job_json.get("domain", "").lower()
            
            entreprise = ""
            company = job_json.get("company", {})
            if isinstance(company, dict):
                entreprise = company.get("name", "")
            elif isinstance(company, str):
                entreprise = company
            
            type_contrat = job_json.get("contract_type", "")
            mode_travail = job_json.get("work_mode", "")
            
            return {
                'job_id': job_id,
                'titre_poste': titre_poste,
                'description': description_text,
                'titre_poste_processed': titre_processed,
                'description_processed': description_processed,
                'competences_requises': competences_str,
                'competences_list': competences_list,
                'localisation': localisation,
                'niveau_souhaite': niveau_souhaite,
                'domaine': domaine,
                'annees_min': annees_min,
                'annees_max': annees_max,
                'entreprise': entreprise,
                'type_contrat': type_contrat,
                'mode_travail': mode_travail,
                'nb_tokens_original': nb_tokens_original,
                'nb_tokens_processed': nb_tokens_processed
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction données: {e}")
            return None
    
  
        # Récupération des fichiers JSON
        try:
            json_files = sorted([
                f for f in self.job_folder.glob("*.json")
                if f.name != "all_jobs.json"  # Exclure le fichier agrégé
            ])
            
            self.total_jobs = len(json_files)
            
            if self.total_jobs == 0:
                logger.warning(f"⚠️ Aucune offre trouvée dans {self.job_folder}")
                return
            
            logger.info(f"📁 {self.total_jobs} offres trouvées dans {self.job_folder}\n")
            
        except Exception as e:
            logger.error(f"❌ Erreur lecture dossier: {e}")
            return
        
        # Ouverture de l'index pour écriture
        ix = open_dir(str(self.index_dir))
        writer = AsyncWriter(ix)
        
        # Traitement de chaque offre
        for i, filepath in enumerate(json_files, 1):
            try:
                # Chargement du JSON
                job_json = self._charger_json(filepath)
                
                if job_json is None:
                    self.error_count += 1
                    continue
                
                # Extraction des données
                job_data = self._extraire_donnees_offre(job_json)
                
                if job_data is None:
                    self.error_count += 1
                    continue
                
                # Indexation
                writer.add_document(
                    job_id=job_data['job_id'],
                    titre_poste=job_data['titre_poste'],
                    description=job_data['description'],
                    titre_poste_processed=job_data['titre_poste_processed'],
                    description_processed=job_data['description_processed'],
                    competences_requises=job_data['competences_requises'],
                    localisation=job_data['localisation'],
                    niveau_souhaite=job_data['niveau_souhaite'],
                    domaine=job_data['domaine'],
                    annees_min=job_data['annees_min'],
                    annees_max=job_data['annees_max'],
                    entreprise=job_data['entreprise'],
                    type_contrat=job_data['type_contrat'],
                    mode_travail=job_data['mode_travail'],
                    nb_tokens_original=job_data['nb_tokens_original'],
                    nb_tokens_processed=job_data['nb_tokens_processed']
                )
                
                # Affichage du résumé
                self._afficher_resume_offre(i, job_data)
                
                self.success_count += 1
                
            except Exception as e:
                logger.error(f"{i:02d}/{self.total_jobs} → ❌ ERREUR: {filepath.name} - {e}")
                self.error_count += 1
                continue
        
        # Commit des changements
        try:
            writer.commit()
            self._afficher_statistiques_finales()
        except Exception as e:
            logger.error(f"❌ Erreur lors du commit: {e}")
    
    def _afficher_resume_offre(self, index: int, job_data: dict):
        """Affiche un résumé formaté de l'offre indexée"""
        # Preview des compétences
        skills_list = job_data['competences_list']
        skills_preview = ", ".join(skills_list[:5])
        if len(skills_list) > 5:
            skills_preview += f" (+ {len(skills_list) - 5} autres)"
        
        # Réduction tokens
        reduction = calculer_reduction(
            job_data['nb_tokens_original'],
            job_data['nb_tokens_processed']
        )
        
        # Preview du titre processed
        titre_preview = job_data['titre_poste_processed'][:80]
        if len(job_data['titre_poste_processed']) > 80:
            titre_preview += "..."
        
        print(f"\n{index:02d}/{self.total_jobs} {'='*100}")
        print(f"  🆔 JOB ID:           {job_data['job_id']}")
        print(f"  💼 TITRE:            {job_data['titre_poste']}")
        print(f"  🏢 ENTREPRISE:       {job_data['entreprise']}")
        print(f"  📍 LOCALISATION:     {job_data['localisation']}")
        print(f"  📊 NIVEAU:           {job_data['niveau_souhaite']} ({job_data['annees_min']}-{job_data['annees_max']} ans)")
        print(f"  🏷️  DOMAINE:          {job_data['domaine'].upper()}")
        print(f"  🛠️  COMPÉTENCES:      {len(skills_list)} skills → {skills_preview}")
        print(f"  🔤 TOKENS NLP:       {job_data['nb_tokens_original']} → {job_data['nb_tokens_processed']} (-{reduction:.1f}%)")
        print(f"  📝 PREVIEW:          {titre_preview}")
    
    def _afficher_statistiques_finales(self):
        """Affiche les statistiques finales de l'indexation"""
        logger.info("\n" + "="*120)
        logger.info("✅ INDEXATION AUTOMATIQUE TERMINÉE AVEC SUCCÈS")
        logger.info("="*120)
        logger.info(f"\n📊 Résumé:")
        logger.info(f"   • Offres indexées avec succès: {self.success_count}")
        logger.info(f"   • Offres en erreur: {self.error_count}")
        logger.info(f"   • Total traité: {self.total_jobs}")
        logger.info(f"   • Taux de succès: {(self.success_count/self.total_jobs*100):.1f}%")
        logger.info(f"\n📁 Index sauvegardé: {self.index_dir}")
        logger.info(f"\n🔍 Pipeline NLP appliqué:")
        logger.info(f"   ✓ Chargement JSON")
        logger.info(f"   ✓ Minuscules")
        logger.info(f"   ✓ Suppression ponctuation")
        logger.info(f"   ✓ Tokenisation (NLTK)")
        logger.info(f"   ✓ Suppression stopwords (EN + FR)")
        logger.info(f"   ✓ Lemmatisation (WordNet)")
        logger.info(f"   ✓ Préservation des compétences techniques")


# ========================================================
# FONCTION PRINCIPALE
# ========================================================
def indexer_offres_automatique(force: bool = False):
    """
    Point d'entrée principal pour l'indexation automatique
    
    Args:
        force: Si True, recrée l'index complètement
    """
    indexer = JobIndexer()
    indexer.indexer_toutes_les_offres(force=force)


# ========================================================
# FONCTION D'INDEXATION EN TEMPS RÉEL (FIXED)
# ========================================================
def indexer_offre_depuis_donnees(
    job_id: str,
    job_data: dict,
    user_id: str = ""
) -> bool:
    """
    Indexe une offre d'emploi en temps réel après soumission par le recruteur.
    
    FIXED:
    - Validation robuste de job_id
    - Gestion des doublons (suppression avant ajout)
    - Gestion d'erreurs complète
    
    Args:
        job_id: L'ID de l'offre dans la base de données PostgreSQL.
        job_data: Dictionnaire contenant les données brutes de l'offre.
        user_id: ID du recruteur qui a posté l'offre.
        
    Returns:
        True si l'indexation réussit, False sinon.
    """
    # FIXED: Validation de job_id
    is_valid, error_msg = valider_job_id(job_id)
    if not is_valid:
        logger.error(f"❌ Validation échouée pour l'offre: {error_msg}")
        return False
    
    job_id_str = str(job_id).strip()
    
    try:
        # Initialisation de la classe pour accéder à la logique d'extraction et de preprocessing
        indexer = JobIndexer() 
        
        # Utilisation de la méthode interne pour structurer et prétraiter les données
        job_data_processed = indexer._extraire_donnees_offre(job_data)
        
        if job_data_processed is None:
            logger.error(f"❌ Échec du prétraitement pour l'offre #{job_id_str}.")
            return False

        # Mise à jour de l'ID
        job_data_processed['job_id'] = job_id_str

        # 1. Ouverture de l'index Whoosh
        ix = open_dir(str(JOB_INDEX))
        
        # FIXED: Suppression du doublon si existant
        try:
            with ix.searcher() as searcher:
                from whoosh.qparser import QueryParser
                query_parser = QueryParser("job_id", ix.schema)
                query = query_parser.parse(job_id_str)
                results = searcher.search(query)
                
                if len(results) > 0:
                    logger.info(f"⚠️ Offre #{job_id_str} existe déjà. Suppression avant réindexation.")
                    
                    # Suppression via AsyncWriter
                    with ix.writer() as writer:
                        writer.delete_by_term("job_id", job_id_str)
        except Exception as e:
            logger.warning(f"⚠️ Vérification doublon échouée: {e}. Continuant l'indexation...")

        # 2. Indexation du document (nouveau writer après suppression)
        writer = AsyncWriter(ix)
        
        try:
            writer.add_document(
                job_id=job_data_processed['job_id'],
                titre_poste=job_data_processed['titre_poste'],
                description=job_data_processed['description'],
                titre_poste_processed=job_data_processed['titre_poste_processed'],
                description_processed=job_data_processed['description_processed'],
                competences_requises=job_data_processed['competences_requises'],
                localisation=job_data_processed['localisation'],
                niveau_souhaite=job_data_processed['niveau_souhaite'],
                domaine=job_data_processed['domaine'],
                annees_min=job_data_processed['annees_min'],
                annees_max=job_data_processed['annees_max'],
                entreprise=job_data_processed['entreprise'],
                type_contrat=job_data_processed['type_contrat'],
                mode_travail=job_data_processed['mode_travail'],
                nb_tokens_original=job_data_processed['nb_tokens_original'],
                nb_tokens_processed=job_data_processed['nb_tokens_processed']
            )
            
            # 3. Commit
            writer.commit()
            logger.info(f"✅ Offre d'emploi #{job_id_str} indexée en temps réel par le recruteur {user_id}.")
            return True
        
        except Exception as e:
            writer.cancel()
            logger.error(f"❌ Erreur lors de l'ajout du document #{job_id_str}: {e}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Échec indexation offre #{job_id_str}: {e}")
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
    
    indexer_offres_automatique(force=force_recreate)