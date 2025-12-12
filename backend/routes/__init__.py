"""
Package routes - Initialisation
"""

from .cv_routes import cv_bp
from .job_routes import job_bp

__all__ = ['cv_bp', 'job_bp']

print("✅ Routes SmartHire chargées")