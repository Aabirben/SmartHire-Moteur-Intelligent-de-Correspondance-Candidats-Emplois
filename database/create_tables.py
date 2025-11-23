from connection import get_db_connection

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Table CVs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cvs (
            id SERIAL PRIMARY KEY,
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
            date_upload TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Table Offres
    cur.execute("""
        CREATE TABLE IF NOT EXISTS offres (
            id SERIAL PRIMARY KEY,
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
            date_publication TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Table Matching Results
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
            date_calcul TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tables créées avec succès!")

if __name__ == "__main__":
    create_tables()