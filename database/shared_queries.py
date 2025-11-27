"""
 REQUÊTES PARTAGÉES POUR TOUTE L'ÉQUIPE

Ce fichier contient les requêtes SQL standardisées que tous les membres
peuvent utiliser pour éviter la duplication de code et garantir la cohérence.
"""

# ==================== REQUÊTES POUR PERSONNE 3 (MOTEUR) ====================

def get_all_cvs():
    """
    Récupère tous les CVs pour le matching automatique
    Utilisation: Personne 3 (Moteur de recherche)
    """
    return """
        SELECT id, competences, niveau_estime, localisation, tags_manuels, texte_complet
        FROM cvs
    """

def get_all_offres():
    """
    Récupère toutes les offres pour le matching automatique  
    Utilisation: Personne 3 (Moteur de recherche)
    """
    return """
        SELECT id, competences_requises, niveau_souhaite, localisation, tags_manuels, texte_complet
        FROM offres
    """

def insert_matching_result():
    """
    Insère un résultat de matching dans la table
    Utilisation: Personne 2 (Moteur de recherche)
    """
    return """
        INSERT INTO matching_results (
            cv_id, offre_id, score_global, score_competences, 
            score_experience, score_localisation, score_description,
            competences_manquantes, competences_presentes, pourcentage_match
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

# ==================== REQUÊTES POUR PERSONNE 4 (FRONTEND) ====================

def search_cvs_by_competences(competences):
    """
    Recherche des CVs par compétences (pour l'interface recruteur)
    Utilisation: Personne 4 (Frontend)
    """
    return """
        SELECT id, nom, competences, niveau_estime, localisation
        FROM cvs 
        WHERE competences && %s
        ORDER BY niveau_estime DESC
    """, [competences]

def search_offres_by_tags(tags):
    """
    Recherche des offres par tags (pour l'interface candidat)
    Utilisation: Personne 4 (Frontend)
    """
    return """
        SELECT id, titre, entreprise, competences_requises, localisation
        FROM offres 
        WHERE tags_manuels && %s
        ORDER BY date_publication DESC
    """, [tags]

def get_matching_results_for_cv(cv_id):
    """
    Récupère les résultats de matching pour un CV spécifique
    Utilisation: Personne 4 (Frontend) - Page de détail CV
    """
    return """
        SELECT mr.*, o.titre, o.entreprise 
        FROM matching_results mr
        JOIN offres o ON mr.offre_id = o.id
        WHERE mr.cv_id = %s
        ORDER BY mr.score_global DESC
    """, [cv_id]

def get_matching_results_for_offre(offre_id):
    """
    Récupère les résultats de matching pour une offre spécifique  
    Utilisation: Personne 4 (Frontend) - Page de détail offre
    """
    return """
        SELECT mr.*, c.nom, c.competences
        FROM matching_results mr
        JOIN cvs c ON mr.cv_id = c.id
        WHERE mr.offre_id = %s
        ORDER BY mr.score_global DESC
    """, [offre_id]

# ==================== REQUÊTES POUR PERSONNE 2  ====================

def insert_cv():
    """
    Insère un CV enrichi dans la base
    Utilisation: Personne 2 (Indexation manuelle)
    """
    return """
        INSERT INTO cvs (
            nom, email, competences, niveau_estime, localisation,
            type_contrat, diplome, annees_experience, tags_manuels,
            chemin_pdf, texte_complet
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

def insert_offre():
    """
    Insère une offre enrichie dans la base
    Utilisation: Personne 3 (Indexation manuelle)  
    """
    return """
        INSERT INTO offres (
            titre, entreprise, competences_requises, description,
            localisation, niveau_souhaite, type_contrat, diplome_requis,
            experience_min, tags_manuels, texte_complet
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

# ==================== REQUÊTES STATISTIQUES ====================

def get_stats_cvs():
    """
    Statistiques sur les CVs (pour dashboard)
    """
    return """
        SELECT 
            COUNT(*) as total_cvs,
            COUNT(DISTINCT localisation) as villes,
            AVG(annees_experience) as experience_moyenne,
            MODE() WITHIN GROUP (ORDER BY niveau_estime) as niveau_commun
        FROM cvs
    """

def get_stats_offres():
    """
    Statistiques sur les offres (pour dashboard)
    """
    return """
        SELECT 
            COUNT(*) as total_offres,
            COUNT(DISTINCT localisation) as villes,
            MODE() WITHIN GROUP (ORDER BY niveau_souhaite) as niveau_commun
        FROM offres
    """

# ==================== REQUÊTES AUTHENTIFICATION ====================

def create_user():
    """
    Crée un nouvel utilisateur
    """
    return """
        INSERT INTO users (email, password_hash, user_type, nom, prenom, entreprise, telephone)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

def get_user_by_email():
    """
    Récupère un utilisateur par email
    """
    return """
        SELECT id, email, password_hash, user_type, nom, prenom, entreprise, est_actif
        FROM users 
        WHERE email = %s
    """

def update_last_login():
    """
    Met à jour la dernière connexion
    """
    return """
        UPDATE users 
        SET derniere_connexion = NOW() 
        WHERE id = %s
    """

# ==================== REQUÊTES SPÉCIFIQUES SYSTÈME ====================

def get_system_cvs():
    """
    Récupère les CVs du système (indexation manuelle)
    """
    return """
        SELECT id, nom, email, competences, niveau_estime, localisation, 
               tags_manuels, texte_complet
        FROM cvs 
        WHERE source_systeme = TRUE AND est_public = TRUE
    """

def get_system_offres():
    """
    Récupère les offres du système (indexation manuelle)
    """
    return """
        SELECT id, titre, entreprise, competences_requises, localisation,
               niveau_souhaite, tags_manuels, texte_complet
        FROM offres 
        WHERE source_systeme = TRUE AND est_active = TRUE
    """

def insert_system_cv():
    """
    Insère un CV du système (sans user_id)
    """
    return """
        INSERT INTO cvs (
            nom, email, competences, niveau_estime, localisation,
            type_contrat, diplome, annees_experience, tags_manuels,
            chemin_pdf, texte_complet, source_systeme, est_public
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
        RETURNING id
    """

def insert_system_offre():
    """
    Insère une offre du système (sans user_id)
    """
    return """
        INSERT INTO offres (
            titre, entreprise, competences_requises, description,
            localisation, niveau_souhaite, type_contrat, diplome_requis,
            experience_min, tags_manuels, texte_complet, source_systeme, 
            est_active, date_expiration
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE, NOW() + INTERVAL '90 days')
        RETURNING id
    """

# ==================== REQUÊTES CANDIDATURES ====================

def create_candidature():
    """
    Crée une nouvelle candidature
    """
    return """
        INSERT INTO candidatures (user_id, offre_id, cv_id, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """

def get_candidatures_by_user():
    """
    Récupère les candidatures d'un utilisateur
    """
    return """
        SELECT c.*, o.titre, o.entreprise, o.localisation
        FROM candidatures c
        JOIN offres o ON c.offre_id = o.id
        WHERE c.user_id = %s
        ORDER BY c.date_candidature DESC
    """

def get_candidatures_for_offre():
    """
    Récupère les candidatures pour une offre (recruteur)
    """
    return """
        SELECT c.*, u.nom, u.prenom, u.email, cv.competences, cv.niveau_estime
        FROM candidatures c
        JOIN users u ON c.user_id = u.id
        JOIN cvs cv ON c.cv_id = cv.id
        WHERE c.offre_id = %s
        ORDER BY c.date_candidature DESC
    """
