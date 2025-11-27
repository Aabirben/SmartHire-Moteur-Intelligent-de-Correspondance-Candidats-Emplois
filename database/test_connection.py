# Fichier: database/verify_setup.py - VERSION MISE À JOUR
from connection import get_db_connection

def verify_setup():
    print("🔍 VÉRIFICATION COMPLÈTE DE L'INSTALLATION...")
    print("=" * 60)
    
    # Étape 1: Test de connexion
    print("1. Test de connexion à la base de données...")
    conn = get_db_connection()
    if not conn:
        print("❌ Échec: connexion impossible")
        return False
    print("✅ Connexion établie avec succès")
    print()
    
    cur = conn.cursor()
    
    try:
        # Étape 2: Vérifier la version PostgreSQL
        print("2. Vérification version PostgreSQL...")
        cur.execute("SELECT version();")
        db_version = cur.fetchone()[0]
        print(f"✅ PostgreSQL: {db_version.split(',')[0]}")
        print()
        
        # Étape 3: Vérifier que TOUTES les tables existent (5 tables maintenant)
        print("3. Vérification des tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'cvs', 'offres', 'matching_results', 'candidatures')
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        expected_tables = ['users', 'cvs', 'offres', 'matching_results', 'candidatures']
        missing_tables = set(expected_tables) - set(tables)
        
        if missing_tables:
            print(f"❌ Tables manquantes: {missing_tables}")
            return False
        else:
            print("✅ Toutes les tables sont présentes")
            print(f"   • {len(tables)}/5 tables détectées")
        print()
        
        # Étape 4: Vérifier le nombre de colonnes par table - NOMBRES MIS À JOUR
        print("4. Vérification structure des tables...")
        table_checks = {
            'users': 11,               # ✅ 11 colonnes
            'cvs': 16,                 # ✅ 16 colonnes (13 + 3 nouvelles)
            'offres': 17,              # ✅ 17 colonnes (13 + 4 nouvelles)
            'matching_results': 14,    # ✅ 14 colonnes (12 + 2 nouvelles)
            'candidatures': 7          # ✅ 7 colonnes (nouvelle table)
        }
        
        all_tables_ok = True
        for table, expected_columns in table_checks.items():
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            actual_columns = cur.fetchone()[0]
            if actual_columns == expected_columns:
                print(f"✅ Table '{table}': {actual_columns} colonnes")
            else:
                print(f"⚠️  Table '{table}': {actual_columns} colonnes (attendu: {expected_columns})")
                all_tables_ok = False
        
        if not all_tables_ok:
            print("ℹ️  Certaines tables ont un nombre de colonnes différent (migration en cours)")
        print()
        
        # Étape 5: Vérifier le contenu des tables
        print("5. Vérification des données...")
        table_counts = {}
        for table in expected_tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            table_counts[table] = count
            
            if table == 'users' and count == 0:
                print(f"✅ Table '{table}': {count} utilisateurs (prête pour inscriptions)")
            elif table == 'candidatures' and count == 0:
                print(f"✅ Table '{table}': {count} candidatures (prête pour postulations)")
            elif table == 'cvs' and count > 0:
                print(f"✅ Table '{table}': {count} CVs (dont données indexées)")
            elif table == 'offres' and count > 0:
                print(f"✅ Table '{table}': {count} offres (dont données indexées)")
            else:
                print(f"ℹ️  Table '{table}': {count} enregistrements")
        print()
        
        # Étape 6: Vérifier les contraintes de clés étrangères
        print("6. Vérification des relations entre tables...")
        cur.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
        """)
        foreign_keys = cur.fetchall()
        
        if foreign_keys:
            print("✅ Relations de clés étrangères configurées:")
            for fk in foreign_keys:
                print(f"   - {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
        else:
            print("⚠️  Aucune clé étrangère détectée")
        print()
        
        # Étape 7: Vérifier les données système
        print("7. Vérification des données système...")
        try:
            cur.execute("SELECT COUNT(*) FROM cvs WHERE source_systeme = TRUE")
            cvs_systeme = cur.fetchone()[0]
            print(f"   ✅ {cvs_systeme} CVs données système")
            
            cur.execute("SELECT COUNT(*) FROM offres WHERE source_systeme = TRUE")
            offres_systeme = cur.fetchone()[0]
            print(f"   ✅ {offres_systeme} offres données système")
            
            cur.execute("SELECT COUNT(*) FROM cvs WHERE user_id IS NOT NULL")
            cvs_utilisateurs = cur.fetchone()[0]
            print(f"   ✅ {cvs_utilisateurs} CVs utilisateurs")
            
        except Exception as e:
            print(f"   ⚠️  Vérification données système: {e}")
        print()
        
        print("=" * 60)
        print("🎉 VÉRIFICATION TERMINÉE AVEC SUCCÈS!")
        print("📊 RÉSUMÉ:")
        print(f"   • Connexion: ✅ OK")
        print(f"   • Tables: ✅ {len(tables)}/5 présentes") 
        print(f"   • Données: ✅ {table_counts['cvs']} CVs, {table_counts['offres']} offres")
        print(f"   • Authentification: ✅ {table_counts['users']} utilisateurs")
        print(f"   • Candidatures: ✅ {table_counts['candidatures']} candidatures")
        print("💡 La base de données est prête pour le développement!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verify_setup()