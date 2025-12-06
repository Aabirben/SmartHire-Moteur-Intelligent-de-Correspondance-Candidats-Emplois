"""
============================================================================
SMARTHIRE - PDF Reader Module (PRODUCTION HARDENED)
Extraction robuste de texte depuis les fichiers PDF
============================================================================
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from io import BytesIO

try:
    from PyPDF2 import PdfReader
    from PyPDF2.errors import PdfReadError
except ImportError:
    raise ImportError("PyPDF2 est requis. Installez-le avec: pip install PyPDF2")

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE_MB = 50  # Limite de taille de fichier
MAX_PAGES = 100  # Limite de pages pour éviter les timeouts


# ========================================================
# FONCTION PRINCIPALE D'EXTRACTION
# ========================================================
def lire_pdf(filepath: Path) -> Optional[str]:
    """
    Lit et extrait le texte d'un fichier PDF de manière robuste
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        Texte extrait ou None en cas d'erreur
        
    Raises:
        ValueError: Si le fichier dépasse la taille maximale
    """
    # Validation du chemin
    if not filepath or not isinstance(filepath, Path):
        logger.error("❌ Chemin de fichier invalide")
        return None
    
    try:
        # Vérification existence
        if not filepath.exists():
            logger.error(f"❌ Fichier introuvable: {filepath}")
            return None
        
        # Vérification extension
        if filepath.suffix.lower() != '.pdf':
            logger.error(f"❌ Format invalide (attendu PDF): {filepath.suffix}")
            return None
        
        # Vérification taille
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.error(f"❌ Fichier trop volumineux: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)")
            return None
        
        # Lecture du PDF
        try:
            reader = PdfReader(str(filepath))
        except PdfReadError as e:
            logger.error(f"❌ PDF corrompu ou illisible {filepath.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lecture PDF {filepath.name}: {e}")
            return None
        
        # Vérification nombre de pages
        if len(reader.pages) == 0:
            logger.warning(f"⚠️ PDF vide: {filepath.name}")
            return None
        
        if len(reader.pages) > MAX_PAGES:
            logger.warning(f"⚠️ PDF trop long ({len(reader.pages)} pages), lecture limitée à {MAX_PAGES} pages")
        
        # Extraction page par page
        text_parts = []
        pages_to_read = min(len(reader.pages), MAX_PAGES)
        
        for page_num in range(pages_to_read):
            try:
                page = reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur page {page_num + 1} de {filepath.name}: {e}")
                continue
        
        # Consolidation du texte
        if not text_parts:
            logger.warning(f"⚠️ Aucun texte extrait de {filepath.name}")
            return None
        
        full_text = " ".join(text_parts)
        
        # Nettoyage basique
        full_text = _nettoyer_texte(full_text)
        
        if not full_text:
            logger.warning(f"⚠️ Texte vide après nettoyage: {filepath.name}")
            return None
        
        logger.info(f"✅ PDF lu avec succès: {filepath.name} ({len(text_parts)} pages, {len(full_text)} caractères)")
        return full_text
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lecture PDF {filepath.name}: {e}", exc_info=True)
        return None


def lire_pdf_avec_info(filepath: Path) -> Dict:
    """
    Lit un PDF et retourne le texte avec des métadonnées détaillées
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        Dictionnaire avec texte et métadonnées
    """
    result = {
        'success': False,
        'text': '',
        'nb_pages': 0,
        'nb_chars': 0,
        'file_size_mb': 0,
        'filename': '',
        'error': None
    }
    
    try:
        if not filepath or not isinstance(filepath, Path):
            result['error'] = 'Chemin invalide'
            return result
        
        if not filepath.exists():
            result['error'] = 'Fichier introuvable'
            return result
        
        # Métadonnées du fichier
        result['filename'] = filepath.name
        result['file_size_mb'] = round(filepath.stat().st_size / (1024 * 1024), 2)
        
        # Extraction du texte
        text = lire_pdf(filepath)
        
        if text is None:
            result['error'] = 'Erreur extraction du texte'
            return result
        
        # Lecture des métadonnées PDF
        try:
            reader = PdfReader(str(filepath))
            result['nb_pages'] = len(reader.pages)
        except Exception as e:
            logger.warning(f"⚠️ Impossible de lire les métadonnées: {e}")
            result['nb_pages'] = text.count('\f') + 1  # Estimation
        
        # Succès
        result['success'] = True
        result['text'] = text
        result['nb_chars'] = len(text)
        
        return result
        
    except Exception as e:
        result['error'] = f'Erreur inattendue: {str(e)}'
        logger.error(f"❌ Erreur lire_pdf_avec_info: {e}", exc_info=True)
        return result


def lire_pdf_from_bytes(pdf_bytes: bytes) -> Optional[str]:
    """
    Lit un PDF directement depuis des bytes (upload API ou base de données)
    
    Args:
        pdf_bytes: Contenu binaire du PDF
        
    Returns:
        Texte extrait ou None en cas d'erreur
    """
    if not pdf_bytes or not isinstance(pdf_bytes, bytes):
        logger.error("❌ Données bytes invalides")
        return None
    
    # Vérification taille
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        logger.error(f"❌ Données trop volumineuses: {size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)")
        return None
    
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        
        if len(reader.pages) == 0:
            logger.warning("⚠️ PDF vide")
            return None
        
        text_parts = []
        pages_to_read = min(len(reader.pages), MAX_PAGES)
        
        for page_num in range(pages_to_read):
            try:
                page = reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur page {page_num + 1}: {e}")
                continue
        
        if not text_parts:
            logger.warning("⚠️ Aucun texte extrait")
            return None
        
        full_text = " ".join(text_parts)
        full_text = _nettoyer_texte(full_text)
        
        return full_text if full_text else None
        
    except PdfReadError as e:
        logger.error(f"❌ PDF corrompu: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur lecture PDF depuis bytes: {e}", exc_info=True)
        return None


def valider_pdf(filepath: Path) -> bool:
    """
    Vérifie si un fichier PDF est valide et lisible
    
    Args:
        filepath: Chemin vers le fichier PDF
        
    Returns:
        True si le PDF est valide
    """
    if not filepath or not isinstance(filepath, Path):
        return False
    
    try:
        # Existence et extension
        if not filepath.exists():
            return False
        
        if filepath.suffix.lower() != '.pdf':
            return False
        
        # Taille
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False
        
        # Lecture PDF
        reader = PdfReader(str(filepath))
        
        # Au moins une page
        if len(reader.pages) == 0:
            return False
        
        # Essaie d'extraire le texte de la première page
        first_page_text = reader.pages[0].extract_text()
        
        return bool(first_page_text and first_page_text.strip())
        
    except PdfReadError:
        return False
    except Exception as e:
        logger.debug(f"Validation PDF échouée pour {filepath}: {e}")
        return False


# ========================================================
# FONCTIONS UTILITAIRES
# ========================================================
def _nettoyer_texte(texte: str) -> str:
    """
    Nettoie le texte extrait du PDF
    
    Args:
        texte: Texte brut
        
    Returns:
        Texte nettoyé
    """
    if not texte:
        return ""
    
    import re
    
    # Supprime les caractères de contrôle sauf espaces et retours à la ligne
    texte = ''.join(char for char in texte if char.isprintable() or char in '\n\r\t ')
    
    # Normalise les espaces
    texte = re.sub(r'[ \t]+', ' ', texte)
    
    # Normalise les retours à la ligne
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    
    return texte.strip()


def compter_pdfs(directory: Path) -> int:
    """
    Compte le nombre de fichiers PDF dans un dossier
    
    Args:
        directory: Chemin du dossier
        
    Returns:
        Nombre de PDFs trouvés
    """
    if not directory or not isinstance(directory, Path):
        logger.error("❌ Chemin de dossier invalide")
        return 0
    
    try:
        if not directory.exists():
            logger.error(f"❌ Dossier introuvable: {directory}")
            return 0
        
        if not directory.is_dir():
            logger.error(f"❌ Pas un dossier: {directory}")
            return 0
        
        return len(list(directory.glob("*.pdf")))
        
    except Exception as e:
        logger.error(f"❌ Erreur comptage PDF dans {directory}: {e}")
        return 0


def lister_pdfs(directory: Path, valides_seulement: bool = False) -> List[Path]:
    """
    Liste tous les fichiers PDF d'un dossier
    
    Args:
        directory: Chemin du dossier
        valides_seulement: Si True, ne retourne que les PDFs valides
        
    Returns:
        Liste des chemins vers les PDFs
    """
    if not directory or not isinstance(directory, Path):
        logger.error("❌ Chemin de dossier invalide")
        return []
    
    try:
        if not directory.exists():
            logger.error(f"❌ Dossier introuvable: {directory}")
            return []
        
        if not directory.is_dir():
            logger.error(f"❌ Pas un dossier: {directory}")
            return []
        
        pdfs = sorted(directory.glob("*.pdf"))
        
        if valides_seulement:
            pdfs = [pdf for pdf in pdfs if valider_pdf(pdf)]
        
        return pdfs
        
    except Exception as e:
        logger.error(f"❌ Erreur listage PDF dans {directory}: {e}")
        return []


def extraire_batch(directory: Path, limit: Optional[int] = None) -> Dict[str, str]:
    """
    Extrait le texte de plusieurs PDFs en batch
    
    Args:
        directory: Dossier contenant les PDFs
        limit: Nombre maximum de PDFs à traiter (None = tous)
        
    Returns:
        Dictionnaire {nom_fichier: texte_extrait}
    """
    results = {}
    
    pdfs = lister_pdfs(directory, valides_seulement=True)
    
    if limit:
        pdfs = pdfs[:limit]
    
    logger.info(f"📄 Extraction de {len(pdfs)} PDFs depuis {directory}")
    
    for i, pdf_path in enumerate(pdfs, 1):
        try:
            texte = lire_pdf(pdf_path)
            if texte:
                results[pdf_path.name] = texte
                logger.info(f"✅ [{i}/{len(pdfs)}] {pdf_path.name}")
            else:
                logger.warning(f"⚠️ [{i}/{len(pdfs)}] Échec extraction: {pdf_path.name}")
        except Exception as e:
            logger.error(f"❌ [{i}/{len(pdfs)}] Erreur {pdf_path.name}: {e}")
            continue
    
    logger.info(f"✅ Extraction terminée: {len(results)}/{len(pdfs)} réussis")
    return results


# ========================================================
# TESTS
# ========================================================
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    print("="*80)
    print("TEST DU MODULE PDF READER")
    print("="*80)
    
    # Test avec un fichier PDF
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        
        print(f"\n📄 Fichier: {test_file}")
        
        # Validation
        print("\n1️⃣ VALIDATION:")
        if valider_pdf(test_file):
            print("   ✅ PDF valide")
            
            # Extraction avec info
            print("\n2️⃣ EXTRACTION AVEC MÉTADONNÉES:")
            result = lire_pdf_avec_info(test_file)
            
            if result['success']:
                print(f"   ✅ Succès")
                print(f"   • Nom: {result['filename']}")
                print(f"   • Taille: {result['file_size_mb']} MB")
                print(f"   • Pages: {result['nb_pages']}")
                print(f"   • Caractères: {result['nb_chars']}")
                
                print(f"\n3️⃣ EXTRAIT (300 premiers caractères):")
                print(f"   {result['text'][:300]}...")
            else:
                print(f"   ❌ Erreur: {result['error']}")
        else:
            print("   ❌ PDF invalide ou illisible")
    
    # Test avec un dossier
    elif len(sys.argv) > 2 and sys.argv[1] == "--dir":
        test_dir = Path(sys.argv[2])
        
        print(f"\n📁 Dossier: {test_dir}")
        
        print("\n1️⃣ COMPTAGE:")
        nb_pdfs = compter_pdfs(test_dir)
        print(f"   {nb_pdfs} PDFs trouvés")
        
        print("\n2️⃣ LISTAGE:")
        pdfs = lister_pdfs(test_dir, valides_seulement=True)
        for pdf in pdfs[:5]:
            print(f"   • {pdf.name}")
        if len(pdfs) > 5:
            print(f"   ... et {len(pdfs) - 5} autres")
        
        print("\n3️⃣ EXTRACTION BATCH (5 premiers):")
        results = extraire_batch(test_dir, limit=5)
        for filename, text in results.items():
            print(f"   ✅ {filename}: {len(text)} caractères")
    
    else:
        print("\nUsage:")
        print("  python pdf_reader.py <chemin_vers_pdf>")
        print("  python pdf_reader.py --dir <chemin_vers_dossier>")