"""
============================================================================
SMARTHIRE - Modèle Booléen (CORRIGÉ - Gestion ID)
✅ Gestion correcte des IDs vides (CVs uploadés)
============================================================================
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

from whoosh.index import open_dir, exists_in
from whoosh import query as wquery

from backend.database.connection import get_db_connection
from backend.config.settings import CV_INDEX, JOB_INDEX, BASE_DIR
from backend.search.filter_processor import FilterProcessor

logger = logging.getLogger(__name__)

# ========================================================
# CLASSE PRINCIPALE
# ========================================================
class BooleanSearchModel:
    """Modèle booléen qui gère CVs système + CVs uploadés"""
    
    def __init__(self):
        self.pg_conn = get_db_connection()
        self.whoosh_cv_index = None
        self.whoosh_job_index = None
        self._init_whoosh()
        self.filter_processor = FilterProcessor()
        self._mapping_cache = None
    
    def __del__(self):
        if hasattr(self, 'pg_conn') and self.pg_conn:
            self.pg_conn.close()
    
    def _init_whoosh(self):
        """Initialise index Whoosh"""
        try:
            if exists_in(str(CV_INDEX)):
                self.whoosh_cv_index = open_dir(str(CV_INDEX))
                logger.info("✅ Index Whoosh CV chargé")
            
            if exists_in(str(JOB_INDEX)):
                self.whoosh_job_index = open_dir(str(JOB_INDEX))
                logger.info("✅ Index Whoosh Offres chargé")
        except Exception as e:
            logger.error(f"❌ Erreur Whoosh: {e}")
    
    # ========================================================
    # API PRINCIPALE
    # ========================================================
    def search(
        self,
        query_terms: Dict[str, List[str]] = None,
        filters: Dict = None,
        target: str = "cvs"
    ) -> List[Dict]:
        """Recherche booléenne avec filtres"""
        query_terms = query_terms or {}
        filters = filters or {}
        
        logger.info(f"🔍 Recherche booléenne sur {target}")
        
        processed_filters = self.filter_processor.process(filters)
        
        combined_terms = self._combine_terms_and_filters(
            query_terms,
            processed_filters
        )
        
        logger.info(f"   Terms finaux: {combined_terms}")
        
        pg_results = self._search_postgresql(
            combined_terms,
            processed_filters,
            target
        )
        logger.info(f"   PostgreSQL → {len(pg_results)} résultats")
        
        whoosh_results = self._search_whoosh(
            combined_terms,
            processed_filters,
            target
        )
        logger.info(f"   Whoosh → {len(whoosh_results)} résultats")
        
        merged = self._merge_results(pg_results, whoosh_results)
        
        logger.info(f"✅ Total: {len(merged)} résultats")
        return merged
    
    def _combine_terms_and_filters(
        self,
        query_terms: Dict,
        processed_filters: Dict
    ) -> Dict:
        """Fusionne query_terms explicites avec filtres"""
        combined = {
            "must_have": list(query_terms.get("must_have", [])),
            "should_have": list(query_terms.get("should_have", [])),
            "must_not_have": list(query_terms.get("must_not_have", []))
        }
        
        bool_filters = processed_filters.get("boolean_filters", {})
        
        if "skills_and" in bool_filters:
            combined["must_have"].extend(bool_filters["skills_and"])
        
        if "skills_or" in bool_filters:
            combined["should_have"].extend(bool_filters["skills_or"])
        
        if "location_or" in bool_filters:
            combined["should_have"].extend(bool_filters["location_or"])
        
        if "level_or" in bool_filters:
            combined["should_have"].extend(bool_filters["level_or"])
        
        combined["must_have"] = list(set(combined["must_have"]))
        combined["should_have"] = list(set(combined["should_have"]))
        combined["must_not_have"] = list(set(combined["must_not_have"]))
        
        return combined
    
    # ========================================================
    # RECHERCHE POSTGRESQL
    # ========================================================
    def _search_postgresql(
        self,
        terms: Dict,
        processed_filters: Dict,
        target: str
    ) -> List[Dict]:
        """Recherche dans PostgreSQL (CVs système validés)"""
        table = "cvs" if target == "cvs" else "offres"
        
        sql_where = processed_filters.get("sql_conditions", {}).get("where", "TRUE")
        sql_params = processed_filters.get("sql_conditions", {}).get("params", [])
        
        extra_conditions = []
        extra_params = []
        
        for term in terms.get("must_have", []):
            extra_conditions.append("%s = ANY(tags_manuels)")
            extra_params.append(term.lower())
        
        for term in terms.get("must_not_have", []):
            extra_conditions.append("NOT (%s = ANY(tags_manuels))")
            extra_params.append(term.lower())
        
        all_conditions = [sql_where]
        if extra_conditions:
            all_conditions.extend(extra_conditions)
        
        final_where = " AND ".join(all_conditions)
        final_params = sql_params + extra_params
        
        if target == "cvs":
            query = f"""
            SELECT 
                id,
                nom,
                email,
                tags_manuels,
                competences,
                localisation,
                niveau_estime,
                annees_experience,
                type_contrat,
                diplome,
                texte_complet
            FROM {table}
            WHERE source_systeme = TRUE
              AND {final_where}
            LIMIT 100
            """
        else:
            query = f"""
            SELECT 
                id,
                titre,
                entreprise,
                tags_manuels,
                competences_requises,
                localisation,
                niveau_souhaite,
                experience_min,
                type_contrat,
                diplome_requis,
                texte_complet
            FROM {table}
            WHERE source_systeme = TRUE
              AND {final_where}
            LIMIT 100
            """
        
        try:
            cur = self.pg_conn.cursor()
            cur.execute(query, final_params)
            rows = cur.fetchall()
            cur.close()
            
            results = []
            for row in rows:
                tags = set(row[3])
                
                score = self._calculate_boolean_score(
                    tags,
                    terms.get("must_have", []),
                    terms.get("should_have", [])
                )
                
                results.append({
                    "id": row[0],
                    "nom": row[1],
                    "email": row[2] if target == "cvs" else None,
                    "tags": list(tags),
                    "competences": row[4],
                    "localisation": row[5],
                    "niveau": row[6],
                    "experience": row[7],
                    "contrat": row[8],
                    "diplome": row[9],
                    "texte": row[10],
                    "score_boolean": score,
                    "source": "postgresql",
                    "source_type": "systeme"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur PostgreSQL: {e}")
            return []
    
    # ========================================================
    # RECHERCHE WHOOSH (CORRIGÉ)
    # ========================================================
    def _search_whoosh(
        self,
        terms: Dict,
        processed_filters: Dict,
        target: str
    ) -> List[Dict]:
        """
        Recherche dans Whoosh (CVs uploadés auto-indexés)
        
        ✅ CORRECTION: Utilise doc_id comme identifiant unique
        """
        idx = self.whoosh_cv_index if target == "cvs" else self.whoosh_job_index
        
        if not idx:
            logger.warning(f"⚠️ Index Whoosh {target} non disponible")
            return []
        
        try:
            with idx.searcher() as searcher:
                queries = []
                
                # 1. MUST (AND)
                for term in terms.get("must_have", []):
                    q = wquery.Term("competences", term.lower())
                    queries.append(q)
                
                # 2. SHOULD (OR)
                should_terms = terms.get("should_have", [])
                if should_terms:
                    or_queries = [
                        wquery.Term("competences", t.lower())
                        for t in should_terms
                    ]
                    queries.append(wquery.Or(or_queries))
                
                # 3. NOT
                for term in terms.get("must_not_have", []):
                    queries.append(
                        wquery.Not(wquery.Term("competences", term.lower()))
                    )
                
                # 4. Filtres range (expérience)
                range_filters = processed_filters.get("range_filters", {})
                if "experience" in range_filters:
                    min_exp, max_exp = range_filters["experience"]
                    queries.append(
                        wquery.NumericRange("annees", min_exp, max_exp)
                    )
                
                # Combinaison AND
                if queries:
                    final_query = wquery.And(queries)
                else:
                    final_query = wquery.Every()
                
                logger.debug(f"Whoosh query: {final_query}")
                
                results = searcher.search(final_query, limit=100)
                
                formatted = []
                for hit in results:
                    # ✅ CORRECTION: Utilise doc_id comme ID unique
                    # doc_id = filename (ex: "CV_01_Amine_Tazi.pdf")
                    doc_id = hit.get("doc_id", "")
                    
                    # ✅ CORRECTION: Ne pas utiliser user_id vide
                    # user_id est vide pour les CVs système indexés dans Whoosh
                    formatted.append({
                        "id": doc_id,  # ✅ doc_id au lieu de user_id
                        "doc_id": doc_id,
                        "nom": hit.get("nom", ""),
                        "email": "",
                        "competences": hit.get("competences", "").split(","),
                        "localisation": hit.get("localisation", ""),
                        "niveau": "",
                        "experience": hit.get("annees", 0),
                        "texte": hit.get("texte_pretraite", ""),
                        "score_boolean": hit.score,
                        "source": "whoosh",
                        "source_type": "uploaded"
                    })
                
                return formatted
                
        except Exception as e:
            logger.error(f"❌ Erreur Whoosh: {e}")
            return []
    
    # ========================================================
    # SCORING
    # ========================================================
    def _calculate_boolean_score(
        self,
        tags: set,
        must_have: List[str],
        should_have: List[str]
    ) -> float:
        """Calcul score booléen"""
        if must_have:
            must_matches = len([t for t in must_have if t in tags])
            must_score = must_matches / len(must_have)
        else:
            must_score = 1.0
        
        if should_have:
            should_matches = len([t for t in should_have if t in tags])
            should_score = should_matches / len(should_have)
        else:
            should_score = 0.0
        
        final = must_score * 0.7 + should_score * 0.3
        return round(final, 3)
    
    # ========================================================
    # FUSION RÉSULTATS
    # ========================================================
    def _merge_results(
        self,
        pg_results: List[Dict],
        whoosh_results: List[Dict]
    ) -> List[Dict]:
        """Fusionne PostgreSQL + Whoosh"""
        all_results = pg_results + whoosh_results
        all_results.sort(key=lambda x: x["score_boolean"], reverse=True)
        return all_results
    
    # ========================================================
    # MATCHING CV ↔ OFFRE (CORRIGÉ)
    # ========================================================
    def match_cv_to_job(self, cv_id, job_id) -> Dict:
        """
        Matching booléen CV ↔ Offre
        
        ✅ CORRECTION: Gestion des IDs vides et validation
        """
        # ✅ VALIDATION: Vérifier que les IDs ne sont pas vides
        if not cv_id or not job_id:
            return {
                "error": "ID CV ou offre invalide (vide)",
                "score": 0,
                "matches": [],
                "missing": [],
                "extra": [],
                "experience_ok": False
            }
        
        # ✅ CORRECTION: Convertir en int si possible (PostgreSQL)
        # Sinon, c'est un doc_id Whoosh (string)
        try:
            cv_id_int = int(cv_id)
            is_cv_pg = True
        except (ValueError, TypeError):
            cv_id_int = None
            is_cv_pg = False
        
        try:
            job_id_int = int(job_id)
            is_job_pg = True
        except (ValueError, TypeError):
            job_id_int = None
            is_job_pg = False
        
        cur = self.pg_conn.cursor()
        
        # ✅ CORRECTION: Récupérer CV (PostgreSQL OU Whoosh)
        if is_cv_pg:
            # CV depuis PostgreSQL
            cur.execute("""
                SELECT tags_manuels, competences, annees_experience, source_systeme
                FROM cvs WHERE id = %s
            """, (cv_id_int,))
            cv_row = cur.fetchone()
            
            if not cv_row:
                cur.close()
                return {"error": f"CV #{cv_id} introuvable en PostgreSQL"}
            
            cv_tags = set(cv_row[0]) if cv_row[3] else set(cv_row[1])
            cv_exp = cv_row[2]
        else:
            # CV depuis Whoosh (doc_id)
            if not self.whoosh_cv_index:
                cur.close()
                return {"error": "Index Whoosh CV non disponible"}
            
            try:
                with self.whoosh_cv_index.searcher() as searcher:
                    from whoosh.qparser import QueryParser
                    parser = QueryParser("doc_id", self.whoosh_cv_index.schema)
                    query = parser.parse(str(cv_id))
                    results = searcher.search(query, limit=1)
                    
                    if len(results) == 0:
                        cur.close()
                        return {"error": f"CV doc_id='{cv_id}' introuvable dans Whoosh"}
                    
                    hit = results[0]
                    cv_tags = set(hit.get("competences", "").split(","))
                    cv_exp = hit.get("annees", 0)
            except Exception as e:
                cur.close()
                return {"error": f"Erreur lecture Whoosh CV: {e}"}
        
        # ✅ CORRECTION: Récupérer offre (PostgreSQL)
        if not is_job_pg:
            cur.close()
            return {"error": "job_id doit être un ID PostgreSQL (integer)"}
        
        cur.execute("""
            SELECT tags_manuels, competences_requises, experience_min
            FROM offres WHERE id = %s
        """, (job_id_int,))
        job_row = cur.fetchone()
        
        cur.close()
        
        if not job_row:
            return {"error": f"Offre #{job_id} introuvable"}
        
        job_tags = set(job_row[1])
        job_exp_min = job_row[2]
        
        # Matching
        matches = cv_tags & job_tags
        missing = job_tags - cv_tags
        extra = cv_tags - job_tags
        
        score = len(matches) / len(job_tags) if job_tags else 0
        
        exp_ok = cv_exp >= job_exp_min
        if exp_ok:
            score *= 1.1
        
        return {
            "score": round(min(score, 1.0), 3),
            "matches": list(matches),
            "missing": list(missing),
            "extra": list(extra),
            "experience_ok": exp_ok
        }


# ========================================================
# TESTS
# ========================================================
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🔍 TEST MODÈLE BOOLÉEN (CORRIGÉ)")
    print("="*80)
    
    model = BooleanSearchModel()
    
    print("\n1️⃣ Test recherche avec filtres")
    results = model.search(
        filters={
            "skills": ["python", "java"],
            "location": ["casablanca"],
            "experience": [5, 10]
        },
        target="cvs"
    )
    
    print(f"Résultats: {len(results)}")
    for r in results[:3]:
        print(f"  • {r['nom']} - Score: {r['score_boolean']} - Source: {r['source_type']}")
    
    print("\n✅ Tests terminés!")