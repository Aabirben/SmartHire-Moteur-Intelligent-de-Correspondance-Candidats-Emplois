"""
============================================================================
SMARTHIRE - Preprocessing NLP Module
Pipeline complet de traitement de texte:
1. Extraction du texte
2. Passage en minuscules
3. Suppression de la ponctuation
4. Tokenisation
5. Suppression des stopwords
6. Lemmatisation
============================================================================
"""

import re
import string
import logging
from typing import List, Tuple, Set
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from backend.config.settings import NLTK_DOWNLOADS, CUSTOM_STOPWORDS

logger = logging.getLogger(__name__)

# ========================================================
# INITIALISATION NLTK
# ========================================================
def init_nltk():
    """Télécharge toutes les ressources NLTK nécessaires"""
    try:
        for resource in NLTK_DOWNLOADS:
            nltk.download(resource, quiet=True)
        logger.info("✅ NLTK resources téléchargées avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement NLTK: {e}")
        raise

# Initialisation au chargement du module
init_nltk()

# ========================================================
# PRÉPARATEURS GLOBAUX
# ========================================================
lemmatizer = WordNetLemmatizer()

# Stopwords (anglais + français + custom)
try:
    stop_words_en = set(stopwords.words('english'))
    stop_words_fr = set(stopwords.words('french'))
    stop_words = stop_words_en.union(stop_words_fr).union(CUSTOM_STOPWORDS)
except Exception as e:
    logger.warning(f"⚠️ Erreur chargement stopwords: {e}")
    stop_words = CUSTOM_STOPWORDS

# ========================================================
# FONCTION PRINCIPALE DE PRÉTRAITEMENT
# ========================================================
def pretraiter_texte(texte: str, preserve_skills: bool = True, skills_list: Set[str] = None) -> Tuple[str, List[str]]:
    """
    Pipeline complet de prétraitement NLP
    
    Args:
        texte: Texte brut à prétraiter
        preserve_skills: Si True, préserve les compétences techniques
        skills_list: Liste des compétences à préserver
        
    Returns:
        Tuple (texte_prétraité, tokens_prétraités)
    """
    if not texte:
        return "", []
    
    # PROTECTION DES COMPÉTENCES (optionnel)
    protected_terms = {}
    if preserve_skills and skills_list:
        for skill in skills_list:
            placeholder = f"__SKILL_{skill.replace(' ', '_').replace('.', '_').upper()}__"
            pattern = r'\b' + re.escape(skill) + r'\b'
            texte = re.sub(pattern, placeholder, texte, flags=re.IGNORECASE)
            protected_terms[placeholder] = skill
    
    # ÉTAPE 1: Nettoyage préliminaire
    texte = re.sub(r'\\[a-zA-Z]+\{.*?\}', ' ', texte)  # Commandes LaTeX
    texte = re.sub(r'\d{4}-\d{4}', ' ', texte)  # Dates
    texte = re.sub(r'[^\w\s\-]', ' ', texte)  # Caractères spéciaux
    
    # ÉTAPE 2: Passage en minuscules
    texte_lower = texte.lower()
    
    # ÉTAPE 3: Suppression de la ponctuation
    translator = str.maketrans('', '', string.punctuation.replace('-', ''))
    texte_sans_ponctuation = texte_lower.translate(translator)
    
    # ÉTAPE 4: Tokenisation
    try:
        tokens = word_tokenize(texte_sans_ponctuation)
    except LookupError:
        logger.warning("⚠️ Tokenisation NLTK échouée, utilisation du split simple")
        tokens = texte_sans_ponctuation.split()
    except Exception as e:
        logger.warning(f"⚠️ Erreur tokenisation: {e}")
        tokens = texte_sans_ponctuation.split()
    
    # ÉTAPE 5: Suppression des stopwords et tokens courts
    tokens_filtres = [
        token for token in tokens 
        if token not in stop_words 
        and len(token) > 2
        and not token.isdigit()
    ]
    
    # ÉTAPE 6: Lemmatisation
    tokens_lemmatises = []
    for token in tokens_filtres:
        try:
            # Lemmatisation verbes puis noms
            lemme = lemmatizer.lemmatize(token, pos='v')
            lemme = lemmatizer.lemmatize(lemme, pos='n')
            tokens_lemmatises.append(lemme)
        except Exception:
            tokens_lemmatises.append(token)
    
    # RESTAURATION DES COMPÉTENCES PROTÉGÉES
    tokens_finaux = []
    for token in tokens_lemmatises:
        if token in protected_terms:
            tokens_finaux.append(protected_terms[token])
        else:
            tokens_finaux.append(token)
    
    texte_pretraite = " ".join(tokens_finaux)
    
    return texte_pretraite, tokens_finaux


