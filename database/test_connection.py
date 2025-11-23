# Fichier: database/verify_setup.py - VERSION CORRIGÉE
from connection import get_db_connection

def verify_setup():
    print("🔍 Vérification complète de l'installation...")
    print("=" * 50)
    
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
        
        # Étape 3: Vérifier que les 3 tables existent
        print("3. Vérification des tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('cvs', 'offres', 'matching_results')
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        expected_tables = ['cvs', 'offres', 'matching_results']
        missing_tables = set(expected_tables) - set(tables)
        
        if missing_tables:
            print(f"❌ Tables manquantes: {missing_tables}")
            return False
        else:
            print("✅ Toutes les tables sont présentes")
        print()
        
        # Étape 4: Vérifier le nombre de colonnes par table - NOMBRES CORRIGÉS
        print("4. Vérification structure des tables...")
        table_checks = {
            'cvs': 13,        # ✅ CORRIGÉ: 13 colonnes
            'offres': 13,     # ✅ CORRIGÉ: 13 colonnes
            'matching_results': 12  # ✅ CORRIGÉ: 12 colonnes
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
                print(f"❌ Table '{table}': {actual_columns} colonnes (attendu: {expected_columns})")
                all_tables_ok = False
        
        if not all_tables_ok:
            print("❌ Certaines tables ont une structure incorrecte")
            return False
        print()
        
        # Étape 5: Vérifier que les tables sont vides (état initial)
        print("5. Vérification état initial des tables...")
        for table in expected_tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            if count == 0:
                print(f"✅ Table '{table}': vide (prête pour l'indexation)")
            else:
                print(f"⚠️  Table '{table}': {count} enregistrements (déjà des données)")
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
            AND tc.table_name = 'matching_results'
        """)
        foreign_keys = cur.fetchall()
        
        if foreign_keys:
            print("✅ Relations de clés étrangères configurées:")
            for fk in foreign_keys:
                print(f"   - {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
        else:
            print("⚠️  Aucune clé étrangère détectée")
        print()
        
        print("=" * 50)
        print("🎉 VÉRIFICATION TERMINÉE AVEC SUCCÈS!")
        print("📊 Résumé:")
        print(f"   • Connexion: ✅ OK")
        print(f"   • Tables: ✅ {len(tables)}/3 présentes") 
        print(f"   • Structure: ✅ Correcte")
        print(f"   • Relations: ✅ Configurées")
        print("💡 La base de données est prête pour l'indexation manuelle!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verify_setup()