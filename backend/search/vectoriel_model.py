"""
Modèle Vectoriel BM25 pour SmartHire
Emplacement: backend/search/vectoriel_model.py

Implémente l'algorithme BM25 (Best Matching 25) pour la recherche par pertinence
"""

import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
import json

from database.connection import get_db_connection
from backend.config.settings import CV_INDEX, JOB_INDEX
from backend.indexation.preprocessing import pretraiter_texte
from whoosh.index import open_dir
from whoosh import qparser


class BM25Scorer:
    """
    Implémentation de l'algorithme BM25
    
    Formule BM25:
    score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))
    
    Où:
    - IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5))
    - f(qi,D) = fréquence du terme qi dans le document D
    - |D| = longueur du document D (nombre de tokens)
    - avgdl = longueur moyenne des documents
    - k1 = paramètre de saturation de fréquence (défaut: 1.5)
    - b = paramètre de normalisation de longueur (défaut: 0.75)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Paramètre de saturation (1.2-2.0 recommandé)
            b: Paramètre de normalisation longueur (0.75 recommandé)
        """
        self.k1 = k1
        self.b = b
        
        # Statistiques corpus (calculées à l'initialisation)
        self.N = 0  # Nombre total de documents
        self.avgdl = 0.0  # Longueur moyenne des documents
        self.df = {}  # Document frequency: {terme: nb_docs_contenant_terme}
        self.idf = {}  # Inverse document frequency: {terme: score_idf}
        self.doc_lengths = {}  # {doc_id: longueur}
        self.doc_terms = {}  # {doc_id: {terme: freq}}
    
    def build_index(self, documents: List[Dict]):
        """
        Construit l'index BM25 à partir des documents
        
        Args:
            documents: Liste de dicts avec clés:
                - id: identifiant unique
                - tokens: liste de tokens prétraités
                - texte_pretraite: texte complet prétraité
        """
        self.N = len(documents)
        
        if self.N == 0:
            return
        
        # 1. Calculer longueurs et fréquences des termes
        total_length = 0
        
        for doc in documents:
            doc_id = doc['id']
            tokens = doc.get('tokens', [])
            
            # Longueur du document
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_length += doc_len
            
            # Fréquences des termes
            term_freqs = Counter(tokens)
            self.doc_terms[doc_id] = dict(term_freqs)
            
            # Document frequency
            unique_terms = set(tokens)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1
        
        # 2. Calculer longueur moyenne
        self.avgdl = total_length / self.N if self.N > 0 else 0
        
        # 3. Calculer IDF pour tous les termes
        for term, df_value in self.df.items():
            # IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5))
            self.idf[term] = math.log(
                (self.N - df_value + 0.5) / (df_value + 0.5)
            )
    
    def score(self, query_tokens: List[str], doc_id: str) -> float:
        """
        Calcule le score BM25 pour une requête et un document
        
        Args:
            query_tokens: Tokens de la requête (après prétraitement)
            doc_id: ID du document à scorer
            
        Returns:
            Score BM25 (float >= 0)
        """
        if doc_id not in self.doc_terms:
            return 0.0
        
        doc_len = self.doc_lengths.get(doc_id, 0)
        if doc_len == 0:
            return 0.0
        
        score_total = 0.0
        doc_term_freqs = self.doc_terms[doc_id]
        
        # Pour chaque terme unique de la requête
        for term in set(query_tokens):
            if term not in self.idf:
                continue  # Terme inconnu
            
            # Fréquence du terme dans le document
            f_qi_D = doc_term_freqs.get(term, 0)
            
            if f_qi_D == 0:
                continue  # Terme absent du document
            
            # IDF du terme
            idf_qi = self.idf[term]
            
            # Normalisation de longueur
            norm = 1 - self.b + self.b * (doc_len / self.avgdl)
            
            # Score BM25 pour ce terme
            term_score = idf_qi * (
                (f_qi_D * (self.k1 + 1)) / 
                (f_qi_D + self.k1 * norm)
            )
            
            score_total += term_score
        
        return round(score_total, 4)
    
    def score_all(self, query_tokens: List[str]) -> Dict[str, float]:
        """
        Score tous les documents pour une requête
        
        Returns:
            {doc_id: score_bm25}
        """
        scores = {}
        
        for doc_id in self.doc_terms.keys():
            score = self.score(query_tokens, doc_id)
            if score > 0:
                scores[doc_id] = score
        
        return scores
    
    def get_stats(self) -> Dict:
        """Retourne statistiques de l'index"""
        return {
            "total_documents": self.N,
            "avg_doc_length": round(self.avgdl, 2),
            "unique_terms": len(self.df),
            "k1": self.k1,
            "b": self.b
        }


