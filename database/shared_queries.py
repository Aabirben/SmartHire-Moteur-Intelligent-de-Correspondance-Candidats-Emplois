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