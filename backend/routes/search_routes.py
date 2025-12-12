"""
Routes pour la recherche avancée (booléenne, vectorielle, hybride)
"""
from flask import Blueprint, request, jsonify, session
from typing import Dict, List
import logging

from backend.search.search_orchestrator import SearchOrchestrator

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

logger = logging.getLogger(__name__)

@search_bp.route('/advanced', methods=['POST'])
def advanced_search():
    """
    Recherche avancée avec filtres booléens et vectoriels
    
    Body JSON:
    {
        "query": "développeur python",
        "filters": {
            "skills": ["python", "react"],
            "location": ["Casablanca", "Remote"],
            "experience": [3, 10],
            "salary": [40000, 80000],
            "remote": true,
            "booleanOperator": "AND"  # "AND" ou "OR"
        },
        "target": "jobs",  # "jobs" ou "cvs"
        "mode": "auto",    # "auto", "boolean", "vectoriel", "hybrid"
        "limit": 20
    }
    """
    try:
        data = request.json
        
        # Vérifier l'authentification selon le target
        user_type = session.get('user_type')
        target = data.get('target', 'jobs')
        
        if target == 'jobs' and user_type != 'candidat':
            return jsonify({'error': 'Seuls les candidats peuvent rechercher des offres'}), 403
        
        if target == 'cvs' and user_type != 'recruteur':
            return jsonify({'error': 'Seuls les recruteurs peuvent rechercher des CVs'}), 403
        
        # Extraire les paramètres
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        mode = data.get('mode', 'auto')
        limit = data.get('limit', 20)
        
        # Adapter les filtres pour le moteur de recherche
        processed_filters = {}
        
        # Compétences
        if 'skills' in filters and filters['skills']:
            boolean_op = filters.get('booleanOperator', 'AND')
            if boolean_op == 'AND':
                processed_filters['skills'] = {"required": filters['skills']}
            else:  # OR
                processed_filters['skills'] = filters['skills']
        
        # Localisation
        if 'location' in filters and filters['location']:
            locations = filters['location']
            if isinstance(locations, str):
                locations = [locations]
            processed_filters['location'] = [loc.lower() for loc in locations if loc != 'Any']
        
        # Expérience
        if 'experience' in filters and filters['experience']:
            processed_filters['experience'] = filters['experience']
        
        # Salaire (convertir k$ → $)
        if 'salary' in filters and filters['salary']:
            salary_min, salary_max = filters['salary']
            processed_filters['salary'] = [salary_min * 1000, salary_max * 1000]
        
        # Remote
        if 'remote' in filters:
            processed_filters['remote'] = bool(filters['remote'])
            if filters.get('remote') and 'location' in processed_filters:
                processed_filters['location'].append('remote')
        
        # Initialiser l'orchestrateur
        orchestrator = SearchOrchestrator()
        
        # Effectuer la recherche
        result = orchestrator.search(
            query=query,
            filters=processed_filters,
            target='cvs' if target == 'cvs' else 'offres',
            mode=mode,
            top_k=limit
        )
        
        # Formater les résultats
        formatted_results = []
        
        for item in result['results']:
            if target == 'jobs':
                formatted_item = {
                    'id': item.get('id') or item.get('doc_id'),
                    'title': item.get('titre') or item.get('nom', ''),
                    'company': item.get('entreprise', ''),
                    'location': item.get('localisation', ''),
                    'remote': 'remote' in item.get('localisation', '').lower() or 
                              item.get('type_contrat', '').lower() == 'télétravail',
                    'experience': item.get('experience_min') or item.get('experience', 0),
                    'salary': {
                        'min': item.get('salaire_min', 0),
                        'max': item.get('salaire_max', 0)
                    },
                    'skills': item.get('competences_requises') or 
                              item.get('tags', []) or 
                              item.get('competences', []),
                    'description': item.get('description', '')[:200] + '...' if 
                                  item.get('description', '') else '',
                    'matchScore': int(item.get('score_hybrid', 0) * 100) if 
                                 item.get('score_hybrid') else 
                                 int(item.get('score_bm25', 0) * 10) if 
                                 item.get('score_bm25') else 0,
                    'postedDate': item.get('date_publication', ''),
                    'source': item.get('source_type', 'systeme')
                }
            else:  # CVs
                formatted_item = {
                    'id': item.get('id') or item.get('doc_id'),
                    'name': item.get('nom', ''),
                    'title': item.get('titre_profil', ''),
                    'location': item.get('localisation', ''),
                    'experience': item.get('annees_experience') or item.get('experience', 0),
                    'skills': item.get('competences') or item.get('tags', []),
                    'level': item.get('niveau_estime', ''),
                    'cvSummary': item.get('texte', '')[:200] + '...' if 
                                item.get('texte', '') else '',
                    'matchScore': int(item.get('score_hybrid', 0) * 100) if 
                                 item.get('score_hybrid') else 
                                 int(item.get('score_bm25', 0) * 10) if 
                                 item.get('score_bm25') else 0,
                    'uploadDate': item.get('date_upload', ''),
                    'source': item.get('source_type', 'uploaded')
                }
            
            formatted_results.append(formatted_item)
        
        response = {
            'success': True,
            'totalResults': result['stats']['total_results'],
            'modeUsed': result['mode_used'],
            'results': formatted_results,
            'searchStats': {
                'query': query,
                'filtersApplied': filters,
                'mode': result['mode_used'],
                'sources': result['stats'].get('source_breakdown', {}),
                'executionTime': result['stats'].get('execution_time', 0)
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Erreur recherche avancée: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@search_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Retourne des suggestions de recherche basées sur l'historique
    """
    try:
        query = request.args.get('q', '')
        
        # Suggestions basées sur les compétences populaires
        suggestions = [
            "React AND TypeScript",
            "Senior Developer OR Lead Engineer", 
            "AWS AND (Docker OR Kubernetes)",
            "Python AND Machine Learning",
            "Java AND Spring Boot",
            "JavaScript AND Node.js",
            "DevOps AND CI/CD",
            "Frontend AND React",
            "Backend AND Django",
            "Full Stack AND MongoDB"
        ]
        
        # Filtrer si une query est fournie
        if query:
            suggestions = [s for s in suggestions if query.lower() in s.lower()]
            suggestions = suggestions[:5]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@search_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    Auto-complétion pour la recherche
    """
    try:
        query = request.args.get('q', '').lower()
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []}), 200
        
        # Base de compétences pour autocomplétion
        skills = [
            "React", "TypeScript", "Node.js", "Python", "AWS",
            "Docker", "PostgreSQL", "Kubernetes", "Java", "JavaScript",
            "Spring Boot", "Django", "Flask", "FastAPI", "MongoDB",
            "MySQL", "Redis", "Git", "CI/CD", "DevOps",
            "Machine Learning", "AI", "TensorFlow", "PyTorch", "Scikit-learn",
            "Angular", "Vue.js", "Next.js", "React Native", "Flutter"
        ]
        
        # Filtrer les compétences
        suggestions = [skill for skill in skills if query in skill.lower()]
        
        return jsonify({'suggestions': suggestions[:10]}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@search_bp.route('/stats', methods=['GET'])
def get_search_stats():
    """
    Statistiques de recherche
    """
    try:
        orchestrator = SearchOrchestrator()
        system_stats = orchestrator.get_system_stats()
        
        return jsonify({
            'success': True,
            'stats': system_stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500