def pretraiter_competences(competences_list: List[str]) -> str:
    """
    Prétraite les compétences (normalisation simple, sans lemmatisation)
    
    Args:
        competences_list: Liste de compétences
        
    Returns:
        Chaîne de compétences normalisées séparées par des virgules
    """
    competences_normalisees = []
    
    for skill in competences_list:
        # Normalisation simple: minuscules et trim
        skill_norm = skill.lower().strip()
        
        # Suppression des caractères spéciaux sauf . et -
        skill_norm = re.sub(r'[^\w\s\.\-]', '', skill_norm)
        
        if skill_norm and len(skill_norm) > 1:
            competences_normalisees.append(skill_norm)
    
    return ",".join(competences_normalisees)


def nettoyer_texte_brut(texte: str) -> str:
    """
    Nettoyage léger du texte brut (avant extraction d'informations)
    
    Args:
        texte: Texte brut
        
    Returns:
        Texte nettoyé
    """
    if not texte:
        return ""
    
    # Suppression des commandes LaTeX
    texte = re.sub(r'\\[a-zA-Z]+\{.*?\}', ' ', texte)
    
    # Suppression des emails
    texte = re.sub(r'Email\s*[: ].*?(\s|$)', ' ', texte, flags=re.I)
    
    # Suppression des téléphones
    texte = re.sub(r'Mobile\s*[: ].*?(\s|$)', ' ', texte, flags=re.I)
    texte = re.sub(r'Phone\s*[: ].*?(\s|$)', ' ', texte, flags=re.I)
    
    # Normalisation des espaces
    texte = re.sub(r'\s+', ' ', texte)
    
    return texte.strip()


# ========================================================
# FONCTIONS UTILITAIRES
# ========================================================
def compter_tokens(texte: str) -> int:
    """Compte le nombre de tokens dans un texte"""
    try:
        return len(word_tokenize(texte))
    except:
        return len(texte.split())


def calculer_reduction(nb_original: int, nb_processed: int) -> float:
    """Calcule le pourcentage de réduction de tokens"""
    if nb_original == 0:
        return 0.0
    return ((nb_original - nb_processed) / nb_original) * 100


if __name__ == "__main__":
    # Tests
    texte_test = """
    Python Developer with 5 years of experience in Django, Flask, and FastAPI.
    Strong knowledge of PostgreSQL, MongoDB, and Redis databases.
    Experienced in Docker, Kubernetes, and AWS cloud services.
    """
    
    print("="*80)
    print("TEST DU MODULE PREPROCESSING")
    print("="*80)
    print(f"\n📝 Texte original:\n{texte_test}")
    
    texte_pretraite, tokens = pretraiter_texte(texte_test, preserve_skills=False)
    
    print(f"\n🔤 Tokens extraits ({len(tokens)}):")
    print(tokens)
    
    print(f"\n✅ Texte prétraité:\n{texte_pretraite}")
    
    nb_original = compter_tokens(texte_test)
    nb_processed = len(tokens)
    reduction = calculer_reduction(nb_original, nb_processed)
    
    print(f"\n📊 Statistiques:")
    print(f"   • Tokens originaux: {nb_original}")
    print(f"   • Tokens après preprocessing: {nb_processed}")
    print(f"   • Réduction: {reduction:.1f}%")