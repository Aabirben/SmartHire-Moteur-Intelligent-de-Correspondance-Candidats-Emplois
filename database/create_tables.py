from connection import get_db_connection

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("🗄️  Création des tables avec système d'authentification...")
    
    # Table Users (NOUVELLE)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('candidat', 'recruteur')),
            nom VARCHAR(100) NOT NULL,
            prenom VARCHAR(100) NOT NULL,
            entreprise VARCHAR(150),
            telephone VARCHAR(20),
            date_inscription TIMESTAMP DEFAULT NOW(),
            derniere_connexion TIMESTAMP,
            est_actif BOOLEAN DEFAULT TRUE
        )
    """)
    print("✅ Table 'users' créée")
    
    # Table CVs (MISE À JOUR avec user_id optionnel)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cvs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            nom VARCHAR(100) NOT NULL,
            email VARCHAR(150),
            competences TEXT[],
            niveau_estime VARCHAR(20),
            localisation VARCHAR(100),
            type_contrat VARCHAR(50),
            diplome VARCHAR(100),
            annees_experience INTEGER,
            tags_manuels TEXT[],
            chemin_pdf VARCHAR(255),
            texte_complet TEXT,
            date_upload TIMESTAMP DEFAULT NOW(),
            est_public BOOLEAN DEFAULT TRUE,
            source_systeme BOOLEAN DEFAULT FALSE
        )
    """)
    print("✅ Table 'cvs' mise à jour")
    
    # Table Offres (MISE À JOUR avec user_id optionnel)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS offres (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            titre VARCHAR(200) NOT NULL,
            entreprise VARCHAR(150),
            competences_requises TEXT[],
            description TEXT,
            localisation VARCHAR(100),
            niveau_souhaite VARCHAR(20),
            type_contrat VARCHAR(50),
            diplome_requis VARCHAR(100),
            experience_min INTEGER,
            tags_manuels TEXT[],
            texte_complet TEXT,
            date_publication TIMESTAMP DEFAULT NOW(),
            date_expiration TIMESTAMP,
            est_active BOOLEAN DEFAULT TRUE,
            source_systeme BOOLEAN DEFAULT FALSE
        )
    """)
    print("✅ Table 'offres' mise à jour")
    
    # Table Matching Results (EXISTANTE avec améliorations)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matching_results (
            id SERIAL PRIMARY KEY,
            cv_id INTEGER REFERENCES cvs(id),
            offre_id INTEGER REFERENCES offres(id),
            score_global DECIMAL(5,4),
            score_competences DECIMAL(5,4),
            score_experience DECIMAL(5,4),
            score_localisation DECIMAL(5,4),
            score_description DECIMAL(5,4),
            competences_manquantes TEXT[],
            competences_presentes TEXT[],
            pourcentage_match INTEGER,
            date_calcul TIMESTAMP DEFAULT NOW(),
            vu_par_recruteur BOOLEAN DEFAULT FALSE,
            vu_par_candidat BOOLEAN DEFAULT FALSE
        )
    """)
    print("✅ Table 'matching_results' mise à jour")
    
    # Table Candidatures (NOUVELLE)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidatures (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            offre_id INTEGER REFERENCES offres(id),
            cv_id INTEGER REFERENCES cvs(id),
            date_candidature TIMESTAMP DEFAULT NOW(),
            statut VARCHAR(50) DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'vue', 'entretien', 'rejetee', 'acceptee')),
            message TEXT,
            UNIQUE(user_id, offre_id)
        )
    """)
    print("✅ Table 'candidatures' créée")
    
    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 TOUTES LES TABLES SONT PRÊTES !")
    print("📊 Structure compatible avec les données existantes et nouvelle authentification")

if __name__ == "__main__":
    create_tables()