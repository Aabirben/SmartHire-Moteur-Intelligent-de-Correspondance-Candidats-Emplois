"""
VALIDATEUR DE SCHÉMA WHOOSH
Vérifie que les index correspondent à la configuration
"""
from whoosh.index import open_dir
from recherche_booleenne.config import (
    CV_INDEX_PATH, 
    JOB_INDEX_PATH,
    CV_SCHEMA_FIELDS,
    JOB_SCHEMA_FIELDS
)

def validate_index_schema(index_path: str, expected_fields: dict, index_name: str):
    """
    Valide qu'un index Whoosh a les bons champs
    
    Args:
        index_path: Chemin de l'index
        expected_fields: Dictionnaire {nom_champ: type}
        index_name: Nom pour logs (ex: "CV")
    
    Returns:
        bool: True si valide
    """
    try:
        ix = open_dir(index_path)
        schema = ix.schema
        
        print(f"\n🔍 Validation index {index_name}:")
        print(f"   Chemin: {index_path}")
        
        missing = []
        extra = []
        
        # Champs manquants
        for field in expected_fields:
            if field not in schema.names():
                missing.append(field)
        
        # Champs en trop (pas grave, juste informatif)
        for field in schema.names():
            if field not in expected_fields:
                extra.append(field)
        
        if missing:
            print(f"   ❌ Champs manquants: {missing}")
            return False
        
        if extra:
            print(f"   ℹ️  Champs supplémentaires: {extra}")
        
        print(f"   ✅ Schéma valide ({len(schema.names())} champs)")
        
        # Compte les documents
        with ix.searcher() as searcher:
            doc_count = searcher.doc_count_all()
            print(f"   📊 Documents indexés: {doc_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def validate_all_indexes():
    """Valide tous les index du projet"""
    print("="*60)
    print("VALIDATION DES INDEX WHOOSH")
    print("="*60)
    
    cv_valid = validate_index_schema(
        CV_INDEX_PATH, 
        CV_SCHEMA_FIELDS, 
        "CV"
    )
    
    job_valid = validate_index_schema(
        JOB_INDEX_PATH, 
        JOB_SCHEMA_FIELDS, 
        "OFFRES"
    )
    
    print("\n" + "="*60)
    if cv_valid and job_valid:
        print("✅ TOUS LES INDEX SONT VALIDES")
        print("="*60)
        return True
    else:
        print("❌ ERREURS DÉTECTÉES - VÉRIFIEZ L'INDEXATION")
        print("="*60)
        return False

if __name__ == "__main__":
    validate_all_indexes()
