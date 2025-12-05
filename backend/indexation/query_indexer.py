"""
============================================================================
SMARTHIRE - Query System Modulaire Complet
Validation + Auto-Correction + Indexation
============================================================================
"""

import os
import json
import re
import logging
import shutil
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC, DATETIME, KEYWORD
from whoosh.writing import AsyncWriter

from backend.config.settings import QUERY_INDEX

logger = logging.getLogger(__name__)

# ========================================================
# CONSTANTES
# ========================================================
MAX_QUERY_LENGTH = 500
MIN_QUERY_LENGTH = 1
MAX_PARENTHESIS_DEPTH = 10

# ========================================================
# MODULE 1: SCHÉMA ET INITIALISATION
# ========================================================
class QueryIndexSchema:
    """Gestion du schéma Whoosh"""
    
    @staticmethod
    def get_schema():
        """Schéma complet avec validation et correction"""
        return Schema(
            id=ID(stored=True, unique=True),
            
            # Requête
            query_original=TEXT(stored=True),
            query_corrected=TEXT(stored=True),  # Après auto-correction
            query_processed=TEXT(stored=True),  # Après prétraitement
            query_type=KEYWORD(stored=True),
            
            # Validation
            query_valid=KEYWORD(stored=True),
            validation_errors=TEXT(stored=True),
            
            # Correction
            corrections_applied=TEXT(stored=True),  # JSON
            
            # Filtres
            filters_json=TEXT(stored=True),
            filter_keys=KEYWORD(stored=True, commas=True),
            
            # Métadonnées
            search_type=KEYWORD(stored=True),
            nb_resultats=NUMERIC(stored=True),
            timestamp=DATETIME(stored=True),
            user_id=ID(stored=True),
            session_id=ID(stored=True)
        )


class QueryIndexManager:
    """Gestion de l'index Whoosh"""
    
    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or str(QUERY_INDEX)
    
    def migrate_if_needed(self) -> bool:
        """Migre l'ancien schéma si nécessaire"""
        if not index.exists_in(self.index_dir):
            return False
        
        try:
            idx = index.open_dir(self.index_dir)
            schema_fields = set(idx.schema.names())
            
            required_fields = {'query_valid', 'validation_errors', 'query_corrected', 'corrections_applied'}
            if not required_fields.issubset(schema_fields):
                logger.warning("⚠️  Migration nécessaire - Ancien schéma détecté")
                
                backup_dir = f"{self.index_dir}_backup_{int(datetime.now().timestamp())}"
                shutil.copytree(self.index_dir, backup_dir)
                logger.info(f"✅ Backup créé: {backup_dir}")
                
                shutil.rmtree(self.index_dir)
                logger.info("🗑️  Ancien index supprimé")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur migration: {e}")
            return False
    
    def init_index(self, force_recreate: bool = False):
        """Initialise ou ouvre l'index"""
        if force_recreate and os.path.exists(self.index_dir):
            backup_dir = f"{self.index_dir}_backup_{int(datetime.now().timestamp())}"
            shutil.copytree(self.index_dir, backup_dir)
            shutil.rmtree(self.index_dir)
            logger.info(f"✅ Ancien index sauvegardé: {backup_dir}")
        
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            logger.info(f"📁 Dossier créé: {self.index_dir}")
        
        self.migrate_if_needed()
        
        if not index.exists_in(self.index_dir):
            schema = QueryIndexSchema.get_schema()
            index.create_in(self.index_dir, schema)
            logger.info(f"✅ Nouvel index créé: {self.index_dir}")
        
        return index.open_dir(self.index_dir)


