"""
============================================================================
JOB OFFERS INDEXING SYSTEM - WHOOSH + NLP PREPROCESSING
Indexes job offers with advanced text processing:
- Lowercase normalization
- Punctuation removal
- Tokenization
- Stopwords removal (NLTK)
- Lemmatization (NLTK)
Compatible with CV indexing system for matching
============================================================================
"""

# Installation (run this first in Colab)
# !pip install whoosh nltk -q

import os
import json
import shutil
import re
import string
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import scoring
from whoosh.analysis import StemmingAnalyzer, Filter, Token
import nltk

# Télécharger les ressources NLTK nécessaires
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('omw-1.4', quiet=True)
except:
    pass

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ========================================================
# CONFIGURATION
# ========================================================
JOB_JSON_FOLDER = "/content/drive/MyDrive/Job_Matching_System/job_offers/json"
INDEX_DIR = "/content/drive/MyDrive/SmartHire_INDEX_VRAI"
JOB_INDEX = os.path.join(INDEX_DIR, "jobs")

os.makedirs(INDEX_DIR, exist_ok=True)

# ========================================================
# ANALYSEUR DE TEXTE PERSONNALISÉ (NLP)
# ========================================================

class LemmatizationFilter(Filter):
    """Filtre personnalisé pour la lemmatisation avec NLTK"""
    
    def __init__(self):
        super().__init__()
        self.lemmatizer = WordNetLemmatizer()
    
    def __call__(self, tokens):
        for token in tokens:
            # Lemmatise le token
            lemmatized = self.lemmatizer.lemmatize(token.text.lower())
            token.text = lemmatized
            yield token

def preprocess_text(text):
    """
    Prétraitement complet du texte selon le pipeline demandé:
    1. Extraction du texte (déjà fait en JSON)
    2. Passage en minuscules
    3. Suppression de la ponctuation
    4. Tokenisation
    5. Suppression des stopwords (NLTK)
    6. Lemmatisation
    """
    if not text:
        return ""
    
    # Étape 1: Minuscules
    text = text.lower()
    
    # Étape 2: Suppression de la ponctuation (sauf espaces)
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Étape 3: Tokenisation
    try:
        tokens = word_tokenize(text)
    except:
        # Fallback si NLTK tokenizer échoue
        tokens = text.split()
    
    # Étape 4: Suppression des stopwords (français + anglais)
    try:
        stop_words_fr = set(stopwords.words('french'))
        stop_words_en = set(stopwords.words('english'))
        stop_words = stop_words_fr.union(stop_words_en)
    except:
        stop_words = set()
    
    # Ajout de stopwords techniques personnalisés
    custom_stopwords = {'etc', 'via', 'plus', 'moins', 'tres', 'beaucoup'}
    stop_words = stop_words.union(custom_stopwords)
    
    tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
    
    # Étape 5: Lemmatisation
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return " ".join(tokens)

# ========================================================
# SCHÉMA D'INDEXATION DES OFFRES (avec analyseur NLP)
# ========================================================
job_schema = Schema(
    # Identifiant unique
    job_id=ID(stored=True, unique=True),
    
    # Titre du poste (avec preprocessing + boost)
    titre_poste=TEXT(stored=True, field_boost=2.0, analyzer=StemmingAnalyzer()),
    
    # Description complète (avec preprocessing)
    description=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    
    # Compétences requises (keywords avec preprocessing)
    competences_requises=KEYWORD(commas=True, lowercase=True, stored=True, field_boost=1.5),
    
    # Versions preprocessées pour le matching avancé
    titre_poste_processed=TEXT(stored=True),
    description_processed=TEXT(stored=True),
    
    # Localisation
    localisation=TEXT(stored=True),
    
    # Niveau souhaité
    niveau_souhaite=ID(stored=True),
    
    # Champs supplémentaires
    domaine=ID(stored=True),
    annees_min=NUMERIC(stored=True),
    annees_max=NUMERIC(stored=True),
    entreprise=TEXT(stored=True),
    type_contrat=TEXT(stored=True),
    mode_travail=TEXT(stored=True),
    
    # Statistiques de preprocessing (pour debug)
    nb_tokens_original=NUMERIC(stored=True),
    nb_tokens_processed=NUMERIC(stored=True),
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
    """Extrait et structure les données d'une offre d'emploi avec preprocessing NLP"""
    
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
    
    # Prétraitement NLP du titre et de la description
    titre_processed = preprocess_text(titre_poste)
    description_processed = preprocess_text(description_text)
    
    # Statistiques de preprocessing
    nb_tokens_original = len((titre_poste + " " + description_text).split())
    nb_tokens_processed = len((titre_processed + " " + description_processed).split())
    
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
        "titre_poste_processed": titre_processed,
        "description_processed": description_processed,
        "competences_requises": competences_requises,
        "localisation": localisation,
        "niveau_souhaite": niveau_souhaite,
        "domaine": domaine,
        "annees_min": annees_min,
        "annees_max": annees_max,
        "entreprise": entreprise,
        "type_contrat": type_contrat,
        "mode_travail": mode_travail,
        "nb_tokens_original": nb_tokens_original,
        "nb_tokens_processed": nb_tokens_processed,
    }