class VectorielSearchModel:
    """
    Modèle de recherche vectorielle utilisant BM25
    Gère PostgreSQL + Whoosh
    """
    
    def __init__(self):
        self.pg_conn = get_db_connection()
        self.whoosh_cv_index = None
        self.whoosh_job_index = None
        self._init_whoosh()
        
        # Scorers BM25 (un par source)
        self.bm25_cv_pg = BM25Scorer(k1=1.5, b=0.75)
        self.bm25_cv_whoosh = BM25Scorer(k1=1.5, b=0.75)
        self.bm25_job_pg = BM25Scorer(k1=1.5, b=0.75)
        self.bm25_job_whoosh = BM25Scorer(k1=1.5, b=0.75)
        
        # Construire index BM25
        self._build_bm25_indices()
    
    def _init_whoosh(self):
        """Initialise connexions Whoosh"""
        try:
            self.whoosh_cv_index = open_dir(CV_INDEX)
        except Exception as e:
            print(f"⚠️ CV Whoosh index non disponible: {e}")
        
        try:
            self.whoosh_job_index = open_dir(JOB_INDEX)
        except Exception as e:
            print(f"⚠️ Job Whoosh index non disponible: {e}")
    
    def _build_bm25_indices(self):
        """Construit les index BM25 pour toutes les sources"""
        
        print("🔨 Construction index BM25...")
        
        # 1. CVs PostgreSQL
        cv_pg_docs = self._load_postgresql_documents("cvs")
        self.bm25_cv_pg.build_index(cv_pg_docs)
        print(f"  ✅ CVs PostgreSQL: {len(cv_pg_docs)} docs")
        
        # 2. CVs Whoosh
        cv_whoosh_docs = self._load_whoosh_documents(self.whoosh_cv_index)
        self.bm25_cv_whoosh.build_index(cv_whoosh_docs)
        print(f"  ✅ CVs Whoosh: {len(cv_whoosh_docs)} docs")
        
        # 3. Jobs PostgreSQL
        job_pg_docs = self._load_postgresql_documents("offres")
        self.bm25_job_pg.build_index(job_pg_docs)
        print(f"  ✅ Jobs PostgreSQL: {len(job_pg_docs)} docs")
        
        # 4. Jobs Whoosh
        job_whoosh_docs = self._load_whoosh_documents(self.whoosh_job_index)
        self.bm25_job_whoosh.build_index(job_whoosh_docs)
        print(f"  ✅ Jobs Whoosh: {len(job_whoosh_docs)} docs")
        
        print("✅ Index BM25 construits\n")
    
    def _load_postgresql_documents(self, table: str) -> List[Dict]:
        """Charge documents PostgreSQL pour indexation BM25"""
        documents = []
        
        try:
            cur = self.pg_conn.cursor()
            
            if table == "cvs":
                query = """
                    SELECT id, nom, texte_complet, tags_manuels
                    FROM cvs
                    WHERE source_systeme = TRUE
                """
            else:  # offres
                query = """
                    SELECT id, titre, texte_complet, competences_requises
                    FROM offres
                    WHERE source_systeme = TRUE
                """
            
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                doc_id = str(row[0])
                texte = row[2] or ""
                
                # Prétraitement NLP
                texte_pretraite, tokens = pretraiter_texte(
                    texte, 
                    preserve_skills=True
                )
                
                documents.append({
                    "id": doc_id,
                    "nom": row[1],
                    "texte_pretraite": texte_pretraite,
                    "tokens": tokens,
                    "tags": row[3] if len(row) > 3 else []
                })
            
            cur.close()
            
        except Exception as e:
            print(f"❌ Erreur load PostgreSQL {table}: {e}")
        
        return documents
    
    def _load_whoosh_documents(self, index) -> List[Dict]:
        """Charge documents Whoosh pour indexation BM25"""
        documents = []
        
        if not index:
            return documents
        
        try:
            with index.searcher() as searcher:
                # Récupérer tous les documents
                from whoosh import query as wquery
                all_docs_query = wquery.Every()
                results = searcher.search(all_docs_query, limit=None)
                
                for hit in results:
                    doc_id = hit.get("doc_id", "")
                    texte_pretraite = hit.get("texte_pretraite", "")
                    
                    # Tokeniser
                    tokens = texte_pretraite.split() if texte_pretraite else []
                    
                    documents.append({
                        "id": doc_id,
                        "nom": hit.get("nom", ""),
                        "texte_pretraite": texte_pretraite,
                        "tokens": tokens,
                        "competences": hit.get("competences", "").split(",")
                    })
        
        except Exception as e:
            print(f"❌ Erreur load Whoosh: {e}")
        
        return documents
    
    def search(
        self,
        query: str,
        target: str = "cvs",
        top_k: int = 20
    ) -> Dict:
        """
        Recherche vectorielle BM25
        
        Args:
            query: Texte de la requête
            target: "cvs" ou "offres"
            top_k: Nombre max de résultats
            
        Returns:
            {
                "results": [...],
                "stats": {...}
            }
        """
        
        # 1. Prétraiter la requête
        texte_pretraite, query_tokens = pretraiter_texte(
            query,
            preserve_skills=True
        )
        
        if not query_tokens:
            return {
                "results": [],
                "stats": {
                    "query": query,
                    "query_tokens": [],
                    "total_results": 0
                }
            }
        
        # 2. Scorer avec BM25
        if target == "cvs":
            scores_pg = self.bm25_cv_pg.score_all(query_tokens)
            scores_whoosh = self.bm25_cv_whoosh.score_all(query_tokens)
        else:  # offres
            scores_pg = self.bm25_job_pg.score_all(query_tokens)
            scores_whoosh = self.bm25_job_whoosh.score_all(query_tokens)
        
        # 3. Récupérer détails et formater
        results_pg = self._fetch_postgresql_results(scores_pg, target)
        results_whoosh = self._fetch_whoosh_results(scores_whoosh, target)
        
        # 4. Fusionner et trier
        all_results = results_pg + results_whoosh
        all_results.sort(key=lambda x: x["score_bm25"], reverse=True)
        
        # 5. Top K
        top_results = all_results[:top_k]
        
        # 6. Statistiques
        stats = {
            "query": query,
            "query_tokens": query_tokens,
            "query_tokens_count": len(query_tokens),
            "total_results": len(all_results),
            "top_k": top_k,
            "source_breakdown": {
                "postgresql": len(results_pg),
                "whoosh": len(results_whoosh)
            },
            "bm25_params": {
                "k1": self.bm25_cv_pg.k1,
                "b": self.bm25_cv_pg.b
            },
            "score_range": {
                "max": round(top_results[0]["score_bm25"], 4) if top_results else 0,
                "min": round(top_results[-1]["score_bm25"], 4) if top_results else 0
            }
        }
        
        return {
            "results": top_results,
            "stats": stats
        }
    
    def _fetch_postgresql_results(
        self,
        scores: Dict[str, float],
        target: str
    ) -> List[Dict]:
        """Récupère détails documents PostgreSQL"""
        results = []
        
        if not scores:
            return results
        
        try:
            cur = self.pg_conn.cursor()
            ids = [int(doc_id) for doc_id in scores.keys()]
            
            if target == "cvs":
                query = """
                    SELECT id, nom, tags_manuels, localisation, 
                           annees_experience, niveau_estime
                    FROM cvs
                    WHERE id = ANY(%s)
                """
            else:
                query = """
                    SELECT id, titre, competences_requises, localisation,
                           experience_min, niveau_souhaite
                    FROM offres
                    WHERE id = ANY(%s)
                """
            
            cur.execute(query, (ids,))
            rows = cur.fetchall()
            
            for row in rows:
                doc_id = str(row[0])
                
                results.append({
                    "id": row[0],
                    "doc_id": doc_id,
                    "nom": row[1],
                    "tags": row[2] if row[2] else [],
                    "localisation": row[3],
                    "experience": row[4],
                    "niveau": row[5],
                    "score_bm25": scores[doc_id],
                    "source": "postgresql",
                    "source_type": "systeme"
                })
            
            cur.close()
            
        except Exception as e:
            print(f"❌ Erreur fetch PostgreSQL: {e}")
        
        return results
    
    def _fetch_whoosh_results(
        self,
        scores: Dict[str, float],
        target: str
    ) -> List[Dict]:
        """Récupère détails documents Whoosh"""
        results = []
        
        if not scores:
            return results
        
        index = self.whoosh_cv_index if target == "cvs" else self.whoosh_job_index
        
        if not index:
            return results
        
        try:
            with index.searcher() as searcher:
                for doc_id, score in scores.items():
                    from whoosh.qparser import QueryParser
                    parser = QueryParser("doc_id", index.schema)
                    query = parser.parse(doc_id)
                    
                    hits = searcher.search(query, limit=1)
                    
                    if len(hits) > 0:
                        hit = hits[0]
                        
                        results.append({
                            "id": doc_id,
                            "doc_id": doc_id,
                            "nom": hit.get("nom", ""),
                            "tags": hit.get("competences", "").split(","),
                            "localisation": hit.get("localisation", ""),
                            "experience": hit.get("annees", 0),
                            "niveau": "",
                            "score_bm25": score,
                            "source": "whoosh",
                            "source_type": "uploaded"
                        })
        
        except Exception as e:
            print(f"❌ Erreur fetch Whoosh: {e}")
        
        return results
    
    def get_index_stats(self) -> Dict:
        """Retourne statistiques de tous les index BM25"""
        return {
            "cvs_postgresql": self.bm25_cv_pg.get_stats(),
            "cvs_whoosh": self.bm25_cv_whoosh.get_stats(),
            "jobs_postgresql": self.bm25_job_pg.get_stats(),
            "jobs_whoosh": self.bm25_job_whoosh.get_stats()
        }


# Fonction utilitaire pour tests
def test_vectoriel_search():
    """Test rapide du modèle vectoriel"""
    
    print("="*80)
    print("TEST MODÈLE VECTORIEL BM25")
    print("="*80)
    
    model = VectorielSearchModel()
    
    # Test 1: Recherche simple
    print("\n📝 Test 1: Recherche 'développeur python django'")
    result = model.search("développeur python django", target="cvs", top_k=5)
    
    print(f"\n✅ Résultats: {result['stats']['total_results']}")
    print(f"   Top K: {result['stats']['top_k']}")
    print(f"   Query tokens: {result['stats']['query_tokens']}")
    
    print("\n🏆 Top 5:")
    for i, res in enumerate(result['results'][:5], 1):
        print(f"   {i}. {res['nom']} - Score: {res['score_bm25']} - Source: {res['source_type']}")
    
    # Statistiques index
    print("\n📊 Statistiques Index BM25:")
    stats = model.get_index_stats()
    for key, val in stats.items():
        print(f"   {key}: {val}")


if __name__ == "__main__":
    test_vectoriel_search()
