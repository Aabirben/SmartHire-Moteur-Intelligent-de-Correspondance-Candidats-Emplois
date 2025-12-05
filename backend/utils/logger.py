"""
============================================================================
SMARTHIRE - Logger Configuration
Configuration centralisée du système de logging
============================================================================
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from ..config.settings import LOGGING_CONFIG, BASE_DIR

# ========================================================
# CONFIGURATION DU LOGGING
# ========================================================
def setup_logging(log_file: bool = True, console: bool = True):
    """
    Configure le système de logging
    
    Args:
        log_file: Si True, écrit dans un fichier de log
        console: Si True, affiche dans la console
    """
    # Dossier de logs
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configuration de base
    root_logger = logging.getLogger()
    root_logger.setLevel(LOGGING_CONFIG['level'])
    
    # Formatter
    formatter = logging.Formatter(
        fmt=LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['datefmt']
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = log_dir / f"smarthire_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"📝 Log file: {log_filename}")


# ========================================================
# FONCTIONS UTILITAIRES
# ========================================================
def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger configuré
    
    Args:
        name: Nom du logger (généralement __name__)
        
    Returns:
        Logger configuré
    """
    return logging.getLogger(name)


def log_separator(logger: logging.Logger, char: str = "=", length: int = 80):
    """Affiche une ligne de séparation dans les logs"""
    logger.info(char * length)


def log_section(logger: logging.Logger, title: str, char: str = "=", length: int = 80):
    """Affiche un titre de section dans les logs"""
    logger.info(char * length)
    logger.info(title.center(length))
    logger.info(char * length)


if __name__ == "__main__":
    # Test du logger
    setup_logging()
    logger = get_logger(__name__)
    
    log_section(logger, "TEST DU SYSTÈME DE LOGGING")
    
    logger.debug("Message de debug")
    logger.info("Message d'information")
    logger.warning("Message d'avertissement")
    logger.error("Message d'erreur")
    
    log_separator(logger)
    logger.info("✅ Test du logging terminé")