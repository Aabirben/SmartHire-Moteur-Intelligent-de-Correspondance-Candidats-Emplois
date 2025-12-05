# ============================================================================
# backend/config/__init__.py
# ============================================================================
"""
Configuration Package
"""

from .settings import (
    CV_FOLDER,
    JOB_FOLDER,
    INDEX_DIR,
    CV_INDEX,
    JOB_INDEX,
    SKILLS_FILE,
    MOROCCAN_CITIES,
    NIVEAU_MAPPING,
    create_directories
)

__all__ = [
    'CV_FOLDER',
    'JOB_FOLDER',
    'INDEX_DIR',
    'CV_INDEX',
    'JOB_INDEX',
    'SKILLS_FILE',
    'MOROCCAN_CITIES',
    'NIVEAU_MAPPING',
    'create_directories'
]


