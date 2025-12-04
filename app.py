"""
APPLICATION FLASK PRINCIPALE
Point d'entrée de l'API SmartHire
"""
from flask import Flask
from flask_cors import CORS
import logging

from api.routes.search_routes import search_bp
from recherche_booleenne.config import verify_setup

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    
    app = Flask(__name__)
    
    # Configuration CORS (pour React sur port 8080)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:5173",  # Vite dev server
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Vérification des index au démarrage
    logger.info("="*80)
    logger.info("🚀 DÉMARRAGE API SMARTHIRE")
    logger.info("="*80)
    
    try:
        if not verify_setup():
            logger.error("❌ Configuration invalide - Arrêt")
            raise RuntimeError("Index manquants ou invalides")
    except Exception as e:
        logger.error(f"❌ Erreur vérification: {e}")
        logger.error("\n💡 Exécutez d'abord:")
        logger.error("   1. python indexation/indexation_cv.py")
        logger.error("   2. python indexation/indexation_offres.py")
        raise
    
    # Enregistrement des routes
    app.register_blueprint(search_bp, url_prefix='/api')
    
    @app.route('/health')
    def health():
        """Endpoint de santé (vérifier que l'API fonctionne)"""
        return {
            "status": "ok",
            "message": "SmartHire API is running",
            "version": "1.0.0"
        }
    
    @app.route('/')
    def home():
        """Page d'accueil de l'API"""
        return {
            "message": "SmartHire Boolean Search API",
            "endpoints": {
                "health": "/health",
                "search_jobs": "/api/search/jobs",
                "search_cvs": "/api/search/cvs",
                "get_cv": "/api/cv/<cv_id>",
                "get_job": "/api/job/<job_id>"
            },
            "docs": "https://github.com/votre-repo/smarthire"
        }
    
    logger.info("✅ Application Flask initialisée")
    logger.info("="*80)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',      # Accessible depuis n'importe quelle interface
        port=5000,           # Port par défaut Flask
        debug=True           # Mode debug (désactiver en production)
    )