# ========================================================
# INDEXATION DES OFFRES
# ========================================================
def index_job_offers():
    """Indexe toutes les offres d'emploi avec preprocessing NLP"""
    
    # Supprime l'ancien index s'il existe
    if os.path.exists(JOB_INDEX):
        shutil.rmtree(JOB_INDEX)
    
    # Crée le nouvel index
    os.makedirs(JOB_INDEX)
    ix = create_in(JOB_INDEX, job_schema)
    writer = AsyncWriter(ix)
    
    print("="*120)
    print("INDEXATION DES OFFRES D'EMPLOI - SYSTÈME DE MATCHING AVEC NLP")
    print("="*120 + "\n")
    
    # Liste tous les fichiers JSON
    json_files = sorted([f for f in os.listdir(JOB_JSON_FOLDER) if f.endswith(".json") and f != "all_jobs.json"])
    total_jobs = len(json_files)
    
    indexed_count = 0
    total_tokens_saved = 0
    
    for i, json_file in enumerate(json_files, 1):
        filepath = os.path.join(JOB_JSON_FOLDER, json_file)
        
        try:
            # Charge le JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            # Extrait les données avec preprocessing
            extracted = extract_job_data(job_data)
            
            # Indexe l'offre
            writer.add_document(
                job_id=extracted["job_id"],
                titre_poste=extracted["titre_poste"],
                description=extracted["description"],
                titre_poste_processed=extracted["titre_poste_processed"],
                description_processed=extracted["description_processed"],
                competences_requises=",".join(extracted["competences_requises"]),
                localisation=extracted["localisation"],
                niveau_souhaite=extracted["niveau_souhaite"],
                domaine=extracted["domaine"],
                annees_min=extracted["annees_min"],
                annees_max=extracted["annees_max"],
                entreprise=extracted["entreprise"],
                type_contrat=extracted["type_contrat"],
                mode_travail=extracted["mode_travail"],
                nb_tokens_original=extracted["nb_tokens_original"],
                nb_tokens_processed=extracted["nb_tokens_processed"],
            )
            
            indexed_count += 1
            tokens_saved = extracted["nb_tokens_original"] - extracted["nb_tokens_processed"]
            total_tokens_saved += tokens_saved
            
            # Affichage formaté avec stats NLP
            skills_preview = ", ".join(extracted["competences_requises"][:5])
            if len(extracted["competences_requises"]) > 5:
                skills_preview += f" (+ {len(extracted['competences_requises']) - 5} autres)"
            
            reduction_pct = (tokens_saved / extracted["nb_tokens_original"] * 100) if extracted["nb_tokens_original"] > 0 else 0
            
            print(f"\n{i:02d}/{total_jobs} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  🆔 JOB ID:             {extracted['job_id']}")
            print(f"  💼 TITRE POSTE:        {extracted['titre_poste']}")
            print(f"  🏢 ENTREPRISE:         {extracted['entreprise']}")
            print(f"  📍 LOCALISATION:       {extracted['localisation']}")
            print(f"  📊 NIVEAU SOUHAITÉ:    {extracted['niveau_souhaite']} ({extracted['annees_min']}-{extracted['annees_max']} ans)")
            print(f"  🏷️  DOMAINE:            {extracted['domaine'].upper()}")
            print(f"  🛠️  COMPÉTENCES:        {len(extracted['competences_requises'])} skills → {skills_preview}")
            print(f"  🧠 NLP PROCESSING:     {extracted['nb_tokens_original']} → {extracted['nb_tokens_processed']} tokens (-{reduction_pct:.1f}%)")
            print(f"     • Titre processed:  {extracted['titre_poste_processed'][:80]}...")
            
        except Exception as e:
            print(f"\n⚠️ Erreur lors du traitement de {json_file}: {str(e)}")
            continue
    
    # Commit l'index
    writer.commit()
    
    avg_reduction = (total_tokens_saved / (indexed_count * 50)) if indexed_count > 0 else 0
    
    print("\n" + "="*120)
    print("✅ INDEXATION DES OFFRES TERMINÉE AVEC SUCCÈS")
    print("="*120)
    print(f"\n📊 Statistiques:")
    print(f"   • Total offres traitées: {total_jobs}")
    print(f"   • Offres indexées avec succès: {indexed_count}")
    print(f"   • Index sauvegardé dans: {JOB_INDEX}")
    print(f"\n🧠 Statistiques NLP:")
    print(f"   • Total tokens économisés: {total_tokens_saved}")
    print(f"   • Réduction moyenne: {avg_reduction:.1f}%")
    print(f"   • Pipeline appliqué: lowercase → depunct → tokenize → stopwords → lemmatize")
    print("\n📁 Champs indexés:")
    print("   ✓ Titre du poste (original + processed, boost 2.0)")
    print("   ✓ Description complète (original + processed)")
    print("   ✓ Compétences requises (avec boost 1.5)")
    print("   ✓ Localisation, niveau, domaine, entreprise")
    print("   ✓ Statistiques de preprocessing")
    
    return indexed_count

