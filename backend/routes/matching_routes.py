"""
Routes pour le matching CV-Offre avec analyse détaillée
"""
from flask import Blueprint, request, jsonify, session
import logging
import re
from database.connection import get_db_connection
from backend.search.boolean_search import BooleanSearchModel
from backend.search.vectoriel_model import VectorielSearchModel

matching_bp = Blueprint('matching', __name__, url_prefix='/api/matching')
logger = logging.getLogger(__name__)

# Initialiser les modèles
boolean_model = BooleanSearchModel()
vectoriel_model = VectorielSearchModel()

# Fonction pour extraire l'ID numérique
def extract_numeric_id(entity_id):
    """
    Extrait l'ID numérique d'un identifiant formaté
    Exemples:
    - "JOB-0007-2025" -> 7
    - "CV_45_Meriem_Hamidi.pdf" -> 45
    - "45" -> 45
    - "07" -> 7
    """
    if not entity_id:
        return None
    
    # Si c'est déjà un nombre
    if isinstance(entity_id, int):
        return entity_id
    if isinstance(entity_id, str) and entity_id.isdigit():
        # Gérer les IDs commençant par 0 comme "07"
        return int(entity_id.lstrip('0') or '0')
    
    # Chercher des nombres dans la chaîne
    numbers = re.findall(r'\d+', entity_id)
    if numbers:
        return int(numbers[0])
    
    return None

def resolve_entity_id(entity_id, entity_type='cv'):
    """
    Résout un ID d'entité qui peut être:
    1. Un ID numérique direct
    2. Un ID formaté
    3. Un ID offset (ajoute 50 car nos IDs commencent à 51)
    """
    if not entity_id:
        return None
    
    # Extraire l'ID numérique
    numeric_id = extract_numeric_id(entity_id)
    
    if numeric_id is not None:
        # Si l'ID est petit (<50) mais que nos vrais IDs commencent à 51
        # On suppose que c'est un offset (position dans la liste)
        if numeric_id < 50:
            return 50 + numeric_id  # Ex: 7 -> 57, 0 -> 50
        return numeric_id
    
    return None

