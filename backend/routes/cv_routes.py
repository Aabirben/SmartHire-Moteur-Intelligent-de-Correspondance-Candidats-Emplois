"""
Routes pour la gestion des CVs (upload, indexation, extraction)
"""

from flask import Blueprint, request, jsonify, session
import os
import tempfile
from datetime import datetime

from database.connection import get_db_connection
from backend.extraction.pdf_reader import lire_pdf_from_bytes
from backend.extraction.info_extractor import extraire_toutes_infos
from backend.extraction.skills_extractor import extraire_competences_avec_stats
from backend.indexation.cv_indexer import indexer_cv_depuis_texte

cv_bp = Blueprint('cv', __name__, url_prefix='/api/cv')

# ==================== UPLOAD CV ====================

@cv_bp.route('/upload', methods=['POST'])
def upload_cv():
    """
    Upload un CV PDF, extrait les informations et indexe dans Whoosh
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    user_id = session['user_id']
    user_type = session.get('user_type', 'candidat')
    
    # Vérifier si c'est un candidat
    if user_type != 'candidat':
        return jsonify({'error': 'Seuls les candidats peuvent uploader des CVs'}), 403
    
    # Vérifier si un fichier est présent
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    
    # Vérifier si un fichier est sélectionné
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Vérifier l'extension
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Format non supporté. Veuillez uploader un PDF'}), 400
    
    # Vérifier la taille (max 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return jsonify({'error': 'Fichier trop volumineux (max 5MB)'}), 400
    
    try:
        # Lire le contenu du PDF
        pdf_bytes = file.read()
        filename = file.filename
        
        # Extraire le texte du PDF
        texte = lire_pdf_from_bytes(pdf_bytes)
        
        if not texte:
            return jsonify({'error': 'Impossible de lire le PDF. Vérifiez que le fichier est valide'}), 400
        
        # Extraire les informations structurées
        infos = extraire_toutes_infos(texte)
        
        # Extraire les compétences avec statistiques
        competences_data = extraire_competences_avec_stats(texte)
        competences = competences_data.get('competences', [])
        
        # Préparer les données pour la base de données
        cv_data = {
            'user_id': user_id,
            'nom': infos.get('nom', 'Inconnu'),
            'competences': competences,
            'niveau_estime': _determiner_niveau(infos.get('annees_experience', 0)),
            'localisation': infos.get('localisation', ''),
            'annees_experience': infos.get('annees_experience', 0),
            'tags_manuels': competences,  # Utiliser les compétences comme tags
            'texte_complet': texte[:10000],  # Limiter à 10k caractères
            'source_systeme': False
        }
        
        # Sauvegarder dans PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Vérifier si un CV existe déjà
        cur.execute("SELECT id FROM cvs WHERE user_id = %s", (user_id,))
        existing_cv = cur.fetchone()
        
        if existing_cv:
            # Mettre à jour le CV existant
            cur.execute("""
                UPDATE cvs 
                SET nom = %s, competences = %s, niveau_estime = %s, 
                    localisation = %s, annees_experience = %s, 
                    tags_manuels = %s, texte_complet = %s, date_upload = NOW()
                WHERE user_id = %s
                RETURNING id
            """, (
                cv_data['nom'], cv_data['competences'], cv_data['niveau_estime'],
                cv_data['localisation'], cv_data['annees_experience'],
                cv_data['tags_manuels'], cv_data['texte_complet'], user_id
            ))
        else:
            # Insérer un nouveau CV
            cur.execute("""
                INSERT INTO cvs (
                    user_id, nom, competences, niveau_estime, localisation,
                    annees_experience, tags_manuels, texte_complet
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, cv_data['nom'], cv_data['competences'], 
                cv_data['niveau_estime'], cv_data['localisation'],
                cv_data['annees_experience'], cv_data['tags_manuels'],
                cv_data['texte_complet']
            ))
        
        cv_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        # Indexer dans Whoosh
        index_success = indexer_cv_depuis_texte(
            cv_id=str(cv_id),
            texte=texte,
            filename=filename,
            user_id=str(user_id)
        )
        
        if not index_success:
            return jsonify({
                'warning': 'CV sauvegardé mais erreur lors de l\'indexation',
                'cv_id': cv_id,
                'skills': competences,
                'infos': infos
            }), 201
        
        return jsonify({
            'success': True,
            'message': 'CV uploadé, analysé et indexé avec succès',
            'cv_id': cv_id,
            'skills': competences,
            'infos': infos,
            'stats': {
                'nb_competences': len(competences),
                'has_skills_section': competences_data.get('has_skills_section', False),
                'annees_experience': infos.get('annees_experience', 0)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur upload CV: {str(e)}")
        return jsonify({'error': f'Erreur lors du traitement du CV: {str(e)}'}), 500

# ==================== GET CV INFO ====================

@cv_bp.route('/info', methods=['GET'])
def get_cv_info():
    """
    Récupère les informations du CV de l'utilisateur
    """
    if 'user_id' not in session or session.get('user_type') != 'candidat':
        return jsonify({'error': 'Non autorisé'}), 403
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, nom, competences, niveau_estime, localisation,
                   annees_experience, tags_manuels, texte_complet, date_upload
            FROM cvs 
            WHERE user_id = %s
        """, (user_id,))
        
        cv = cur.fetchone()
        cur.close()
        conn.close()
        
        if not cv:
            return jsonify({'exists': False}), 200
        
        # Formater les compétences
        competences = cv[2] if cv[2] else []
        
        # Rechercher dans Whoosh pour des infos supplémentaires
        from whoosh.index import open_dir, exists_in
        from backend.config.settings import CV_INDEX
        
        whoosh_info = {}
        if exists_in(str(CV_INDEX)):
            try:
                ix = open_dir(str(CV_INDEX))
                with ix.searcher() as searcher:
                    from whoosh.qparser import QueryParser
                    parser = QueryParser("doc_id", ix.schema)
                    query = parser.parse(str(cv[0]))
                    results = searcher.search(query, limit=1)
                    
                    if len(results) > 0:
                        hit = results[0]
                        whoosh_info = {
                            'original_filename': hit.get('original_filename', ''),
                            'user_id': hit.get('user_id', ''),
                            'nb_tokens_original': hit.get('nb_tokens_original', 0),
                            'nb_tokens_processed': hit.get('nb_tokens_processed', 0)
                        }
            except Exception as e:
                print(f"⚠️ Erreur lecture Whoosh: {e}")
        
        cv_data = {
            'exists': True,
            'id': cv[0],
            'nom': cv[1],
            'competences': competences,
            'niveau_estime': cv[3],
            'localisation': cv[4],
            'annees_experience': cv[5],
            'tags_manuels': cv[6] if cv[6] else [],
            'texte_preview': (cv[7][:500] + '...') if cv[7] and len(cv[7]) > 500 else (cv[7] or ''),
            'date_upload': cv[8].isoformat() if cv[8] else None,
            'indexed_in_whoosh': bool(whoosh_info),
            'whoosh_info': whoosh_info
        }
        
        return jsonify(cv_data), 200
        
    except Exception as e:
        print(f"❌ Erreur récupération CV: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== DELETE CV ====================

# ==================== DELETE CV ====================

@cv_bp.route('/delete', methods=['DELETE'])
def delete_cv():
    """
    Supprime le CV de l'utilisateur
    """
    if 'user_id' not in session or session.get('user_type') != 'candidat':
        return jsonify({'error': 'Non autorisé'}), 403
    
    user_id = session['user_id']
    
    try:
        # Récupérer l'ID du CV
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM cvs WHERE user_id = %s", (user_id,))
        cv = cur.fetchone()
        
        if not cv:
            return jsonify({'error': 'Aucun CV trouvé'}), 404
        
        cv_id = cv[0]
        
        # NOUVEAU: Supprimer d'abord les candidatures associées
        cur.execute("DELETE FROM candidatures WHERE cv_id = %s", (cv_id,))
        deleted_applications = cur.rowcount  # Utiliser rowcount au lieu de ROW_COUNT()
        
        # Puis supprimer le CV
        cur.execute("DELETE FROM cvs WHERE id = %s", (cv_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Supprimer de Whoosh
        from backend.indexation.cv_indexer import supprimer_cv
        whoosh_success = supprimer_cv(str(cv_id))
        
        return jsonify({
            'success': True,
            'message': f'CV supprimé avec succès ({deleted_applications} candidature(s) associée(s) supprimée(s))',
            'deleted_applications': deleted_applications,
            'deleted_from_postgresql': True,
            'deleted_from_whoosh': whoosh_success
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur suppression CV: {e}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== ANALYZE TEXT ====================

@cv_bp.route('/analyze-text', methods=['POST'])
def analyze_text():
    """
    Analyse un texte de CV (pour preview avant upload)
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    data = request.json
    texte = data.get('text', '')
    
    if not texte or len(texte.strip()) < 50:
        return jsonify({'error': 'Texte trop court (minimum 50 caractères)'}), 400
    
    try:
        # Extraire les informations
        infos = extraire_toutes_infos(texte)
        competences_data = extraire_competences_avec_stats(texte)
        
        return jsonify({
            'infos': infos,
            'competences': competences_data,
            'preview': {
                'nom': infos.get('nom', 'Inconnu'),
                'annees_experience': infos.get('annees_experience', 0),
                'localisation': infos.get('localisation', ''),
                'nb_competences': len(competences_data.get('competences', [])),
                'competences_preview': ', '.join(competences_data.get('competences', [])[:5])
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur analyse texte: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@cv_bp.route('/health', methods=['GET'])
def health_check():
    """
    Vérifie l'état des services nécessaires
    """
    services = {
        'postgresql': False,
        'whoosh_index': False,
        'nltk_resources': False
    }
    
    # Vérifier PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        services['postgresql'] = True
    except Exception as e:
        services['postgresql_error'] = str(e)
    
    # Vérifier Whoosh
    try:
        from backend.config.settings import CV_INDEX
        from whoosh.index import exists_in
        
        services['whoosh_index'] = exists_in(str(CV_INDEX))
        services['whoosh_path'] = str(CV_INDEX)
    except Exception as e:
        services['whoosh_error'] = str(e)
    
    # Vérifier NLTK
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        services['nltk_resources'] = True
    except Exception as e:
        services['nltk_error'] = str(e)
    
    return jsonify({
        'status': 'ok' if all([services['postgresql'], services['nltk_resources']]) else 'degraded',
        'services': services,
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== UTILITY FUNCTIONS ====================

def _determiner_niveau(annees_experience):
    """Détermine le niveau en fonction des années d'expérience"""
    if annees_experience < 2:
        return 'débutant'
    elif annees_experience < 5:
        return 'intermédiaire'
    elif annees_experience < 10:
        return 'senior'
    else:
        return 'expert'