"""
============================================================================
SMARTHIRE - PDF Reader Module
Extraction de texte depuis les fichiers PDF
============================================================================
"""

import logging
from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader
from io import BytesIO
from PyPDF2 import PdfReader
logger = logging.getLogger(__name__)

# ========================================================
# FONCTION PRINCIPALE D'EXTRACTION
# ========================================================
def lire_pdf(filepath: Path) -> Optional[str]:
    """
    Lit et extrait le texte d'un fichier PDF
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        Texte extrait ou None en cas d'erreur
    """
    try:
        if not filepath.exists():
            logger.error(f"❌ Fichier introuvable: {filepath}")
            return None
        
        if not filepath.suffix.lower() == '.pdf':
            logger.error(f"❌ Format invalide (attendu PDF): {filepath}")
            return None
        
        text = ""
        reader = PdfReader(str(filepath))
        
        if len(reader.pages) == 0:
            logger.warning(f"⚠️ PDF vide: {filepath}")
            return None
        
        # Extraction page par page
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
            except Exception as e:
                logger.warning(f"⚠️ Erreur page {page_num} de {filepath.name}: {e}")
                continue
        
        if not text.strip():
            logger.warning(f"⚠️ Aucun texte extrait de {filepath.name}")
            return None
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture PDF {filepath.name}: {e}")
        return None


def lire_pdf_avec_info(filepath: Path) -> dict:
    """
    Lit un PDF et retourne le texte avec des métadonnées
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        Dictionnaire avec texte et métadonnées
    """
    try:
        text = lire_pdf(filepath)
        
        if text is None:
            return {
                'success': False,
                'text': '',
                'nb_pages': 0,
                'nb_chars': 0,
                'error': 'Erreur extraction'
            }
        
        reader = PdfReader(str(filepath))
        
        return {
            'success': True,
            'text': text,
            'nb_pages': len(reader.pages),
            'nb_chars': len(text),
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'nb_pages': 0,
            'nb_chars': 0,
            'error': str(e)
        }


def valider_pdf(filepath: Path) -> bool:
    """
    Vérifie si un fichier PDF est valide et lisible
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        True si le PDF est valide
    """
    try:
        if not filepath.exists():
            return False
        
        if not filepath.suffix.lower() == '.pdf':
            return False
        
        reader = PdfReader(str(filepath))
        
        # Vérifie qu'il y a au moins une page
        if len(reader.pages) == 0:
            return False
        
        # Essaie d'extraire le texte de la première page
        first_page_text = reader.pages[0].extract_text()
        
        return bool(first_page_text and first_page_text.strip())
        
    except Exception:
        return False


# ========================================================
# FONCTIONS UTILITAIRES
# ========================================================
def compter_pdfs(directory: Path) -> int:
    """Compte le nombre de fichiers PDF dans un dossier"""
    try:
        return len(list(directory.glob("*.pdf")))
    except Exception as e:
        logger.error(f"❌ Erreur comptage PDF dans {directory}: {e}")
        return 0


def lister_pdfs(directory: Path) -> list:
    """Liste tous les fichiers PDF d'un dossier"""
    try:
        return sorted(directory.glob("*.pdf"))
    except Exception as e:
        logger.error(f"❌ Erreur listage PDF dans {directory}: {e}")
        return []
def lire_pdf_from_bytes(pdf_bytes: bytes) -> Optional[str]:
    """Lit un PDF directement depuis des bytes (upload API ou base de données)"""
    if not pdf_bytes:
        return None
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + " "
        return text.strip() if text.strip() else None
    except Exception as e:
        logger.error(f"Erreur lecture PDF depuis bytes : {e}")
        return None


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Test avec un fichier PDF
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        
        print("="*80)
        print("TEST DU MODULE PDF READER")
        print("="*80)
        print(f"\n📄 Fichier: {test_file}")
        
        # Validation
        if valider_pdf(test_file):
            print("✅ PDF valide")
            
            # Extraction avec info
            result = lire_pdf_avec_info(test_file)
            
            if result['success']:
                print(f"\n📊 Métadonnées:")
                print(f"   • Nombre de pages: {result['nb_pages']}")
                print(f"   • Nombre de caractères: {result['nb_chars']}")
                print(f"\n📝 Extrait (200 premiers caractères):")
                print(result['text'][:200] + "...")
            else:
                print(f"❌ Erreur: {result['error']}")
        else:
            print("❌ PDF invalide ou illisible")
    else:
        print("Usage: python pdf_reader.py <chemin_vers_pdf>")