@matching_bp.route('/cv/<cv_id>/job/<job_id>', methods=['GET'])
def match_cv_to_job(cv_id, job_id):
    """
    Analyse détaillée du matching CV ↔ Offre
    """
    conn = None
    try:
        # Résoudre les IDs
        cv_id_num = resolve_entity_id(cv_id, 'cv')
        job_id_num = resolve_entity_id(job_id, 'job')
        
        logger.info(f"Matching: cv_id={cv_id}->{cv_id_num}, job_id={job_id}->{job_id_num}")
        
        if not cv_id_num or not job_id_num:
            return jsonify({'error': f'ID invalide (cv:{cv_id}, job:{job_id})'}), 400
        
        # Récupérer les détails CV et Offre
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Détails CV
        cur.execute("""
            SELECT nom, email, competences, localisation, annees_experience,
                   niveau_estime, type_contrat, diplome, texte_complet
            FROM cvs WHERE id = %s
        """, (cv_id_num,))
        cv_data = cur.fetchone()
        
        # Détails Offre
        cur.execute("""
            SELECT titre, entreprise, competences_requises, localisation,
                   experience_min, niveau_souhaite, type_contrat, 
                   diplome_requis, description
            FROM offres WHERE id = %s
        """, (job_id_num,))
        job_data = cur.fetchone()
        
        cur.close()
        
        if not cv_data:
            return jsonify({'error': 'CV non trouvé'}), 404
        if not job_data:
            return jsonify({'error': 'Offre non trouvée'}), 404
        
        # 3. Calculer les scores détaillés
        cv_skills = set(cv_data[2]) if cv_data[2] else set()
        job_skills = set(job_data[2]) if job_data[2] else set()
        
        matching_skills = cv_skills & job_skills
        missing_skills = job_skills - cv_skills
        extra_skills = cv_skills - job_skills
        
        # Score compétences
        skills_score = (len(matching_skills) / len(job_skills) * 100) if job_skills else 0
        
        # Score expérience
        cv_exp = cv_data[4] or 0
        job_exp = job_data[4] or 0
        exp_match = min(cv_exp / job_exp, 1.5) if job_exp > 0 else 1.0
        exp_score = min(exp_match * 100, 100)
        
        # Score localisation
        cv_location = (cv_data[3] or "").lower()
        job_location = (job_data[3] or "").lower()
        location_score = 100 if cv_location == job_location or "remote" in job_location else 50
        
        # Score niveau
        cv_level = cv_data[5] or ""
        job_level = job_data[5] or ""
        level_map = {"débutant": 1, "intermédiaire": 2, "senior": 3, "expert": 4}
        cv_level_val = level_map.get(cv_level.lower(), 2)
        job_level_val = level_map.get(job_level.lower(), 2)
        level_score = 100 if cv_level_val >= job_level_val else 70
        
        # Score global
        total_score = int(
            skills_score * 0.5 +
            exp_score * 0.2 +
            location_score * 0.15 +
            level_score * 0.15
        )
        
        # 4. Breakdown détaillé
        score_breakdown = [
            {
                "category": "Compétences Techniques",
                "score": int(skills_score),
                "contribution": 50,
                "icon": "Code",
                "detail": f"{len(matching_skills)} compétences correspondent sur {len(job_skills)} requises. {len(missing_skills)} compétences manquantes."
            },
            {
                "category": "Expérience",
                "score": int(exp_score),
                "contribution": 20,
                "icon": "Briefcase",
                "detail": f"{cv_exp} ans d'expérience vs {job_exp} ans requis. {'Excellent match!' if cv_exp >= job_exp else 'Légèrement en dessous.'}"
            },
            {
                "category": "Localisation",
                "score": int(location_score),
                "contribution": 15,
                "icon": "MapPin",
                "detail": f"Candidat à {cv_location}, poste à {job_location}. {'Parfait!' if location_score == 100 else 'Acceptable'}"
            },
            {
                "category": "Niveau",
                "score": int(level_score),
                "contribution": 15,
                "icon": "TrendingUp",
                "detail": f"Niveau {cv_level} vs {job_level} requis. {'Parfait match!' if level_score == 100 else 'Bon potentiel'}"
            }
        ]
        
        # 5. Données radar chart
        skills_data = []
        for skill in list(job_skills)[:8]:  # Top 8 compétences
            skills_data.append({
                "skill": skill,
                "required": 100,
                "user": 100 if skill in cv_skills else 0
            })
        
        # 6. Fit criteria
        fit_criteria = [
            {
                "name": "Expérience",
                "required": f"{job_exp}+ ans",
                "candidate": f"{cv_exp} ans",
                "matchPercent": int(exp_score),
                "icon": "Clock"
            },
            {
                "name": "Localisation",
                "required": job_location,
                "candidate": cv_location,
                "matchPercent": int(location_score),
                "icon": "MapPin"
            },
            {
                "name": "Niveau",
                "required": job_level,
                "candidate": cv_level,
                "matchPercent": int(level_score),
                "icon": "Award"
            },
            {
                "name": "Compétences",
                "required": f"{len(job_skills)} compétences",
                "candidate": f"{len(matching_skills)} matching",
                "matchPercent": int(skills_score),
                "icon": "CheckCircle"
            }
        ]
        
        # 7. Skill gaps
        missing_skills_list = []
        for skill in list(missing_skills)[:5]:
            missing_skills_list.append({
                "name": skill,
                "requiredLevel": 100,
                "currentLevel": 0,
                "impactPercent": int(100 / len(job_skills)) if job_skills else 0,
                "suggestions": [
                    f"Suivre un cours en ligne sur {skill}",
                    f"Réaliser un projet pratique avec {skill}",
                    f"Obtenir une certification {skill}"
                ]
            })
        
        # 8. Recommandation
        if total_score >= 80:
            recommendation = "Excellent candidat ! Profil très aligné avec les exigences du poste. Recommandé pour un entretien."
        elif total_score >= 60:
            recommendation = "Bon candidat avec quelques compétences à développer. Potentiel intéressant."
        else:
            recommendation = "Profil avec des écarts significatifs. Formation complémentaire recommandée."
        
        # 9. Niveau détecté
        level_detection = {
            "level": cv_level or "Intermédiaire",
            "confidence": int(level_score),
            "reasons": [
                f"{cv_exp} années d'expérience professionnelle",
                f"{len(cv_skills)} compétences techniques maîtrisées",
                f"Niveau estimé: {cv_level}",
                f"Type de contrat recherché: {cv_data[6] or 'CDI'}"
            ]
        }
        
        # Résultat final
        result = {
            "totalScore": total_score,
            "scoreBreakdown": score_breakdown,
            "skillsData": skills_data,
            "fitCriteria": fit_criteria,
            "recommendation": recommendation,
            "level": level_detection,
            "missingSkills": missing_skills_list,
            "matchingSkills": list(matching_skills),
            "candidate": {
                "name": cv_data[0] or "Candidat",
                "email": cv_data[1] or "",
                "location": cv_location,
                "experience": cv_exp,
                "level": cv_level,
                "skills": list(cv_skills)
            },
            "job": {
                "title": job_data[0] or "Offre",
                "company": job_data[1] or "",
                "location": job_location,
                "experience": job_exp,
                "level": job_level,
                "skills": list(job_skills)
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur matching: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@matching_bp.route('/candidate/<candidate_id>', methods=['GET'])
def get_candidate_details(candidate_id):
    """
    Récupère les détails d'un candidat pour l'interface recruteur
    """
    # Vérifier l'authentification - plus souple pour le debug
    # if 'user_id' not in session or session.get('user_type') != 'recruteur':
    #     return jsonify({'error': 'Non autorisé'}), 403
    
    conn = None
    try:
        # Résoudre l'ID
        candidate_id_num = resolve_entity_id(candidate_id, 'cv')
        
        if not candidate_id_num:
            return jsonify({'error': f'ID candidat invalide: {candidate_id}'}), 400
        
        logger.info(f"get_candidate_details: {candidate_id} -> {candidate_id_num}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, nom, email, competences, localisation, annees_experience,
                   niveau_estime, type_contrat, diplome, texte_complet
            FROM cvs WHERE id = %s
        """, (candidate_id_num,))
        
        cv = cur.fetchone()
        
        if cv:
            result = {
                "id": str(cv[0]),
                "name": cv[1] or "Candidat",
                "email": cv[2] or "",
                "title": f"{cv[6] or 'Developer'}",
                "location": cv[4] or "",
                "experience": cv[5] or 0,
                "skills": cv[3] or [],
                "level": cv[6] or "Intermédiaire",
                "cvSummary": (cv[9][:300] + "...") if cv[9] else "Aucun résumé disponible"
            }
            
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Candidat non trouvé'}), 404
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération candidat: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@matching_bp.route('/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """
    Récupère les détails d'une offre pour l'interface candidat
    """
    # Vérifier l'authentification - plus souple pour le debug
    # if 'user_id' not in session or session.get('user_type') != 'candidat':
    #     return jsonify({'error': 'Non autorisé'}), 403
    
    conn = None
    try:
        # Résoudre l'ID
        job_id_num = resolve_entity_id(job_id, 'job')
        
        if not job_id_num:
            return jsonify({'error': f'ID offre invalide: {job_id}'}), 400
        
        logger.info(f"get_job_details: {job_id} -> {job_id_num}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, titre, entreprise, competences_requises, description,
                   localisation, niveau_souhaite, type_contrat,
                   diplome_requis, experience_min, date_publication
            FROM offres WHERE id = %s
        """, (job_id_num,))
        
        job = cur.fetchone()
        
        if job:
            result = {
                "id": str(job[0]),
                "title": job[1] or "Offre",
                "company": job[2] or "",
                "skills": job[3] or [],
                "description": job[4] or "",
                "location": job[5] or "",
                "remote": "remote" in (job[5] or "").lower() or job[7] == "télétravail",
                "experience": job[9] or 0,
                "level": job[6] or "",
                "posted": job[10].strftime("%Y-%m-%d") if job[10] else ""
            }
            
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Offre non trouvée'}), 404
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération offre: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


# Routes de débogage
@matching_bp.route('/debug/ids', methods=['GET'])
def debug_ids():
    """Affiche tous les IDs disponibles"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # CVs
        cur.execute("SELECT id, nom FROM cvs ORDER BY id")
        cvs = cur.fetchall()
        
        # Jobs
        cur.execute("SELECT id, titre FROM offres ORDER BY id")
        jobs = cur.fetchall()
        
        cv_list = [{"id": row[0], "name": row[1]} for row in cvs]
        job_list = [{"id": row[0], "title": row[1]} for row in jobs]
        
        return jsonify({
            "cvs": cv_list,
            "jobs": job_list,
            "total_cvs": len(cv_list),
            "total_jobs": len(job_list),
            "cv_id_range": {"min": cv_list[0]["id"], "max": cv_list[-1]["id"]} if cv_list else None,
            "job_id_range": {"min": job_list[0]["id"], "max": job_list[-1]["id"]} if job_list else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur debug: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()