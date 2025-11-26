"""
============================================================================
JOB OFFERS INDEXING SYSTEM - WHOOSH
Indexes 50 job offers with: title, description, skills, location, level
Compatible with CV indexing system for matching
============================================================================
"""

# Installation (run this first in Colab)
# !pip install whoosh -q

import os
import json
import shutil
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import scoring

# ========================================================
# CONFIGURATION
# ========================================================
JOB_JSON_FOLDER = "/content/drive/MyDrive/Job_Matching_System/job_offers/json"
INDEX_DIR = "/content/drive/MyDrive/SmartHire_INDEX_VRAI"
JOB_INDEX = os.path.join(INDEX_DIR, "jobs")

os.makedirs(INDEX_DIR, exist_ok=True)

# ========================================================
# SCHÉMA D'INDEXATION DES OFFRES
# ========================================================
job_schema = Schema(
    # Identifiant unique
    job_id=ID(stored=True, unique=True),
    
    # Titre du poste
    titre_poste=TEXT(stored=True, field_boost=2.0),  # Boost pour importance
    
    # Description complète (responsabilités + description)
    description=TEXT(stored=True),
    
    # Compétences requises (required + preferred)
    competences_requises=KEYWORD(commas=True, lowercase=True, stored=True, field_boost=1.5),
    
    # Localisation
    localisation=TEXT(stored=True),
    
    # Niveau souhaité (Junior, Mid-Level, Senior, Expert)
    niveau_souhaite=ID(stored=True),
    
    # Champs supplémentaires utiles pour le matching
    domaine=ID(stored=True),
    annees_min=NUMERIC(stored=True),
    annees_max=NUMERIC(stored=True),
    entreprise=TEXT(stored=True),
    type_contrat=TEXT(stored=True),
    mode_travail=TEXT(stored=True),
)

# ========================================================
# MAPPING NIVEAU → ANNÉES D'EXPÉRIENCE
# ========================================================
NIVEAU_MAPPING = {
    "Junior": (0, 2),
    "Mid-Level": (3, 5),
    "Senior": (6, 10),
    "Expert": (11, 20)
}

# ========================================================
# EXTRACTION DES DONNÉES DES OFFRES
# ========================================================
def extract_job_data(job_json):
    """Extrait et structure les données d'une offre d'emploi"""
    
    # Titre du poste
    titre_poste = job_json.get("title", "")
    
    # Description complète (description + responsabilités)
    description_text = job_json.get("description", "")
    responsibilities = job_json.get("responsibilities", [])
    if responsibilities:
        description_text += " " + " ".join(responsibilities)
    
    # Compétences requises (required + preferred)
    required_skills = job_json.get("required_skills", [])
    preferred_skills = job_json.get("preferred_skills", [])
    all_skills = required_skills + preferred_skills
    competences_requises = [skill.lower() for skill in all_skills]
    
    # Localisation
    localisation = job_json.get("location", "")
    if not localisation:
        localisation = job_json.get("company", {}).get("city", "")
    
    # Niveau souhaité
    niveau_souhaite = job_json.get("experience_level", "Mid-Level")
    
    # Années min/max selon niveau
    annees_min, annees_max = NIVEAU_MAPPING.get(niveau_souhaite, (0, 5))
    
    # Champs supplémentaires
    domaine = job_json.get("domain", "").lower()
    entreprise = job_json.get("company", {}).get("name", "")
    type_contrat = job_json.get("contract_type", "")
    mode_travail = job_json.get("work_mode", "")
    
    return {
        "job_id": job_json.get("job_id", ""),
        "titre_poste": titre_poste,
        "description": description_text,
        "competences_requises": competences_requises,
        "localisation": localisation,
        "niveau_souhaite": niveau_souhaite,
        "domaine": domaine,
        "annees_min": annees_min,
        "annees_max": annees_max,
        "entreprise": entreprise,
        "type_contrat": type_contrat,
        "mode_travail": mode_travail,
    }

