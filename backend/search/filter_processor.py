"""
============================================================================
SMARTHIRE - Filter Processor
Gestion intelligente des filtres avec logique OR/AND
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
    
    Exemples:
        filters = {
            "skills": ["python", "java"],        # python OR java
            "location": ["casa", "rabat"],       # casa OR rabat  
            "experience": [5, 10]                # 5 <= exp <= 10
        }
        → (python OR java) AND (casa OR rabat) AND (5 <= exp <= 10)
    """
    
    def __init__(self):
        self.supported_filters = {
            "skills",
            "location", 
            "experience",
            "level",
            "contract_type",
            "diploma"
        }
    
    def process(self, filters: Dict[str, Any]) -> Dict:
        """
        Traite et structure les filtres
        
        Returns:
            {
                "boolean_filters": {
                    "skills_or": ["python", "java"],
                    "location_or": ["casa", "rabat"]
                },
                "range_filters": {
                    "experience": (5, 10)
                },
                "sql_conditions": {
                    "postgresql": "...",
                    "whoosh": "..."
                }
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
            
            # Dispatcher selon le type
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
        
        # Générer SQL/Whoosh
        self._generate_sql(result)
        self._generate_whoosh(result)
        
        return result
    
    # ========================================================
    # TRAITEMENT PAR TYPE
    # ========================================================
    def _process_skills(self, value: Any, result: Dict):
        """
        Traite filtre compétences
        
        Cas 1: Liste → OR
            ["python", "java"] → python OR java
        
        Cas 2: Dict avec required/optional
            {"required": ["python"], "optional": ["java"]}
        """
        if isinstance(value, list):
            # Liste simple → OR
            result["boolean_filters"]["skills_or"] = [s.lower() for s in value]
        
        elif isinstance(value, dict):
            # Dict structuré
            if "required" in value:
                result["boolean_filters"]["skills_and"] = [
                    s.lower() for s in value["required"]
                ]
            if "optional" in value:
                result["boolean_filters"]["skills_or"] = [
                    s.lower() for s in value.get("optional", [])
                ]
    
    def _process_location(self, value: Any, result: Dict):
        """
        Traite filtre localisation (toujours OR)
        
        ["casa", "rabat"] → casa OR rabat
        """
        if isinstance(value, str):
            result["boolean_filters"]["location_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["location_or"] = [
                loc.lower() for loc in value
            ]
    
    def _process_experience(self, value: Any, result: Dict):
        """
        Traite filtre expérience (range)
        
        [5, 10] → 5 <= experience <= 10
        5 → experience >= 5
        """
        if isinstance(value, list) and len(value) == 2:
            result["range_filters"]["experience"] = tuple(value)
        elif isinstance(value, int):
            result["range_filters"]["experience"] = (value, 100)
    
    def _process_level(self, value: Any, result: Dict):
        """
        Traite filtre niveau (OR si liste)
        
        ["senior", "expert"] → senior OR expert
        """
        if isinstance(value, str):
            result["boolean_filters"]["level_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["level_or"] = [
                lvl.lower() for lvl in value
            ]
    
    def _process_contract_type(self, value: Any, result: Dict):
        """
        Traite filtre type contrat (OR si liste)
        
        ["cdi", "cdd"] → cdi OR cdd
        """
        if isinstance(value, str):
            result["boolean_filters"]["contract_type_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["contract_type_or"] = [
                ct.lower() for ct in value
            ]
    
    def _process_diploma(self, value: Any, result: Dict):
        """
        Traite filtre diplôme (OR si liste)
        """
        if isinstance(value, str):
            result["boolean_filters"]["diploma_or"] = [value.lower()]
        elif isinstance(value, list):
            result["boolean_filters"]["diploma_or"] = [
                dip.lower() for dip in value
            ]
    
    # ========================================================
    # GÉNÉRATION SQL
    # ========================================================
    def _generate_sql(self, result: Dict):
        """
        Génère les conditions SQL pour PostgreSQL
        
        Logique:
        - Chaque filtre avec _or → ANY(array)
        - Combinaison des filtres → AND
        """
        conditions = []
        params = []
        
        bool_filters = result["boolean_filters"]
        
        # 1. Compétences (OR)
        if "skills_or" in bool_filters:
            # Au moins une compétence
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
        
        # 6. Expérience (range)
        if "experience" in result["range_filters"]:
            min_exp, max_exp = result["range_filters"]["experience"]
            conditions.append("annees_experience >= %s")
            conditions.append("annees_experience <= %s")
            params.extend([min_exp, max_exp])
        
        # Combiner avec AND
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        result["sql_conditions"] = {
            "where": where_clause,
            "params": params
        }
    
    def _generate_whoosh(self, result: Dict):
        """
        Génère les requêtes Whoosh
        
        Note: Whoosh utilise sa propre syntaxe Query
        On stocke juste les termes ici, la construction Query
        sera faite dans boolean_search.py
        """
        whoosh_terms = {
            "skills_or": result["boolean_filters"].get("skills_or", []),
            "skills_and": result["boolean_filters"].get("skills_and", []),
            "location_or": result["boolean_filters"].get("location_or", []),
            "level_or": result["boolean_filters"].get("level_or", [])
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
        """
        Valide les filtres
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        if not filters:
            return True, []
        
        # Vérifier types
        if "experience" in filters:
            exp = filters["experience"]
            if isinstance(exp, list):
                if len(exp) != 2:
                    errors.append("experience doit avoir exactement 2 valeurs [min, max]")
                elif exp[0] > exp[1]:
                    errors.append("experience: min > max")
                elif exp[0] < 0:
                    errors.append("experience: valeur négative")
        
        # Vérifier filtres supportés
        for key in filters.keys():
            if key not in self.supported_filters:
                errors.append(f"Filtre non supporté: {key}")
        
        return len(errors) == 0, errors


# ========================================================
# TESTS
# ========================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("🔍 TEST FILTER PROCESSOR")
    print("="*80)
    
    processor = FilterProcessor()
    
    # Test 1: Filtres multiples avec OR/AND
    print("\n1️⃣ Test filtres multiples:")
    filters1 = {
        "skills": ["python", "java"],           # OR
        "location": ["casablanca", "rabat"],    # OR
        "experience": [5, 10]                    # Range
    }
    result1 = processor.process(filters1)
    
    print(f"Input: {filters1}")
    print(f"\nBoolean filters:")
    for k, v in result1["boolean_filters"].items():
        print(f"  {k}: {v}")
    
    print(f"\nRange filters:")
    for k, v in result1["range_filters"].items():
        print(f"  {k}: {v}")
    
    print(f"\nSQL WHERE: {result1['sql_conditions']['where']}")
    print(f"SQL PARAMS: {result1['sql_conditions']['params']}")
    
    # Test 2: Compétences required/optional
    print("\n2️⃣ Test compétences structurées:")
    filters2 = {
        "skills": {
            "required": ["python"],
            "optional": ["docker", "kubernetes"]
        }
    }
    result2 = processor.process(filters2)
    print(f"Input: {filters2}")
    print(f"Result: {result2['boolean_filters']}")
    
    # Test 3: Validation
    print("\n3️⃣ Test validation:")
    filters3 = {
        "experience": [10, 5],  # Invalide
        "invalid_filter": "test"
    }
    is_valid, errors = processor.validate(filters3)
    print(f"Input: {filters3}")
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    
    print("\n✅ Tests terminés!")