"""
CONSTRUCTION DE REQUÊTES WHOOSH BOOLÉENNES - VERSION AMÉLIORÉE
✅ Support complet des champs indexés (tags_manuels, texte_pretraite)
✅ Opérateurs AND/OR/NOT explicites
✅ Recherche hybride texte + filtres stricts
"""

from whoosh import query as wquery
from whoosh.qparser import MultifieldParser, QueryParser, OrGroup, AndGroup
from whoosh.fields import Schema
from typing import List, Optional
import logging

from recherche_booleenne.config import CV_SCHEMA_FIELDS, JOB_SCHEMA_FIELDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BooleanQueryBuilder:
    """
    Constructeur de requêtes booléennes avancées
    
    Nouveautés v2:
    - Recherche dans tags_manuels (indexation semi-auto)
    - Utilisation prioritaire de texte_pretraite (NLP)
    - Support NOT explicite
    - Boost dynamique selon pertinence champs
    """
    
    def __init__(self, schema: Schema, is_cv: bool = True):
        self.schema = schema
        self.is_cv = is_cv
        self.fields = CV_SCHEMA_FIELDS if is_cv else JOB_SCHEMA_FIELDS
    
    
    def build_text_query(
        self, 
        text: str, 
        use_processed: bool = True,
        boost_fields: bool = True
    ) -> Optional[wquery.Query]:
        """
        Construit une requête texte multi-champs avec boost
        
        ✅ AMÉLIORATION : Utilise texte_pretraite en priorité + boost selon importance
        
        Args:
            text: Texte de recherche
            use_processed: Utiliser champs NLP
            boost_fields: Appliquer boost de pertinence
        
        Returns:
            Query Whoosh ou None
        """
        if not text or not text.strip():
            return None
        
        # Sélection des champs selon le type et preprocessing
        if self.is_cv:
            if use_processed:
                # ✅ CORRECTION : Utilise texte_pretraite (champ NLP) en priorité
                search_fields = {
                    "texte_pretraite": 2.0,      # Boost x2 (texte NLP complet)
                    "titre_profil": 1.5,          # Boost x1.5 (titre important)
                    "competences": 1.8,           # Boost x1.8 (compétences critiques)
                    "resume_complet": 1.0         # Boost x1 (contexte)
                }
            else:
                search_fields = {
                    "resume_complet": 1.5,
                    "titre_profil": 1.3,
                    "description_experience": 1.0
                }
        else:  # Offres
            if use_processed:
                search_fields = {
                    "titre_poste_processed": 2.0,
                    "description_processed": 1.5,
                    "competences_requises": 1.8
                }
            else:
                search_fields = {
                    "titre_poste": 2.0,
                    "description": 1.5,
                    "competences_requises": 1.8
                }
        
        # Construction avec boost
        if boost_fields:
            field_boosts = search_fields
        else:
            field_boosts = {k: 1.0 for k in search_fields.keys()}
        
        parser = MultifieldParser(
            list(field_boosts.keys()),
            schema=self.schema,
            fieldboosts=field_boosts,
            group=OrGroup  # OR = au moins un champ matche
        )
        
        try:
            parsed_query = parser.parse(text)
            logger.info(f"✅ Requête texte construite avec boost: {parsed_query}")
            return parsed_query
        except Exception as e:
            logger.error(f"❌ Erreur parsing texte '{text}': {e}")
            return None
    
    
    def build_skills_query(
        self, 
        skills: List[str], 
        operator: str = "AND",
        include_tags: bool = True
    ) -> Optional[wquery.Query]:
        """
        Construit une requête sur compétences
        
        ✅ AMÉLIORATION : Cherche aussi dans tags_manuels (indexation semi-auto)
        
        Args:
            skills: Liste de compétences
            operator: "AND" (toutes) / "OR" (au moins une) / "NOT" (exclure)
            include_tags: Chercher aussi dans tags_manuels
        
        Returns:
            Query Whoosh ou None
        """
        if not skills:
            return None
        
        skill_field = "competences" if self.is_cv else "competences_requises"
        skill_queries = []
        
        for skill in skills:
            skill = skill.lower().strip()
            if not skill:
                continue
            
            # Requête principale sur compétences
            skill_query = wquery.Term(skill_field, skill)
            
            # ✅ AMÉLIORATION : Cherche aussi dans tags_manuels
            if include_tags:
                tag_query = wquery.Term("tags_manuels", skill)
                # OR entre competences et tags_manuels
                combined_skill = wquery.Or([skill_query, tag_query])
                skill_queries.append(combined_skill)
            else:
                skill_queries.append(skill_query)
        
        if not skill_queries:
            return None
        
        # Combinaison selon opérateur
        if operator.upper() == "AND":
            combined = wquery.And(skill_queries)
        elif operator.upper() == "NOT":
            # NOT = exclure ces compétences
            combined = wquery.Not(wquery.Or(skill_queries))
        else:  # OR
            combined = wquery.Or(skill_queries)
        
        logger.info(f"✅ Requête skills ({operator}) construite: {combined}")
        return combined
    
    
    def build_experience_query(
        self, 
        min_exp: Optional[int] = None, 
        max_exp: Optional[int] = None
    ) -> Optional[wquery.Query]:
        """
        Construit une requête sur expérience (plage numérique)
        
        Args:
            min_exp: Expérience minimale (années)
            max_exp: Expérience maximale (années)
        
        Returns:
            Query Whoosh ou None
        """
        if min_exp is None and max_exp is None:
            return None
        
        if self.is_cv:
            exp_field = "annees"
        else:
            # ✅ AMÉLIORATION : Pour offres, vérifie que min_exp candidat >= annees_min offre
            exp_field = "annees_min"
        
        experience_query = wquery.NumericRange(
            exp_field,
            start=min_exp if min_exp is not None else 0,
            end=max_exp if max_exp is not None else 50
        )
        
        logger.info(f"✅ Requête expérience construite: {experience_query}")
        return experience_query
    
    
    def build_location_query(self, location: str) -> Optional[wquery.Query]:
        """
        Construit une requête sur localisation (recherche flexible)
        
        Args:
            location: Ville/région (ex: "casablanca")
        
        Returns:
            Query Whoosh ou None
        """
        if not location or not location.strip():
            return None
        
        location = location.lower().strip()
        
        # ✅ AMÉLIORATION : Cherche aussi dans tags_manuels
        loc_query = wquery.Or([
            wquery.Term("localisation", location),
            wquery.Term("tags_manuels", location)
        ])
        
        logger.info(f"✅ Requête localisation construite: {loc_query}")
        return loc_query
    
    
    def build_contract_type_query(self, contract_type: str) -> Optional[wquery.Query]:
        """
        ✅ NOUVEAU : Filtre par type de contrat (CDI/CDD/Freelance)
        
        Args:
            contract_type: Type de contrat (ex: "cdi")
        
        Returns:
            Query Whoosh ou None
        """
        if not contract_type or not contract_type.strip():
            return None
        
        contract_type = contract_type.lower().strip()
        
        if self.is_cv:
            contract_query = wquery.Term("type_contrat", contract_type)
        else:
            contract_query = wquery.Term("type_contrat", contract_type)
        
        logger.info(f"✅ Requête type contrat construite: {contract_query}")
        return contract_query
    
    
    def build_level_query(self, level: str) -> Optional[wquery.Query]:
        """
        Construit une requête sur niveau (junior/senior/expert)
        UNIQUEMENT POUR OFFRES
        
        Args:
            level: Niveau souhaité (ex: "senior")
        
        Returns:
            Query Whoosh ou None
        """
        if self.is_cv:
            logger.warning("⚠️ Niveau non applicable aux CV (ignoré)")
            return None
        
        if not level or not level.strip():
            return None
        
        level = level.lower().strip()
        
        valid_levels = ["junior", "intermediaire", "senior", "expert"]
        if level not in valid_levels:
            logger.warning(f"⚠️ Niveau invalide '{level}' (ignoré)")
            return None
        
        level_query = wquery.Term("niveau_souhaite", level)
        
        logger.info(f"✅ Requête niveau construite: {level_query}")
        return level_query
    
    
    def build_remote_query(self) -> Optional[wquery.Query]:
        """
        Construit une requête pour offres remote uniquement
        UNIQUEMENT POUR OFFRES
        
        Returns:
            Query Whoosh ou None
        """
        if self.is_cv:
            return None
        
        remote_query = wquery.Or([
            wquery.Term("mode_travail", "remote"),
            wquery.Term("mode_travail", "hybrid")
        ])
        
        logger.info(f"✅ Requête remote construite: {remote_query}")
        return remote_query
    
    
    def build_tags_query(
        self, 
        tags: List[str], 
        operator: str = "OR"
    ) -> Optional[wquery.Query]:
        """
        ✅ NOUVEAU : Recherche directe dans tags_manuels (indexation semi-auto)
        
        Args:
            tags: Liste de tags (ex: ["backend_developer", "python"])
            operator: "AND" ou "OR"
        
        Returns:
            Query Whoosh ou None
        """
        if not tags:
            return None
        
        tag_queries = []
        for tag in tags:
            tag = tag.lower().strip()
            if tag:
                tag_queries.append(wquery.Term("tags_manuels", tag))
        
        if not tag_queries:
            return None
        
        if operator.upper() == "AND":
            combined = wquery.And(tag_queries)
        else:
            combined = wquery.Or(tag_queries)
        
        logger.info(f"✅ Requête tags ({operator}) construite: {combined}")
        return combined
    
    
    def combine_queries(
        self, 
        queries: List[wquery.Query], 
        operator: str = "AND"
    ) -> Optional[wquery.Query]:
        """
        Combine plusieurs requêtes avec AND/OR
        
        Args:
            queries: Liste de Query Whoosh
            operator: "AND" ou "OR"
        
        Returns:
            Query combinée ou None
        """
        valid_queries = [q for q in queries if q is not None]
        
        if not valid_queries:
            logger.warning("⚠️ Aucune requête valide à combiner")
            return None
        
        if len(valid_queries) == 1:
            return valid_queries[0]
        
        if operator.upper() == "AND":
            combined = wquery.And(valid_queries)
        else:
            combined = wquery.Or(valid_queries)
        
        logger.info(f"✅ Requêtes combinées ({operator}): {combined}")
        return combined
    
    
    def build_complete_query(
        self,
        text: str = "",
        skills: List[str] = None,
        min_exp: int = None,
        max_exp: int = None,
        location: str = "",
        level: str = "",
        remote: bool = False,
        contract_type: str = "",
        tags: List[str] = None,
        skills_operator: str = "AND",
        main_operator: str = "AND"
    ) -> Optional[wquery.Query]:
        """
        Construit une requête complète avec tous les filtres
        
        ✅ AMÉLIORATIONS :
        - Support contract_type
        - Support tags_manuels
        - main_operator pour combiner tous les filtres
        
        Args:
            text: Recherche textuelle libre
            skills: Liste de compétences
            min_exp/max_exp: Plage d'expérience
            location: Localisation
            level: Niveau (pour offres)
            remote: Remote only (pour offres)
            contract_type: Type de contrat (CDI/CDD/Freelance)
            tags: Liste de tags manuels
            skills_operator: "AND" ou "OR" pour compétences
            main_operator: "AND" ou "OR" pour combiner tous les filtres
        
        Returns:
            Query Whoosh complète ou None
        """
        queries_to_combine = []
        
        # 1. Requête texte (recherche dans texte_pretraite)
        if text:
            text_query = self.build_text_query(text, use_processed=True, boost_fields=True)
            if text_query:
                queries_to_combine.append(text_query)
        
        # 2. Requête compétences (cherche aussi dans tags_manuels)
        if skills:
            skills_query = self.build_skills_query(skills, skills_operator, include_tags=True)
            if skills_query:
                queries_to_combine.append(skills_query)
        
        # 3. Requête expérience
        if min_exp is not None or max_exp is not None:
            exp_query = self.build_experience_query(min_exp, max_exp)
            if exp_query:
                queries_to_combine.append(exp_query)
        
        # 4. Requête localisation (cherche aussi dans tags_manuels)
        if location:
            loc_query = self.build_location_query(location)
            if loc_query:
                queries_to_combine.append(loc_query)
        
        # 5. ✅ NOUVEAU : Requête type de contrat
        if contract_type:
            contract_query = self.build_contract_type_query(contract_type)
            if contract_query:
                queries_to_combine.append(contract_query)
        
        # 6. ✅ NOUVEAU : Requête tags manuels
        if tags:
            tags_query = self.build_tags_query(tags, operator="OR")
            if tags_query:
                queries_to_combine.append(tags_query)
        
        # 7. Requête niveau (offres seulement)
        if level and not self.is_cv:
            level_query = self.build_level_query(level)
            if level_query:
                queries_to_combine.append(level_query)
        
        # 8. Remote (offres seulement)
        if remote and not self.is_cv:
            remote_query = self.build_remote_query()
            if remote_query:
                queries_to_combine.append(remote_query)
        
        # Combinaison finale
        return self.combine_queries(queries_to_combine, main_operator)