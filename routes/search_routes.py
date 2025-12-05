"""
ROUTES DE RECHERCHE - VERSION COMPLÈTE
Endpoints pour l'interface React
"""
from flask import Blueprint, request, jsonify
import logging

from recherche_booleenne.boolean_engine import BooleanSearchEngine

logger = logging.getLogger(__name__)

# Création du blueprint
search_bp = Blueprint('search', __name__)

# Initialisation du moteur (singleton)
try:
    search_engine = BooleanSearchEngine()
    logger.info("✅ Moteur de recherche initialisé")
except Exception as e:
    logger.error(f"❌ Erreur init moteur: {e}")
    search_engine = None


# ============================================================
# ENDPOINT 1 : RECHERCHE OFFRES POUR CANDIDATS
# ============================================================
@search_bp.route('/search/jobs', methods=['POST', 'GET'])
def search_jobs():
    """
    Recherche offres pour un candidat
    
    POST /api/search/jobs
    Body: {
        "query": "python developer",
        "filters": {
            "skills": ["python", "django"],
            "location": "casablanca",
            "experience": [3, 10],
            "level": "senior",
            "remote": true,
            "boolean_operator": "AND"
        },
        "limit": 10
    }
    
    GET /api/search/jobs?q=python&location=casablanca&limit=5
    
    Response: {
        "results": [
            {
                "id": "offre_job-0001-2025",
                "postgres_id": 51,
                "titre": "Cloud Infrastructure Engineer",
                "entreprise": "Webhelp Morocco",
                "competences": ["aws", "docker", "kubernetes"],
                "localisation": "Casablanca, Morocco",
                "niveau": "senior",
                "experience_min": 6,
                "experience_max": 10,
                "type_contrat": "cdd (fixed-term)",
                "score_booleen": 1.0
            }
        ],
        "total": 12,
        "query_info": {
            "query_text": "python developer",
            "filters": {...},
            "whoosh_query": "..."
        }
    }
    """
    if not search_engine:
        return jsonify({
            "error": "Moteur de recherche non initialisé",
            "message": "Vérifiez les index Whoosh"
        }), 500
    
    try:
        # Récupération des paramètres
        if request.method == 'POST':
            data = request.get_json() or {}
            query_text = data.get("query", "")
            filters = data.get("filters", {})
            limit = data.get("limit", 10)
        else:  # GET
            query_text = request.args.get("q", "")
            
            # Construction des filtres depuis query params
            filters = {}
            
            if request.args.get("location"):
                filters["location"] = request.args.get("location")
            
            if request.args.getlist("skills"):
                filters["skills"] = request.args.getlist("skills")
            
            if request.args.get("level"):
                filters["level"] = request.args.get("level")
            
            if request.args.get("remote"):
                filters["remote"] = request.args.get("remote", "false").lower() == "true"
            
            if request.args.get("exp_min") or request.args.get("exp_max"):
                filters["experience"] = [
                    int(request.args.get("exp_min", 0)),
                    int(request.args.get("exp_max", 50))
                ]
            
            limit = int(request.args.get("limit", 10))
        
        logger.info(f"🔍 Recherche offres: query='{query_text}', filters={filters}")
        
        # Exécution de la recherche
        results = search_engine.search_jobs_for_candidate(
            query_text=query_text,
            filters=filters,
            limit=limit
        )
        
        return jsonify(results), 200
        
    except ValueError as e:
        logger.error(f"⚠️ Paramètres invalides: {e}")
        return jsonify({
            "error": "Paramètres invalides",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche offres: {e}", exc_info=True)
        return jsonify({
            "error": "Erreur lors de la recherche",
            "message": str(e)
        }), 500


# ============================================================
# ENDPOINT 2 : RECHERCHE CV POUR RECRUTEURS
# ============================================================
@search_bp.route('/search/cvs', methods=['POST', 'GET'])
def search_cvs():
    """
    Recherche CV pour un recruteur
    
    POST /api/search/cvs
    Body: {
        "query": "senior developer",
        "filters": {
            "skills": ["react", "typescript"],
            "location": "rabat",
            "experience": [5, 15],
            "boolean_operator": "OR"
        },
        "limit": 10
    }
    
    GET /api/search/cvs?q=senior&skills=react&skills=typescript
    
    Response: {
        "results": [
            {
                "id": "cv_cv_01_amine_tazi",
                "postgres_id": 51,
                "nom": "Amine Tazi",
                "titre": "Full-stack Developer",
                "competences": ["python", "django", "react"],
                "experience": 4,
                "localisation": "Casablanca",
                "projets": "E-commerce Platform | Chat App",
                "score_booleen": 1.0
            }
        ],
        "total": 8,
        "query_info": {...}
    }
    """
    if not search_engine:
        return jsonify({
            "error": "Moteur de recherche non initialisé"
        }), 500
    
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            query_text = data.get("query", "")
            filters = data.get("filters", {})
            limit = data.get("limit", 10)
        else:  # GET
            query_text = request.args.get("q", "")
            
            filters = {}
            if request.args.get("location"):
                filters["location"] = request.args.get("location")
            if request.args.getlist("skills"):
                filters["skills"] = request.args.getlist("skills")
            if request.args.get("exp_min") or request.args.get("exp_max"):
                filters["experience"] = [
                    int(request.args.get("exp_min", 0)),
                    int(request.args.get("exp_max", 50))
                ]
            
            limit = int(request.args.get("limit", 10))
        
        logger.info(f"🔍 Recherche CV: query='{query_text}', filters={filters}")
        
        results = search_engine.search_cvs_for_recruiter(
            query_text=query_text,
            filters=filters,
            limit=limit
        )
        
        return jsonify(results), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Paramètres invalides",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche CV: {e}", exc_info=True)
        return jsonify({
            "error": "Erreur lors de la recherche",
            "message": str(e)
        }), 500


# ============================================================
# ENDPOINT 3 : RÉCUPÉRER UN CV SPÉCIFIQUE
# ============================================================
@search_bp.route('/cv/<cv_id>', methods=['GET'])
def get_cv(cv_id):
    """
    Récupère un CV par son ID système
    
    GET /api/cv/cv_cv_01_amine_tazi
    
    Response: {
        "id": "cv_cv_01_amine_tazi",
        "postgres_id": 51,
        "nom": "Amine Tazi",
        "titre": "Full-stack Developer",
        ...
    }
    """
    if not search_engine:
        return jsonify({"error": "Moteur non initialisé"}), 500
    
    try:
        logger.info(f"📄 Récupération CV: {cv_id}")
        cv = search_engine.get_cv_by_id(cv_id)
        
        if cv:
            return jsonify(cv), 200
        else:
            return jsonify({
                "error": "CV non trouvé",
                "cv_id": cv_id
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erreur get CV: {e}")
        return jsonify({
            "error": "Erreur serveur",
            "message": str(e)
        }), 500


# ============================================================
# ENDPOINT 4 : RÉCUPÉRER UNE OFFRE SPÉCIFIQUE
# ============================================================
@search_bp.route('/job/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Récupère une offre par son ID système
    
    GET /api/job/offre_job-0001-2025
    
    Response: {
        "id": "offre_job-0001-2025",
        "postgres_id": 51,
        "titre": "Cloud Infrastructure Engineer",
        ...
    }
    """
    if not search_engine:
        return jsonify({"error": "Moteur non initialisé"}), 500
    
    try:
        logger.info(f"📋 Récupération offre: {job_id}")
        job = search_engine.get_job_by_id(job_id)
        
        if job:
            return jsonify(job), 200
        else:
            return jsonify({
                "error": "Offre non trouvée",
                "job_id": job_id
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erreur get job: {e}")
        return jsonify({
            "error": "Erreur serveur",
            "message": str(e)
        }), 500


# ============================================================
# ENDPOINT 5 : STATISTIQUES (BONUS)
# ============================================================
@search_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Statistiques sur les index
    
    GET /api/stats
    
    Response: {
        "cvs": {
            "total": 50,
            "skills_most_common": ["python", "javascript", "react"],
            "avg_experience": 4.5
        },
        "jobs": {
            "total": 50,
            "levels": {"junior": 15, "senior": 20, "expert": 15},
            "locations": {"Casablanca": 25, "Rabat": 15, ...}
        }
    }
    """
    if not search_engine:
        return jsonify({"error": "Moteur non initialisé"}), 500
    
    try:
        from recherche_booleenne.config import CV_MAPPING, JOB_MAPPING
        
        stats = {
            "cvs": {
                "total": len(CV_MAPPING),
                "indexed": True
            },
            "jobs": {
                "total": len(JOB_MAPPING),
                "indexed": True
            },
            "message": "Statistiques détaillées à implémenter (optionnel)"
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        return jsonify({"error": str(e)}), 500