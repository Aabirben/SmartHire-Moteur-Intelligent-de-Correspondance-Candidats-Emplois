"""
============================================================================
SMARTHIRE - Filter Processor (CORRIGÉ)
Gestion intelligente des filtres avec logique OR/AND
CORRECTION: annees_experience au lieu de annees
============================================================================
"""

import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# ========================================================
# CLASSE PRINCIPALE
# ========================================================
class FilterProcessor:
    """
    Traite les filtres selon les règles :
    1. Un filtre avec plusieurs valeurs → OR
       location: ["casa", "rabat"] → casa OR rabat
    
    2. Plusieurs filtres → AND
       experience: [5,10] AND location: ["casa"]
    """
    
    def __init__(self):
        self.supported_filters = {
            "skills",
            "location", 
            "experience",
            "level",
            "contract_type",
            "diploma",
            "remote"
        }
    
    def process(self, filters: Dict[str, Any],target: str = "cvs") -> Dict:
        """
        Traite et structure les filtres
        
        Returns:
            {
                "boolean_filters": {...},
                "range_filters": {...},
                "sql_conditions": {...}
            }
        """
        if not filters:
            return self._empty_result()
        
        result = {
            "boolean_filters": {},
            "range_filters": {},
            "sql_conditions": {},
            "whoosh_queries": []
        }
        
        # Traiter chaque filtre
        for filter_name, filter_value in filters.items():
            if filter_name not in self.supported_filters:
                logger.warning(f"⚠️ Filtre non supporté ignoré: {filter_name}")
                continue
            
            if filter_name == "skills":
                self._process_skills(filter_value, result)
            elif filter_name == "location":
                self._process_location(filter_value, result)
            elif filter_name == "experience":
                self._process_experience(filter_value, result)
            elif filter_name == "level":
                self._process_level(filter_value, result)
            elif filter_name == "contract_type":
                self._process_contract_type(filter_value, result)
            elif filter_name == "diploma":
                self._process_diploma(filter_value, result)
            elif filter_name == "remote":
                self._process_remote(filter_value, result)
        
        # Générer SQL/Whoosh
        self._generate_sql(result, target)
        self._generate_whoosh(result)
        
        return result
    
    # ========================================================
    # TRAITEMENT PAR TYPE
    # ========================================================
    def _process_skills(self, value: Any, result: Dict):
        """Traite filtre compétences"""
        if isinstance(value, list):
            result["boolean_filters"]["skills_or"] = [s.lower() for s in value]
        elif isinstance(value, dict):
            if "required" in value:
                result["boolean_filters"]["skills_and"] = [
                    s.lower() for s in value["required"]
                ]
            if "optional" in value:
                result["boolean_filters"]["skills_or"] = [
                    s.lower() for s in value.get("optional", [])
                ]
    
    def _process_location(self, value: Any, result: Dict):
        """Traite filtre localisation"""
        if isinstance(value, str):
            result["boolean_filters"]["location_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["location_or"] = [
                loc.lower() for loc in value
            ]
    
    def _process_experience(self, value: Any, result: Dict):
        """Traite filtre expérience"""
        if isinstance(value, list) and len(value) == 2:
            result["range_filters"]["experience"] = tuple(value)
        elif isinstance(value, int):
            result["range_filters"]["experience"] = (value, 100)
    
    def _process_level(self, value: Any, result: Dict):
        """Traite filtre niveau"""
        if isinstance(value, str):
            result["boolean_filters"]["level_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["level_or"] = [
                lvl.lower() for lvl in value
            ]
    
    def _process_contract_type(self, value: Any, result: Dict):
        """Traite filtre type contrat"""
        if isinstance(value, str):
            result["boolean_filters"]["contract_type_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["contract_type_or"] = [
                ct.lower() for ct in value
            ]
    
    def _process_diploma(self, value: Any, result: Dict):
        """Traite filtre diplôme"""
        if isinstance(value, str):
            result["boolean_filters"]["diploma_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["diploma_or"] = [
                dip.lower() for dip in value
            ]
    
    def _process_remote(self, value: Any, result: Dict):
        """Traite filtre remote"""
        if isinstance(value, bool) and value:
            result["boolean_filters"]["remote"] = True
            
            if "location_or" in result["boolean_filters"]:
                if "remote" not in [loc.lower() for loc in result["boolean_filters"]["location_or"]]:
                    result["boolean_filters"]["location_or"].append("remote")
            else:
                result["boolean_filters"]["location_or"] = ["remote"]
        else:
            result["boolean_filters"]["remote"] = False
    
    # ========================================================
    # GÉNÉRATION SQL (CORRIGÉ)
    # ========================================================
    def _generate_sql(self, result: Dict,target: str = "cvs"):
        """
        Génère les conditions SQL pour PostgreSQL
        
        ✅ CORRECTION: Utilise annees_experience au lieu de annees
        """
        conditions = []
        params = []
        
        bool_filters = result["boolean_filters"]
        
        # 1. Compétences (OR)
        if "skills_or" in bool_filters:
            placeholders = " OR ".join([
                "%s = ANY(tags_manuels)" 
                for _ in bool_filters["skills_or"]
            ])
            conditions.append(f"({placeholders})")
            params.extend(bool_filters["skills_or"])
        
        # 2. Compétences (AND) - requises
        if "skills_and" in bool_filters:
            for skill in bool_filters["skills_and"]:
                conditions.append("%s = ANY(tags_manuels)")
                params.append(skill)
        
        # 3. Localisation (OR)
        if "location_or" in bool_filters:
            placeholders = " OR ".join([
                "LOWER(localisation) LIKE %s" 
                for _ in bool_filters["location_or"]
            ])
            conditions.append(f"({placeholders})")
            params.extend([f"%{loc}%" for loc in bool_filters["location_or"]])
        
        # 4. Niveau (OR)
        if "level_or" in bool_filters:
            placeholders = " OR ".join([
                "LOWER(niveau_estime) = %s" 
                for _ in bool_filters["level_or"]
            ])
            conditions.append(f"({placeholders})")
            params.extend(bool_filters["level_or"])
        
        # 5. Type contrat (OR)
        if "contract_type_or" in bool_filters:
            placeholders = " OR ".join([
                "LOWER(type_contrat) = %s" 
                for _ in bool_filters["contract_type_or"]
            ])
            conditions.append(f"({placeholders})")
            params.extend(bool_filters["contract_type_or"])
        
        # ✅ 6. Expérience (CORRIGÉ: annees_experience)
        if "experience" in result["range_filters"]:
            min_exp, max_exp = result["range_filters"]["experience"]
            if target == "cvs":
                 # Pour la table cvs
               conditions.append("annees_experience >= %s")
               conditions.append("annees_experience <= %s")
            else:
                # Pour la table offres
                conditions.append("experience_min >= %s")
                conditions.append("experience_min <= %s")
            
            params.extend([min_exp, max_exp])

        
        # 7. Remote
        if bool_filters.get("remote") == True:
            has_remote_in_location = False
            if "location_or" in bool_filters:
                for loc in bool_filters["location_or"]:
                    if "remote" in loc.lower():
                        has_remote_in_location = True
                        break
            
            if not has_remote_in_location:
                conditions.append("(LOWER(localisation) LIKE %s OR LOWER(localisation) LIKE %s OR LOWER(type_contrat) LIKE %s)")
                params.extend(["%remote%", "%télétravail%", "%télétravail%"])
        
        # Combiner avec AND
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        result["sql_conditions"] = {
            "where": where_clause,
            "params": params
        }
    
    def _generate_whoosh(self, result: Dict):
        """Génère les requêtes Whoosh"""
        whoosh_terms = {
            "skills_or": result["boolean_filters"].get("skills_or", []),
            "skills_and": result["boolean_filters"].get("skills_and", []),
            "location_or": result["boolean_filters"].get("location_or", []),
            "level_or": result["boolean_filters"].get("level_or", []),
            "remote": result["boolean_filters"].get("remote", False)
        }
        
        result["whoosh_queries"] = whoosh_terms
    
    def _empty_result(self) -> Dict:
        """Résultat vide"""
        return {
            "boolean_filters": {},
            "range_filters": {},
            "sql_conditions": {"where": "TRUE", "params": []},
            "whoosh_queries": {}
        }
    
    # ========================================================
    # VALIDATION
    # ========================================================
    def validate(self, filters: Dict) -> Tuple[bool, List[str]]:
        """Valide les filtres"""
        errors = []
        
        if not filters:
            return True, []
        
        if "experience" in filters:
            exp = filters["experience"]
            if isinstance(exp, list):
                if len(exp) != 2:
                    errors.append("experience doit avoir exactement 2 valeurs [min, max]")
                elif exp[0] > exp[1]:
                    errors.append("experience: min > max")
                elif exp[0] < 0:
                    errors.append("experience: valeur négative")
        
        if "remote" in filters:
            remote_val = filters["remote"]
            if not isinstance(remote_val, bool):
                errors.append("remote doit être un booléen (True/False)")
        
        for key in filters.keys():
            if key not in self.supported_filters:
                errors.append(f"Filtre non supporté: {key}")
        
        return len(errors) == 0, errors


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🔍 TEST FILTER PROCESSOR (CORRIGÉ)")
    print("="*80)
    
    processor = FilterProcessor()
    
    filters1 = {
        "skills": ["python", "java"],
        "location": ["casablanca", "rabat"],
        "experience": [5, 10],
        "remote": True
    }
    result1 = processor.process(filters1)
    
    print(f"Input: {filters1}")
    print(f"\nSQL WHERE: {result1['sql_conditions']['where']}")
    print(f"SQL PARAMS: {result1['sql_conditions']['params']}")
    print("\n✅ La requête SQL utilise maintenant 'annees_experience' correctement!")