# ========================================================
# INDEXATION DES OFFRES
# ========================================================
def index_job_offers():
    """Indexe toutes les offres d'emploi depuis les fichiers JSON"""
    
    # Supprime l'ancien index s'il existe
    if os.path.exists(JOB_INDEX):
        shutil.rmtree(JOB_INDEX)
    
    # Crée le nouvel index
    os.makedirs(JOB_INDEX)
    ix = create_in(JOB_INDEX, job_schema)
    writer = AsyncWriter(ix)
    
    print("="*120)
    print("INDEXATION DES OFFRES D'EMPLOI - SYSTÈME DE MATCHING")
    print("="*120 + "\n")
    
    # Liste tous les fichiers JSON
    json_files = sorted([f for f in os.listdir(JOB_JSON_FOLDER) if f.endswith(".json") and f != "all_jobs.json"])
    total_jobs = len(json_files)
    
    indexed_count = 0
    
    for i, json_file in enumerate(json_files, 1):
        filepath = os.path.join(JOB_JSON_FOLDER, json_file)
        
        try:
            # Charge le JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            # Extrait les données
            extracted = extract_job_data(job_data)
            
            # Indexe l'offre
            writer.add_document(
                job_id=extracted["job_id"],
                titre_poste=extracted["titre_poste"],
                description=extracted["description"],
                competences_requises=",".join(extracted["competences_requises"]),
                localisation=extracted["localisation"],
                niveau_souhaite=extracted["niveau_souhaite"],
                domaine=extracted["domaine"],
                annees_min=extracted["annees_min"],
                annees_max=extracted["annees_max"],
                entreprise=extracted["entreprise"],
                type_contrat=extracted["type_contrat"],
                mode_travail=extracted["mode_travail"],
            )
            
            indexed_count += 1
            
            # Affichage formaté
            skills_preview = ", ".join(extracted["competences_requises"][:5])
            if len(extracted["competences_requises"]) > 5:
                skills_preview += f" (+ {len(extracted['competences_requises']) - 5} autres)"
            
            desc_preview = extracted["description"][:60] + "..." if len(extracted["description"]) > 60 else extracted["description"]
            
            print(f"\n{i:02d}/{total_jobs} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  🆔 JOB ID:             {extracted['job_id']}")
            print(f"  💼 TITRE POSTE:        {extracted['titre_poste']}")
            print(f"  🏢 ENTREPRISE:         {extracted['entreprise']}")
            print(f"  📍 LOCALISATION:       {extracted['localisation']}")
            print(f"  📊 NIVEAU SOUHAITÉ:    {extracted['niveau_souhaite']} ({extracted['annees_min']}-{extracted['annees_max']} ans)")
            print(f"  🏷️  DOMAINE:            {extracted['domaine'].upper()}")
            print(f"  🛠️  COMPÉTENCES:        {len(extracted['competences_requises'])} skills → {skills_preview}")
            print(f"  📝 DESCRIPTION:        {desc_preview}")
            
        except Exception as e:
            print(f"\n⚠️ Erreur lors du traitement de {json_file}: {str(e)}")
            continue
    
    # Commit l'index
    writer.commit()
    
    print("\n" + "="*120)
    print("✅ INDEXATION DES OFFRES TERMINÉE AVEC SUCCÈS")
    print("="*120)
    print(f"\n📊 Statistiques:")
    print(f"   • Total offres traitées: {total_jobs}")
    print(f"   • Offres indexées avec succès: {indexed_count}")
    print(f"   • Index sauvegardé dans: {JOB_INDEX}")
    print("\n📁 Champs indexés:")
    print("   ✓ Titre du poste (avec boost 2.0)")
    print("   ✓ Description complète")
    print("   ✓ Compétences requises (avec boost 1.5)")
    print("   ✓ Localisation")
    print("   ✓ Niveau souhaité")
    print("   ✓ Domaine, entreprise, type de contrat, mode de travail")
    
    return indexed_count

# ========================================================
# FONCTION DE RECHERCHE (POUR TESTS)
# ========================================================
def search_jobs(query_text, top_n=5):
    """Recherche des offres par mot-clé"""
    from whoosh.index import open_dir
    
    ix = open_dir(JOB_INDEX)
    
    with ix.searcher(weighting=scoring.BM25F()) as searcher:
        # Parser multi-champs avec OR
        parser = MultifieldParser(
            ["titre_poste", "description", "competences_requises", "localisation"],
            schema=job_schema,
            group=OrGroup
        )
        
        query = parser.parse(query_text)
        results = searcher.search(query, limit=top_n)
        
        print(f"\n🔍 Recherche: '{query_text}'")
        print(f"📊 {len(results)} résultats trouvés\n")
        print("="*120)
        
        for i, hit in enumerate(results, 1):
            print(f"\n{i}. {hit['titre_poste']} - {hit['entreprise']}")
            print(f"   📍 {hit['localisation']} | 📊 {hit['niveau_souhaite']} | 🏷️ {hit['domaine'].upper()}")
            print(f"   🛠️ Compétences: {hit['competences_requises'][:100]}...")
            print(f"   Score: {hit.score:.2f}")
        
        print("\n" + "="*120)

# ========================================================
# EXÉCUTION
# ========================================================
if __name__ == "__main__":
    # Indexation des offres
    indexed_count = index_job_offers()
    
    print("\n" + "="*120)
    print("🎯 SYSTÈME PRÊT POUR LE MATCHING CV-OFFRES")
    print("="*120)
    print("\n💡 Prochaines étapes:")
    print("   1. L'index des CV existe déjà: /content/drive/MyDrive/SmartHire_INDEX_VRAI/cv")
    print("   2. L'index des offres est maintenant créé: /content/drive/MyDrive/SmartHire_INDEX_VRAI/jobs")
    print("   3. Vous pouvez maintenant créer l'algorithme de matching qui compare les deux index")
    print("\n📊 Exemples de recherche:")
    print("   • search_jobs('python backend developer')")
    print("   • search_jobs('react frontend casablanca')")
    print("   • search_jobs('devops kubernetes senior')")
    print("="*120)