# ========================================================
# MODULE 2: VALIDATION
# ========================================================
class QueryValidator:
    """Validation des requêtes et filtres"""
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, List[str]]:
        """Valide une requête"""
        errors = []
        
        if not query or not query.strip():
            errors.append("EMPTY_QUERY")
            return False, errors
        
        if len(query) > MAX_QUERY_LENGTH:
            errors.append(f"QUERY_TOO_LONG:>{MAX_QUERY_LENGTH}")
        
        if len(query.strip()) < MIN_QUERY_LENGTH:
            errors.append(f"QUERY_TOO_SHORT:<{MIN_QUERY_LENGTH}")
        
        errors.extend(QueryValidator._check_parentheses(query))
        errors.extend(QueryValidator._check_operators(query))
        
        if QueryValidator._contains_dangerous_patterns(query):
            errors.append("DANGEROUS_PATTERN")
        
        depth = QueryValidator._get_parenthesis_depth(query)
        if depth > MAX_PARENTHESIS_DEPTH:
            errors.append(f"PARENTHESIS_TOO_DEEP:>{MAX_PARENTHESIS_DEPTH}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _check_parentheses(query: str) -> List[str]:
        """Vérifie les parenthèses"""
        errors = []
        stack = []
        
        for i, char in enumerate(query):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if not stack:
                    errors.append(f"UNMATCHED_CLOSING_PAREN:pos_{i}")
                else:
                    stack.pop()
        
        if stack:
            errors.append(f"UNMATCHED_OPENING_PAREN:{len(stack)}_unclosed")
        
        if re.search(r'\(\s*\)', query):
            errors.append("EMPTY_PARENTHESES")
        
        return errors
    
    @staticmethod
    def _check_operators(query: str) -> List[str]:
        """Vérifie les opérateurs booléens"""
        errors = []
        query_upper = query.upper()
        
        if re.match(r'^\s*(AND|OR|NOT)\b', query_upper):
            errors.append("OPERATOR_AT_START")
        
        if re.search(r'\b(AND|OR)\s*$', query_upper):
            errors.append("OPERATOR_AT_END")
        
        if re.search(r'\b(AND|OR|NOT)\s+(AND|OR)\b', query_upper):
            errors.append("CONSECUTIVE_OPERATORS")
        
        if re.search(r'\bNOT\s*$', query_upper):
            errors.append("ISOLATED_NOT")
        
        if re.search(r'\w(AND|OR|NOT)\w', query_upper):
            errors.append("OPERATOR_NO_SPACE")
        
        return errors
    
    @staticmethod
    def _get_parenthesis_depth(query: str) -> int:
        """Calcule la profondeur des parenthèses"""
        max_depth = current_depth = 0
        for char in query:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        return max_depth
    
    @staticmethod
    def _contains_dangerous_patterns(query: str) -> bool:
        """Détecte les patterns dangereux"""
        patterns = [
            r'<script', r'javascript:', r'DROP\s+TABLE',
            r';\s*--', r'\bexec\b', r'\beval\b', r'\.\./', r'\\\\'
        ]
        query_lower = query.lower()
        return any(re.search(p, query_lower, re.IGNORECASE) for p in patterns)
    
    @staticmethod
    def validate_filters(filters: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Valide les filtres"""
        errors = []
        if not filters:
            return True, []
        
        if "experience" in filters:
            exp = filters["experience"]
            if isinstance(exp, list) and len(exp) == 2:
                min_exp, max_exp = exp
                if min_exp > max_exp:
                    errors.append("EXPERIENCE_MIN_GT_MAX")
                if min_exp < 0:
                    errors.append("EXPERIENCE_NEGATIVE_MIN")
                if max_exp < 0:
                    errors.append("EXPERIENCE_NEGATIVE_MAX")
                if max_exp > 100:
                    errors.append("EXPERIENCE_MAX_UNREALISTIC")
        
        if "salary" in filters:
            sal = filters["salary"]
            if isinstance(sal, list) and len(sal) == 2:
                min_sal, max_sal = sal
                if min_sal > max_sal:
                    errors.append("SALARY_MIN_GT_MAX")
                if min_sal < 0:
                    errors.append("SALARY_NEGATIVE_MIN")
                if max_sal < 0:
                    errors.append("SALARY_NEGATIVE_MAX")
        
        if "remote" in filters:
            if not isinstance(filters["remote"], bool):
                errors.append("REMOTE_NOT_BOOLEAN")
        
        for key, value in filters.items():
            if isinstance(value, list):
                if len(value) != len(set(str(v).lower() for v in value)):
                    errors.append(f"DUPLICATES_IN_{key.upper()}")
        
        return len(errors) == 0, errors


# ========================================================
# MODULE 3: AUTO-CORRECTION
# ========================================================
class QueryCorrector:
    """Auto-correction des requêtes mal formées"""
    
    @staticmethod
    def autocorrect(query: str) -> Tuple[str, List[str]]:
        """Corrige automatiquement une requête"""
        if not query or not query.strip():
            return "", ["EMPTY_QUERY_REMOVED"]
        
        corrections = []
        corrected = query.strip()
        
        corrected, ops_removed = QueryCorrector._remove_leading_trailing_operators(corrected)
        corrections.extend(ops_removed)
        
        corrected, ops_merged = QueryCorrector._merge_consecutive_operators(corrected)
        corrections.extend(ops_merged)
        
        corrected, parens_fixed = QueryCorrector._fix_parentheses(corrected)
        corrections.extend(parens_fixed)
        
        corrected, empty_removed = QueryCorrector._remove_empty_parentheses(corrected)
        corrections.extend(empty_removed)
        
        corrected = re.sub(r'\s+', ' ', corrected).strip()
        
        if not corrected:
            return "", ["QUERY_BECAME_EMPTY_AFTER_CORRECTION"]
        
        if corrections:
            logger.info(f"🔧 Auto-correction: {query} → {corrected}")
            logger.info(f"   Corrections: {corrections}")
        
        return corrected, corrections
    
    @staticmethod
    def _remove_leading_trailing_operators(query: str) -> Tuple[str, List[str]]:
        """Supprime les opérateurs en début/fin"""
        corrections = []
        original = query
        
        query = re.sub(r'^\s*(AND|OR)\s+', '', query, flags=re.IGNORECASE)
        if query != original:
            corrections.append("REMOVED_LEADING_OPERATOR")
            original = query
        
        query = re.sub(r'\s+(AND|OR|NOT)\s*$', '', query, flags=re.IGNORECASE)
        if query != original:
            corrections.append("REMOVED_TRAILING_OPERATOR")
        
        return query, corrections
    
    @staticmethod
    def _merge_consecutive_operators(query: str) -> Tuple[str, List[str]]:
        """Fusionne les opérateurs consécutifs"""
        corrections = []
        original = query
        
        query = re.sub(r'\b(AND)\s+(AND\s+)+', r'\1 ', query, flags=re.IGNORECASE)
        query = re.sub(r'\b(OR)\s+(OR\s+)+', r'\1 ', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOT\s+NOT\s+', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\b(AND)\s+(OR)\s+', r'\1 ', query, flags=re.IGNORECASE)
        query = re.sub(r'\b(OR)\s+(AND)\s+', r'\1 ', query, flags=re.IGNORECASE)
        
        if query != original:
            corrections.append("MERGED_CONSECUTIVE_OPERATORS")
        
        return query, corrections
    
    @staticmethod
    def _fix_parentheses(query: str) -> Tuple[str, List[str]]:
        """Corrige les parenthèses déséquilibrées"""
        corrections = []
        
        open_count = query.count('(')
        close_count = query.count(')')
        
        if open_count == close_count:
            return query, corrections
        
        if open_count > close_count:
            diff = open_count - close_count
            for _ in range(diff):
                query = re.sub(r'\((?![^(]*\))', '', query, count=1)
            corrections.append(f"REMOVED_{diff}_UNCLOSED_OPENING_PAREN")
        
        elif close_count > open_count:
            diff = close_count - open_count
            for _ in range(diff):
                query = re.sub(r'(?<!\()\)', '', query, count=1)
            corrections.append(f"REMOVED_{diff}_UNMATCHED_CLOSING_PAREN")
        
        return query, corrections
    
    @staticmethod
    def _remove_empty_parentheses(query: str) -> Tuple[str, List[str]]:
        """Supprime les parenthèses vides"""
        corrections = []
        original = query
        
        query = re.sub(r'\(\s*\)', '', query)
        query = re.sub(r'\s+(AND|OR)\s*$', '', query, flags=re.IGNORECASE)
        query = re.sub(r'^\s*(AND|OR)\s+', '', query, flags=re.IGNORECASE)
        
        if query != original:
            corrections.append("REMOVED_EMPTY_PARENTHESES")
        
        return query, corrections
    
    @staticmethod
    def fallback_to_simple(query: str) -> str:
        """Convertit en requête simple (dernier recours)"""
        simple = re.sub(r'\b(AND|OR|NOT)\b', ' ', query, flags=re.IGNORECASE)
        simple = re.sub(r'[()]', ' ', simple)
        simple = re.sub(r'\s+', ' ', simple).strip()
        
        logger.info(f"🔄 Fallback simple: {query} → {simple}")
        return simple
    
    @staticmethod
    def extract_terms(query: str) -> List[str]:
        """Extrait les termes significatifs"""
        cleaned = re.sub(r'\b(AND|OR|NOT)\b', ' ', query, flags=re.IGNORECASE)
        cleaned = re.sub(r'[()]', ' ', cleaned)
        terms = [t.strip() for t in cleaned.split() if t.strip()]
        return terms


# ========================================================
# MODULE 4: PRÉTRAITEMENT
# ========================================================
class QueryProcessor:
    """Prétraitement et nettoyage des requêtes"""
    
    @staticmethod
    def clean(query: str) -> str:
        """Nettoyage de base"""
        if not query:
            return ""
        
        query = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', query)
        query = re.sub(r'[\u200b-\u200d\ufeff]', '', query)
        query = re.sub(r'\s+', ' ', query)
        
        return query.strip()
    
    @staticmethod
    def preprocess(query: str, preserve_operators: bool = True) -> str:
        """Prétraitement complet"""
        if not query:
            return ""
        
        processed = query
        
        if preserve_operators:
            bool_operators = {
                'AND': '__AND__',
                'OR': '__OR__',
                'NOT': '__NOT__'
            }
            
            for operator, placeholder in bool_operators.items():
                pattern = rf'\b{operator}\b'
                processed = re.sub(pattern, placeholder, processed, flags=re.IGNORECASE)
        
        processed = processed.lower()
        processed = re.sub(r'[^a-z0-9àâäéèêëîïôöùûüç\s\-_()]', ' ', processed)
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        if preserve_operators:
            for operator, placeholder in bool_operators.items():
                processed = processed.replace(placeholder.lower(), f' {operator} ')
            
            processed = re.sub(r'\s+', ' ', processed).strip()
        
        return processed
    
    @staticmethod
    def normalize_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalise les filtres"""
        if not filters:
            return {}
        
        normalized = {}
        
        for key, value in filters.items():
            if value is None:
                continue
            
            if isinstance(value, list) and len(value) == 0:
                continue
            
            if isinstance(value, list):
                seen = set()
                deduped = []
                for item in value:
                    key_item = str(item).lower() if isinstance(item, str) else item
                    if key_item not in seen:
                        seen.add(key_item)
                        deduped.append(item)
                normalized[key] = deduped
            else:
                normalized[key] = value
        
        return normalized
    
    @staticmethod
    def detect_type(query: str) -> str:
        """Détecte le type de requête"""
        if not query:
            return "simple"
        
        query_upper = query.upper()
        patterns = [r'\bAND\b', r'\bOR\b', r'\bNOT\b', r'\(', r'\)']
        
        for pattern in patterns:
            if re.search(pattern, query_upper):
                return "boolean"
        
        return "simple"
    
    @staticmethod
    def extract_filter_keys(filters: Optional[Dict[str, Any]]) -> List[str]:
        """Extrait les clés de filtres"""
        if not filters:
            return []
        
        keys = []
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, list) and len(value) > 0:
                    keys.append(key)
                elif not isinstance(value, list):
                    keys.append(key)
        
        return keys


# ========================================================
# MODULE 5: INDEXATION PRINCIPALE
# ========================================================
class QueryIndexer:
    """Système d'indexation complet"""
    
    def __init__(self, index_dir: str = None):
        self.manager = QueryIndexManager(index_dir)
        self.validator = QueryValidator()
        self.corrector = QueryCorrector()
        self.processor = QueryProcessor()
    
    def index_query(
        self,
        query_text: str,
        search_type: str,
        nb_resultats: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        skip_validation: bool = False,
        skip_correction: bool = False
    ) -> Dict[str, Any]:
        """
        Indexe une requête avec validation et auto-correction
        
        Returns:
            {
                "doc_id": str,
                "query_original": str,
                "query_corrected": str,
                "query_processed": str,
                "is_valid": bool,
                "errors": List[str],
                "corrections": List[str]
            }
        """
        try:
            # Initialisation
            idx = self.manager.init_index()
            
            # ÉTAPE 1: Nettoyage
            query_cleaned = self.processor.clean(query_text) if query_text else ""
            filters_normalized = self.processor.normalize_filters(filters)
            
            # ÉTAPE 2: Auto-correction (si activée)
            query_corrected = query_cleaned
            corrections = []
            
            if not skip_correction:
                query_corrected, corrections = self.corrector.autocorrect(query_cleaned)
            
            # ÉTAPE 3: Validation
            query_valid = True
            validation_errors = []
            
            if not skip_validation:
                query_valid, validation_errors = self.validator.validate_query(query_corrected)
                filter_valid, filter_errors = self.validator.validate_filters(filters_normalized)
                
                if not filter_valid:
                    validation_errors.extend(filter_errors)
                    query_valid = False
            
            # ÉTAPE 4: Détection type et prétraitement
            query_type = self.processor.detect_type(query_corrected)
            preserve_ops = (query_type == "boolean")
            query_processed = self.processor.preprocess(query_corrected, preserve_operators=preserve_ops)
            
            # ÉTAPE 5: Préparation des données
            filters_json = json.dumps(filters_normalized, ensure_ascii=False)
            filter_keys = self.processor.extract_filter_keys(filters_normalized)
            filter_keys_str = ",".join(filter_keys) if filter_keys else ""
            
            doc_id = f"{datetime.now(timezone.utc).timestamp()}"
            
            # ÉTAPE 6: Indexation
            writer = AsyncWriter(idx)
            writer.add_document(
                id=doc_id,
                query_original=query_text or "",
                query_corrected=query_corrected,
                query_processed=query_processed,
                query_type=query_type,
                query_valid="valid" if query_valid else "invalid",
                validation_errors=json.dumps(validation_errors, ensure_ascii=False),
                corrections_applied=json.dumps(corrections, ensure_ascii=False),
                filters_json=filters_json,
                filter_keys=filter_keys_str,
                search_type=search_type,
                nb_resultats=nb_resultats,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id or "",
                session_id=session_id or ""
            )
            writer.commit()
            
            # ÉTAPE 7: Logging
            if query_valid:
                logger.info(f"✅ Requête VALIDE indexée: {doc_id}")
            else:
                logger.warning(f"⚠️  Requête INVALIDE indexée: {doc_id}")
                logger.warning(f"   Erreurs: {validation_errors}")
            
            if corrections:
                logger.info(f"   🔧 Corrections: {corrections}")
            
            logger.info(f"   📝 Original: {query_text}")
            logger.info(f"   🔄 Corrigée: {query_corrected}")
            logger.info(f"   💾 Processed: {query_processed}")
            logger.info(f"   🏷️  Type: {query_type}")
            logger.info(f"   🔍 Search: {search_type}")
            logger.info(f"   🎯 Filtres: {filter_keys}")
            logger.info(f"   📊 Résultats: {nb_resultats}")
            
            return {
                "doc_id": doc_id,
                "query_original": query_text,
                "query_corrected": query_corrected,
                "query_processed": query_processed,
                "is_valid": query_valid,
                "errors": validation_errors,
                "corrections": corrections
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur indexation: {e}")
            logger.exception(e)
            return {
                "doc_id": "",
                "query_original": query_text,
                "query_corrected": "",
                "query_processed": "",
                "is_valid": False,
                "errors": [str(e)],
                "corrections": []
            }


# ========================================================
# API PUBLIQUE
# ========================================================
def indexer_requete(
    query_text: str,
    search_type: str,
    nb_resultats: int = 0,
    filters: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    skip_validation: bool = False,
    skip_correction: bool = False
) -> str:
    """
    Fonction principale d'indexation (API publique)
    
    Returns:
        doc_id (str)
    """
    indexer = QueryIndexer()
    result = indexer.index_query(
        query_text, search_type, nb_resultats, filters,
        user_id, session_id, skip_validation, skip_correction
    )
    return result["doc_id"]


def prepare_query_for_search(
    query: str,
    auto_correct: bool = True
) -> Tuple[str, List[str]]:
    """
    Prépare une requête pour la recherche
    
    Returns:
        (query_corrigée, corrections_appliquées)
    """
    corrector = QueryCorrector()
    
    if auto_correct:
        return corrector.autocorrect(query)
    else:
        processor = QueryProcessor()
        return processor.clean(query), []


# ========================================================
# TESTS
# ========================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*80)
    print("🔥 TESTS DU SYSTÈME MODULAIRE COMPLET")
    print("="*80)
    
    indexer = QueryIndexer()
    
    test_cases = [
        ("Python Developer", "job", 25, None),
        ("AND Python", "job", 15, None),
        ("Python AND AND Django", "job", 8, None),
        ("(Python AND Django", "job", 12, None),
        ("Python OR", "job", 5, None),
        ("", "job", 0, None),
        ("Python Developer", "job", 10, {"experience": [10, 5]}),
    ]
    
    for query, search_type, nb_res, filters in test_cases:
        print(f"\n{'─'*80}")
        print(f"Test: '{query}'")
        print("─"*80)
        
        result = indexer.index_query(
            query_text=query,
            search_type=search_type,
            nb_resultats=nb_res,
            filters=filters
        )
        
        print(f"ID: {result['doc_id']}")
        print(f"Valide: {result['is_valid']}")
        print(f"Corrigée: {result['query_corrected']}")
        print(f"Corrections: {result['corrections']}")
        print(f"Erreurs: {result['errors']}")
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)