"""
Routes pour la gestion des offres d'emploi avec indexation temps réel
"""

from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime

from database.connection import get_db_connection
from backend.indexation.job_indexer import indexer_offre_depuis_donnees

job_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

logger = logging.getLogger(__name__)

@job_bp.route('/index/<int:job_id>', methods=['POST'])
def index_job(job_id):
    """
    Indexe une offre en temps réel (appelé après création)
    """
    if 'user_id' not in session or session.get('user_type') != 'recruteur':
        logger.warning(f"Unauthorized indexing attempt for job #{job_id}")
        return jsonify({'error': 'Non autorisé'}), 403
    
    user_id = session['user_id']
    
    try:
        data = request.json
        job_data = data.get('job_data', {})
        
        logger.info(f"Indexing job #{job_id} by recruiter {user_id}")
        
        # Indexer l'offre
        success = indexer_offre_depuis_donnees(
            job_id=str(job_id),
            job_data=job_data,
            user_id=str(user_id)
        )
        
        if success:
            logger.info(f"✅ Job #{job_id} indexed successfully")
            return jsonify({
                'success': True,
                'message': 'Job indexed successfully',
                'job_id': job_id,
                'indexed_at': datetime.now().isoformat()
            }), 200
        else:
            logger.error(f"❌ Failed to index job #{job_id}")
            return jsonify({
                'success': False,
                'message': 'Indexing failed',
                'job_id': job_id,
                'indexed_at': None
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error indexing job #{job_id}: {str(e)}")
        return jsonify({'error': f'Indexing error: {str(e)}'}), 500

@job_bp.route('/test-index', methods=['GET'])
def test_index():
    """
    Route de test pour vérifier l'indexation
    """
    return jsonify({
        'status': 'ready',
        'whoosh_available': True,
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'create_job': 'POST /api/recruiter/jobs',
            'index_job': 'POST /api/jobs/index/<id>',
            'get_jobs': 'GET /api/recruiter/jobs'
        }
    }), 200