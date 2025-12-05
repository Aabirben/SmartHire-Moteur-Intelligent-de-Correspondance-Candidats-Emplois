"""
MOTEUR DE RECHERCHE BOOLÉEN PRINCIPAL - VERSION AMÉLIORÉE
✅ Support scoring hybride (BM25F + boost champs)
✅ Logs détaillés pour debugging
✅ Gestion avancée des filtres (contract_type, tags_manuels)
"""

from whoosh.index import open_dir
from whoosh import scoring
from typing import List, Dict, Optional
import logging

from recherche_booleenne.config import (
    CV_INDEX_PATH,
    JOB_INDEX_PATH,
    CV_MAPPING,
    JOB_MAPPING,
    SEARCH_CONFIG
)
from recherche_booleenne.query_builder import BooleanQueryBuilder
from recherche_booleenne.utils import (
    validate_search_filters,
    format_cv_result,
    format_job_result
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BooleanSearchEngine:
    """
    Moteur de recherche booléen pour SmartHire
    
    Fonctionnalités v2:
    - ✅ Recherche dans texte_pretraite (NLP)
    - ✅ Support tags_manuels (indexation semi-auto)
    - ✅ Scoring hybride BM25F + boost champs
    - ✅ Filtres avancés (contract_type, tags)
    - ✅ Logs détaillés pour debugging
    """
    
    def __init__(self):
        """Initialise les index Whoosh"""
        try:
            self.cv_index = open_dir(CV_INDEX_PATH)
            self.job_index = open_dir(JOB_INDEX_PATH)
            
            logger.info("✅ Index CV et offres chargés avec succès")
            logger.info(f"  • CV mappés: {len(CV_MAPPING)}")
            logger.info(f"  • Offres mappées: {len(JOB_MAPPING)}")
            
            # Vérification des champs indexés
            cv_fields = list(self.cv_index.schema.names())
            job_fields = list(self.job_index.schema.names())
            
            logger.info(f"  • Champs CV: {', '.join(cv_fields[:5])}... ({len(cv_fields)} total)")
            logger.info(f"  • Champs Offres: {', '.join(job_fields[:5])}... ({len(job_fields)} total)")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement index: {e}")
            raise
    
    
    def search_jobs_for_candidate(
        self,
        query_text: str = "",
        filters: Optional[Dict] = None,
        limit: int = 10,
        use_nlp: bool = True
    ) -> Dict:
        """
        RECHERCHE OFFRES POUR UN CANDIDAT
        
        ✅ AMÉLIORATIONS :
        - Utilise texte_pretraite (NLP) par défaut
        - Support contract_type, tags_manuels
        - Logs détaillés de la requête construite
        
        Args:
            query_text: Texte libre (ex: "python developer casablanca")
            filters: Filtres structurés
            limit: Nombre max de résultats
            use_nlp: Utiliser champs NLP (texte_pretraite)
        
        Returns:
            {
                "results": [...],
                "total": 12,
                "query_info": {...}
            }
        """
        filters = validate_search_filters(filters or {})
        limit = min(limit, SEARCH_CONFIG["max_limit"])
        
        logger.info("="*80)
        logger.info("🔍 RECHERCHE OFFRES POUR CANDIDAT")
        logger.info(f"  • Requête texte: '{query_text}'")
        logger.info(f"  • Filtres: {filters}")
        logger.info(f"  • Utilisation NLP: {use_nlp}")
        logger.info("="*80)
        
        # ✅ AMÉLIORATION : Utilise BM25F pour scoring (meilleur que BM25 par défaut)
        with self.job_index.searcher(weighting=scoring.BM25F()) as searcher:
            query_builder = BooleanQueryBuilder(self.job_index.schema, is_cv=False)
            
            final_query = query_builder.build_complete_query(
                text=query_text,
                skills=filters.get("skills", []),
                min_exp=filters.get("experience_min"),
                max_exp=filters.get("experience_max"),
                location=filters.get("location", ""),
                level=filters.get("level", ""),
                remote=filters.get("remote", False),
                contract_type=filters.get("contract_type", ""),  # ✅ NOUVEAU
                tags=filters.get("tags", []),  # ✅ NOUVEAU
                skills_operator=filters.get("boolean_operator", "AND"),
                main_operator="AND"  # Tous les filtres DOIVENT matcher
            )
            
            if not final_query:
                logger.warning("⚠️ Aucune requête valide construite")
                return {
                    "results": [],
                    "total": 0,
                    "query_info": {
                        "query_text": query_text,
                        "filters": filters,
                        "error": "Aucun critère de recherche valide"
                    }
                }
            
            logger.info(f"📊 Requête Whoosh construite:")
            logger.info(f"   {final_query}")
            
            # Exécution de la recherche
            results = searcher.search(final_query, limit=limit)
            
            logger.info(f"✅ {len(results)} offres trouvées")
            
            # Formatage des résultats
            formatted_results = []
            for i, hit in enumerate(results, 1):
                job_id = hit.get("job_id")
                postgres_id = JOB_MAPPING.get(job_id)
                
                formatted = format_job_result(dict(hit), postgres_id)
                formatted["score"] = hit.score  # ✅ Ajout du score BM25F
                formatted["rank"] = i
                
                formatted_results.append(formatted)
                
                # Log des 3 premiers résultats
                if i <= 3:
                    logger.info(f"  {i}. {formatted['titre']} - Score: {hit.score:.2f}")
            
            return {
                "results": formatted_results,
                "total": len(results),
                "query_info": {
                    "query_text": query_text,
                    "filters": filters,
                    "whoosh_query": str(final_query),
                    "use_nlp": use_nlp
                }
            }
    
    
    def search_cvs_for_recruiter(
        self,
        query_text: str = "",
        filters: Optional[Dict] = None,
        limit: int = 10,
        use_nlp: bool = True
    ) -> Dict:
        """
        RECHERCHE CV POUR UN RECRUTEUR
        
        ✅ AMÉLIORATIONS :
        - Utilise texte_pretraite (NLP) par défaut
        - Support contract_type, tags_manuels
        - Logs détaillés
        
        Args:
            query_text: Texte libre
            filters: Filtres structurés
            limit: Nombre max de résultats
            use_nlp: Utiliser champs NLP
        
        Returns:
            {
                "results": [...],
                "total": 8,
                "query_info": {...}
            }
        """
        filters = validate_search_filters(filters or {})
        limit = min(limit, SEARCH_CONFIG["max_limit"])
        
        logger.info("="*80)
        logger.info("🔍 RECHERCHE CV POUR RECRUTEUR")
        logger.info(f"  • Requête texte: '{query_text}'")
        logger.info(f"  • Filtres: {filters}")
        logger.info(f"  • Utilisation NLP: {use_nlp}")
        logger.info("="*80)
        
        with self.cv_index.searcher(weighting=scoring.BM25F()) as searcher:
            query_builder = BooleanQueryBuilder(self.cv_index.schema, is_cv=True)
            
            final_query = query_builder.build_complete_query(
                text=query_text,
                skills=filters.get("skills", []),
                min_exp=filters.get("experience_min"),
                max_exp=filters.get("experience_max"),
                location=filters.get("location", ""),
                contract_type=filters.get("contract_type", ""),  # ✅ NOUVEAU
                tags=filters.get("tags", []),  # ✅ NOUVEAU
                skills_operator=filters.get("boolean_operator", "AND"),
                main_operator="AND"
            )
            
            if not final_query:
                logger.warning("⚠️ Aucune requête valide construite")
                return {
                    "results": [],
                    "total": 0,
                    "query_info": {
                        "query_text": query_text,
                        "filters": filters,
                        "error": "Aucun critère de recherche valide"
                    }
                }
            
            logger.info(f"📊 Requête Whoosh construite:")
            logger.info(f"   {final_query}")
            
            results = searcher.search(final_query, limit=limit)
            
            logger.info(f"✅ {len(results)} CV trouvés")
            
            formatted_results = []
            for i, hit in enumerate(results, 1):
                cv_id = hit.get("doc_id")
                postgres_id = CV_MAPPING.get(cv_id)
                
                formatted = format_cv_result(dict(hit), postgres_id)
                formatted["score"] = hit.score  # ✅ Ajout du score BM25F
                formatted["rank"] = i
                
                formatted_results.append(formatted)
                
                if i <= 3:
                    logger.info(f"  {i}. {formatted['nom']} - Score: {hit.score:.2f}")
            
            return {
                "results": formatted_results,
                "total": len(results),
                "query_info": {
                    "query_text": query_text,
                    "filters": filters,
                    "whoosh_query": str(final_query),
                    "use_nlp": use_nlp
                }
            }
    
    
    def get_cv_by_id(self, cv_id: str) -> Optional[Dict]:
        """
        Récupère un CV par son ID système
        
        Args:
            cv_id: ID système (ex: "cv_cv_01_amine_tazi")
        
        Returns:
            CV formaté ou None
        """
        logger.info(f"🔍 Récupération CV: {cv_id}")
        
        with self.cv_index.searcher() as searcher:
            results = searcher.documents(doc_id=cv_id)
            
            for hit in results:
                postgres_id = CV_MAPPING.get(cv_id)
                logger.info(f"✅ CV trouvé (PostgreSQL ID: {postgres_id})")
                return format_cv_result(dict(hit), postgres_id)
        
        logger.warning(f"⚠️ CV non trouvé: {cv_id}")
        return None
    
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """
        Récupère une offre par son ID système
        
        Args:
            job_id: ID système (ex: "offre_job-0001-2025")
        
        Returns:
            Offre formatée ou None
        """
        logger.info(f"🔍 Récupération offre: {job_id}")
        
        with self.job_index.searcher() as searcher:
            results = searcher.documents(job_id=job_id)
            
            for hit in results:
                postgres_id = JOB_MAPPING.get(job_id)
                logger.info(f"✅ Offre trouvée (PostgreSQL ID: {postgres_id})")
                return format_job_result(dict(hit), postgres_id)
        
        logger.warning(f"⚠️ Offre non trouvée: {job_id}")
        return None
    
    
    def search_by_tags(
        self,
        tags: List[str],
        is_cv: bool = True,
        operator: str = "OR",
        limit: int = 10
    ) -> Dict:
        """
        ✅ NOUVEAU : Recherche directe par tags_manuels (indexation semi-auto)
        
        Args:
            tags: Liste de tags (ex: ["backend_developer", "python", "senior"])
            is_cv: True pour CV, False pour offres
            operator: "AND" ou "OR"
            limit: Nombre max de résultats
        
        Returns:
            Résultats de recherche
        """
        logger.info("="*80)
        logger.info(f"🔍 RECHERCHE PAR TAGS ({'CV' if is_cv else 'OFFRES'})")
        logger.info(f"  • Tags: {tags}")
        logger.info(f"  • Opérateur: {operator}")
        logger.info("="*80)
        
        index = self.cv_index if is_cv else self.job_index
        mapping = CV_MAPPING if is_cv else JOB_MAPPING
        
        with index.searcher(weighting=scoring.BM25F()) as searcher:
            query_builder = BooleanQueryBuilder(index.schema, is_cv=is_cv)
            
            query = query_builder.build_tags_query(tags, operator)
            
            if not query:
                return {"results": [], "total": 0, "query_info": {"error": "Tags invalides"}}
            
            logger.info(f"📊 Requête: {query}")
            
            results = searcher.search(query, limit=limit)
            
            formatted_results = []
            for hit in results:
                doc_id = hit.get("doc_id" if is_cv else "job_id")
                postgres_id = mapping.get(doc_id)
                
                if is_cv:
                    formatted = format_cv_result(dict(hit), postgres_id)
                else:
                    formatted = format_job_result(dict(hit), postgres_id)
                
                formatted["score"] = hit.score
                formatted_results.append(formatted)
            
            logger.info(f"✅ {len(results)} résultats trouvés")
            
            return {
                "results": formatted_results,
                "total": len(results),
                "query_info": {
                    "tags": tags,
                    "operator": operator,
                    "whoosh_query": str(query)
                }
            }