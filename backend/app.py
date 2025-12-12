from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from backend.routes.cv_routes import cv_bp
from backend.routes.job_routes import job_bp
from backend.routes.search_routes import search_bp
from backend.routes.matching_routes import matching_bp




load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

app.register_blueprint(cv_bp)
app.register_blueprint(job_bp)
app.register_blueprint(search_bp)
app.register_blueprint(matching_bp)



# Configuration PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': os.getenv('DB_SSL')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ==================== AUTHENTIFICATION ====================

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')
        nom = data.get('nom')
        prenom = data.get('prenom')
        entreprise = data.get('entreprise', '')
        telephone = data.get('telephone', '')

        if not all([email, password, user_type, nom, prenom]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Hasher le mot de passe
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO users (email, password_hash, user_type, nom, prenom, entreprise, telephone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, email, user_type, nom, prenom, entreprise
            """, (email, password_hash, user_type, nom, prenom, entreprise, telephone))
            
            user = cur.fetchone()
            conn.commit()
            
            user_data = {
                'id': user[0],
                'email': user[1],
                'user_type': user[2],
                'nom': user[3],
                'prenom': user[4],
                'entreprise': user[5]
            }
            
            # Définir la session
            session['user_id'] = user[0]
            session['user_type'] = user_type
            
            return jsonify({
                'message': 'Registration successful',
                'user': user_data
            }), 201
            
        except psycopg2.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 409
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, email, password_hash, user_type, nom, prenom, entreprise, telephone, est_actif
            FROM users 
            WHERE email = %s
        """, (email,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Vérifier si le compte est actif
        if not user[8]:  # est_actif
            return jsonify({'error': 'Account is deactivated'}), 403

        # Vérifier le mot de passe
        if not bcrypt.check_password_hash(user[2], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Mettre à jour la dernière connexion
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET derniere_connexion = NOW() WHERE id = %s", (user[0],))
        conn.commit()
        cur.close()
        conn.close()

        # Préparer les données utilisateur
        user_data = {
            'id': user[0],
            'email': user[1],
            'user_type': user[3],
            'nom': user[4],
            'prenom': user[5],
            'entreprise': user[6],
            'telephone': user[7]
        }

        # Définir la session
        session['user_id'] = user[0]
        session['user_type'] = user[3]

        return jsonify({
            'message': 'Login successful',
            'user': user_data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, user_type, nom, prenom, entreprise, telephone
            FROM users 
            WHERE id = %s AND est_actif = TRUE
        """, (session['user_id'],))
        
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            user_data = {
                'id': user[0],
                'email': user[1],
                'user_type': user[2],
                'nom': user[3],
                'prenom': user[4],
                'entreprise': user[5],
                'telephone': user[6]
            }
            return jsonify({'authenticated': True, 'user': user_data}), 200
    
    return jsonify({'authenticated': False}), 401

# ==================== PROFIL UTILISATEUR ====================

@app.route('/api/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, email, user_type, nom, prenom, entreprise, telephone, 
               date_inscription, derniere_connexion
        FROM users 
        WHERE id = %s
    """, (session['user_id'],))
    
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_data = {
        'id': user[0],
        'email': user[1],
        'user_type': user[2],
        'nom': user[3],
        'prenom': user[4],
        'entreprise': user[5],
        'telephone': user[6],
        'date_inscription': user[7].isoformat() if user[7] else None,
        'derniere_connexion': user[8].isoformat() if user[8] else None
    }

    return jsonify(user_data), 200

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    nom = data.get('nom')
    prenom = data.get('prenom')
    entreprise = data.get('entreprise', '')
    telephone = data.get('telephone', '')

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE users 
        SET nom = %s, prenom = %s, entreprise = %s, telephone = %s
        WHERE id = %s
        RETURNING id, email, user_type, nom, prenom, entreprise, telephone
    """, (nom, prenom, entreprise, telephone, session['user_id']))
    
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    user_data = {
        'id': user[0],
        'email': user[1],
        'user_type': user[2],
        'nom': user[3],
        'prenom': user[4],
        'entreprise': user[5],
        'telephone': user[6]
    }

    return jsonify({'message': 'Profile updated', 'user': user_data}), 200

# ==================== CV MANAGEMENT ====================

@app.route('/api/candidate/cv', methods=['POST'])
def upload_cv():
    if 'user_id' not in session or session['user_type'] != 'candidat':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.json
        competences = data.get('competences', [])
        niveau_estime = data.get('niveau_estime', 'intermediaire')
        localisation = data.get('localisation', '')
        type_contrat = data.get('type_contrat', '')
        diplome = data.get('diplome', '')
        annees_experience = data.get('annees_experience', 0)
        tags_manuels = data.get('tags_manuels', [])
        texte_complet = data.get('texte_complet', '')

        conn = get_db_connection()
        cur = conn.cursor()

        # Vérifier si un CV existe déjà pour cet utilisateur
        cur.execute("SELECT id FROM cvs WHERE user_id = %s", (session['user_id'],))
        existing_cv = cur.fetchone()

        if existing_cv:
            # Mettre à jour le CV existant
            cur.execute("""
                UPDATE cvs 
                SET competences = %s, niveau_estime = %s, localisation = %s,
                    type_contrat = %s, diplome = %s, annees_experience = %s,
                    tags_manuels = %s, texte_complet = %s, date_upload = NOW()
                WHERE user_id = %s
                RETURNING id
            """, (competences, niveau_estime, localisation, type_contrat, diplome,
                  annees_experience, tags_manuels, texte_complet, session['user_id']))
        else:
            # Créer un nouveau CV
            cur.execute("""
                INSERT INTO cvs (
                    user_id, competences, niveau_estime, localisation,
                    type_contrat, diplome, annees_experience, tags_manuels, texte_complet
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (session['user_id'], competences, niveau_estime, localisation,
                  type_contrat, diplome, annees_experience, tags_manuels, texte_complet))

        cv_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'CV uploaded successfully', 'cv_id': cv_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/cv', methods=['GET'])
def get_cv():
    if 'user_id' not in session or session['user_type'] != 'candidat':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, competences, niveau_estime, localisation, type_contrat,
               diplome, annees_experience, tags_manuels, texte_complet, date_upload
        FROM cvs 
        WHERE user_id = %s
    """, (session['user_id'],))
    
    cv = cur.fetchone()
    cur.close()
    conn.close()

    if not cv:
        return jsonify({'exists': False}), 200

    cv_data = {
        'id': cv[0],
        'competences': cv[1],
        'niveau_estime': cv[2],
        'localisation': cv[3],
        'type_contrat': cv[4],
        'diplome': cv[5],
        'annees_experience': cv[6],
        'tags_manuels': cv[7],
        'texte_complet': cv[8],
        'date_upload': cv[9].isoformat() if cv[9] else None,
        'exists': True
    }

    return jsonify(cv_data), 200

# ==================== JOB MANAGEMENT ====================

@app.route('/api/recruiter/jobs', methods=['POST'])
def create_job():
    if 'user_id' not in session or session['user_type'] != 'recruteur':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.json
        titre = data.get('titre')
        competences_requises = data.get('competences_requises', [])
        description = data.get('description', '')
        localisation = data.get('localisation', '')
        niveau_souhaite = data.get('niveau_souhaite', 'intermediaire')
        type_contrat = data.get('type_contrat', '')
        diplome_requis = data.get('diplome_requis', '')
        experience_min = data.get('experience_min', 0)
        tags_manuels = data.get('tags_manuels', [])

        if not titre:
            return jsonify({'error': 'Job title is required'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO offres (
                user_id, titre, entreprise, competences_requises, description,
                localisation, niveau_souhaite, type_contrat, diplome_requis,
                experience_min, tags_manuels, texte_complet
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (session['user_id'], titre, session.get('entreprise', ''), competences_requises,
              description, localisation, niveau_souhaite, type_contrat, diplome_requis,
              experience_min, tags_manuels, description))

        job_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Job created successfully', 'job_id': job_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recruiter/jobs', methods=['GET'])
def get_recruiter_jobs():
    if 'user_id' not in session or session['user_type'] != 'recruteur':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, titre, entreprise, competences_requises, description,
               localisation, niveau_souhaite, type_contrat, diplome_requis,
               experience_min, tags_manuels, date_publication, est_active
        FROM offres 
        WHERE user_id = %s
        ORDER BY date_publication DESC
    """, (session['user_id'],))
    
    jobs = []
    for row in cur.fetchall():
        jobs.append({
            'id': row[0],
            'titre': row[1],
            'entreprise': row[2],
            'competences_requises': row[3],
            'description': row[4],
            'localisation': row[5],
            'niveau_souhaite': row[6],
            'type_contrat': row[7],
            'diplome_requis': row[8],
            'experience_min': row[9],
            'tags_manuels': row[10],
            'date_publication': row[11].isoformat() if row[11] else None,
            'est_active': row[12]
        })
    
    cur.close()
    conn.close()

    return jsonify(jobs), 200

# ==================== MESSAGING SYSTEM ====================

@app.route('/api/messages', methods=['GET'])
def get_conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Récupérer les conversations
    cur.execute("""
        SELECT 
            m.id as message_id,
            m.sender_id,
            m.receiver_id,
            m.content,
            m.timestamp,
            m.read,
            u1.nom as sender_nom,
            u1.prenom as sender_prenom,
            u1.user_type as sender_type,
            u2.nom as receiver_nom,
            u2.prenom as receiver_prenom,
            u2.user_type as receiver_type
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        JOIN users u2 ON m.receiver_id = u2.id
        WHERE m.sender_id = %s OR m.receiver_id = %s
        ORDER BY m.timestamp DESC
    """, (user_id, user_id))

    # Organiser les conversations
    conversations = {}
    for row in cur.fetchall():
        other_user_id = row[2] if row[1] == user_id else row[1]
        
        if other_user_id not in conversations:
            other_user_name = f"{row[9]} {row[10]}" if row[1] == user_id else f"{row[6]} {row[7]}"
            other_user_type = row[11] if row[1] == user_id else row[8]
            
            conversations[other_user_id] = {
                'participant_id': other_user_id,
                'participant_name': other_user_name,
                'participant_role': other_user_type,
                'last_message': row[3],
                'last_message_time': row[4].isoformat(),
                'unread_count': 0,
                'messages': []
            }
        
        conversations[other_user_id]['messages'].append({
            'id': row[0],
            'sender_id': row[1],
            'sender_name': f"{row[6]} {row[7]}",
            'content': row[3],
            'timestamp': row[4].isoformat(),
            'read': row[5]
        })

        # Compter les messages non lus
        if not row[5] and row[2] == user_id:
            conversations[other_user_id]['unread_count'] += 1

    cur.close()
    conn.close()

    return jsonify(list(conversations.values())), 200

@app.route('/api/messages/<int:other_user_id>', methods=['GET'])
def get_messages(other_user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            m.id,
            m.sender_id,
            m.receiver_id,
            m.content,
            m.timestamp,
            m.read,
            u.nom,
            u.prenom
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.timestamp ASC
    """, (session['user_id'], other_user_id, other_user_id, session['user_id']))

    messages = []
    for row in cur.fetchall():
        messages.append({
            'id': row[0],
            'sender_id': row[1],
            'sender_name': f"{row[6]} {row[7]}",
            'content': row[3],
            'timestamp': row[4].isoformat(),
            'read': row[5]
        })

    # Marquer les messages comme lus
    cur.execute("""
        UPDATE messages 
        SET read = TRUE 
        WHERE receiver_id = %s AND sender_id = %s AND read = FALSE
    """, (session['user_id'], other_user_id))
    
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(messages), 200

@app.route('/api/messages', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({'error': 'Receiver ID and content required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (sender_id, receiver_id, content)
        VALUES (%s, %s, %s)
        RETURNING id, timestamp
    """, (session['user_id'], receiver_id, content))

    message = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'id': message[0],
        'timestamp': message[1].isoformat()
    }), 201

# ==================== JOB SEARCH ====================

@app.route('/api/jobs/search', methods=['GET'])
def search_jobs():
    if 'user_id' not in session or session['user_type'] != 'candidat':
        return jsonify({'error': 'Unauthorized'}), 403

    query = request.args.get('q', '')
    location = request.args.get('location', '')
    skills = request.args.getlist('skills')

    conn = get_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT id, titre, entreprise, competences_requises, description,
               localisation, niveau_souhaite, type_contrat, date_publication
        FROM offres 
        WHERE est_active = TRUE
    """
    params = []

    if query:
        sql += " AND (titre ILIKE %s OR description ILIKE %s)"
        params.extend([f'%{query}%', f'%{query}%'])

    if location:
        sql += " AND localisation ILIKE %s"
        params.append(f'%{location}%')

    if skills:
        sql += " AND competences_requises && %s"
        params.append(skills)

    sql += " ORDER BY date_publication DESC"
    
    cur.execute(sql, params)
    
    jobs = []
    for row in cur.fetchall():
        jobs.append({
            'id': row[0],
            'titre': row[1],
            'entreprise': row[2],
            'competences_requises': row[3],
            'description': row[4],
            'localisation': row[5],
            'niveau_souhaite': row[6],
            'type_contrat': row[7],
            'date_publication': row[8].isoformat() if row[8] else None
        })
    
    cur.close()
    conn.close()

    return jsonify(jobs), 200

# ==================== CANDIDATURES ====================

@app.route('/api/candidate/applications', methods=['POST'])
def apply_for_job():
    if 'user_id' not in session or session['user_type'] != 'candidat':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    offre_id = data.get('offre_id')
    message = data.get('message', '')

    if not offre_id:
        return jsonify({'error': 'Job ID required'}), 400

    # Vérifier si l'utilisateur a un CV
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM cvs WHERE user_id = %s", (session['user_id'],))
    cv = cur.fetchone()

    if not cv:
        return jsonify({'error': 'You need to upload a CV first'}), 400

    cv_id = cv[0]

    try:
        cur.execute("""
            INSERT INTO candidatures (user_id, offre_id, cv_id, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id, date_candidature
        """, (session['user_id'], offre_id, cv_id, message))

        application = cur.fetchone()
        conn.commit()

        return jsonify({
            'message': 'Application submitted successfully',
            'application_id': application[0],
            'date_candidature': application[1].isoformat()
        }), 201

    except psycopg2.IntegrityError:
        return jsonify({'error': 'Already applied for this job'}), 409
    finally:
        cur.close()
        conn.close()

@app.route('/api/candidate/applications', methods=['GET'])
def get_applications():
    if 'user_id' not in session or session['user_type'] != 'candidat':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.offre_id, c.date_candidature, c.statut, c.message,
               o.titre, o.entreprise, o.localisation
        FROM candidatures c
        JOIN offres o ON c.offre_id = o.id
        WHERE c.user_id = %s
        ORDER BY c.date_candidature DESC
    """, (session['user_id'],))

    applications = []
    for row in cur.fetchall():
        applications.append({
            'id': row[0],
            'offre_id': row[1],
            'date_candidature': row[2].isoformat(),
            'statut': row[3],
            'message': row[4],
            'titre': row[5],
            'entreprise': row[6],
            'localisation': row[7]
        })
    
    cur.close()
    conn.close()

    return jsonify(applications), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