# ========================================================
# FONCTION DE RECHERCHE AMÉLIORÉE
# ========================================================
def search_jobs(query_text, top_n=5, use_processed=True):
    """Recherche des offres avec option de texte preprocessé"""
    from whoosh.index import open_dir
    
    ix = open_dir(JOB_INDEX)
    
    # Prétraite la requête si demandé
    if use_processed:
        query_text_search = preprocess_text(query_text)
        fields = ["titre_poste_processed", "description_processed", "competences_requises"]
        print(f"\n🔍 Requête originale: '{query_text}'")
        print(f"🧠 Requête preprocessée: '{query_text_search}'")
    else:
        query_text_search = query_text
        fields = ["titre_poste", "description", "competences_requises"]
        print(f"\n🔍 Recherche standard: '{query_text}'")
    
    with ix.searcher(weighting=scoring.BM25F()) as searcher:
        parser = MultifieldParser(fields, schema=job_schema, group=OrGroup)
        
        query = parser.parse(query_text_search)
        results = searcher.search(query, limit=top_n)
        
        print(f"📊 {len(results)} résultats trouvés\n")
        print("="*120)
        
        for i, hit in enumerate(results, 1):
            reduction = hit['nb_tokens_original'] - hit['nb_tokens_processed']
            reduction_pct = (reduction / hit['nb_tokens_original'] * 100) if hit['nb_tokens_original'] > 0 else 0
            
            print(f"\n{i}. {hit['titre_poste']} - {hit['entreprise']}")
            print(f"   📍 {hit['localisation']} | 📊 {hit['niveau_souhaite']} | 🏷️ {hit['domaine'].upper()}")
            print(f"   🛠️ Compétences: {hit['competences_requises'][:80]}...")
            print(f"   🧠 NLP: {hit['nb_tokens_original']} → {hit['nb_tokens_processed']} tokens (-{reduction_pct:.1f}%)")
            print(f"   Score: {hit.score:.2f}")
        
        print("\n" + "="*120)
        return results

# ========================================================
# ANALYSE DE LA QUALITÉ DU PREPROCESSING
# ========================================================
def analyze_preprocessing_quality():
    """Analyse la qualité du preprocessing sur l'index"""
    from whoosh.index import open_dir
    
    ix = open_dir(JOB_INDEX)
    
    print("\n" + "="*120)
    print("📊 ANALYSE DE LA QUALITÉ DU PREPROCESSING NLP")
    print("="*120 + "\n")
    
    total_original = 0
    total_processed = 0
    count = 0
    
    with ix.searcher() as searcher:
        for doc in searcher.documents():
            total_original += doc.get('nb_tokens_original', 0)
            total_processed += doc.get('nb_tokens_processed', 0)
            count += 1
    
    avg_original = total_original / count if count > 0 else 0
    avg_processed = total_processed / count if count > 0 else 0
    avg_reduction = ((total_original - total_processed) / total_original * 100) if total_original > 0 else 0
    
    print(f"📈 Statistiques globales sur {count} offres:")
    print(f"   • Tokens originaux (moyenne): {avg_original:.1f}")
    print(f"   • Tokens après preprocessing (moyenne): {avg_processed:.1f}")
    print(f"   • Réduction moyenne: {avg_reduction:.1f}%")
    print(f"   • Total tokens économisés: {total_original - total_processed}")
    print("\n✅ Pipeline de preprocessing:")
    print("   1. ✓ Lowercase normalization")
    print("   2. ✓ Punctuation removal")
    print("   3. ✓ Tokenization (NLTK)")
    print("   4. ✓ Stopwords removal (FR + EN)")
    print("   5. ✓ Lemmatization (WordNet)")
    print("="*120)

# ========================================================
# EXÉCUTION
# ========================================================
if __name__ == "__main__":
    # Indexation des offres avec NLP
    indexed_count = index_job_offers()
    
    # Analyse de la qualité du preprocessing
    analyze_preprocessing_quality()
    
    print("\n" + "="*120)
    print("🎯 SYSTÈME PRÊT POUR LE MATCHING CV-OFFRES AVEC NLP")
    print("="*120)
    print("\n💡 Prochaines étapes:")
    print("   1. Index CV avec NLP: /content/drive/MyDrive/SmartHire_INDEX_VRAI/cv")
    print("   2. Index offres avec NLP: /content/drive/MyDrive/SmartHire_INDEX_VRAI/jobs")
    print("   3. Créer algorithme de matching qui compare les champs *_processed")
    print("\n📊 Exemples de recherche:")
    print("   • search_jobs('développement python backend', use_processed=True)")
    print("   • search_jobs('react frontend casablanca', use_processed=True)")
    print("   • search_jobs('ingénieur devops kubernetes senior', use_processed=True)")
    print("="*120)