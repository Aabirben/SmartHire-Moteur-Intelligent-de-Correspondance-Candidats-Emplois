#!/usr/bin/env python3
"""
INSERTION MANUELLE - Validation et insertion directe en base
"""

import os
import json
import sys
import traceback
from datetime import datetime

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from database.shared_queries import insert_system_cv, insert_system_offre

class InsertionManuelle:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.chemins = {
            'verification_manuelle': os.path.join(self.base_path, 'verification_manuelle'),
            'resultats_finals': os.path.join(self.base_path, 'resultats_finals')
        }
    
    def nettoyer_base_donnees(self):
        """Nettoie complètement la base de données des anciennes données"""
        print("\n" + "="*80)
        print("🧹 NETTOYAGE DE LA BASE DE DONNÉES")
        print("="*80)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Supprimer les données dans l'ordre pour respecter les contraintes
            print("🗑️  Suppression des données existantes...")
            
            # Commencer par les tables dépendantes
            cur.execute("DELETE FROM matching_results;")
            print("✅ matching_results nettoyée")
            
            cur.execute("DELETE FROM candidatures;")
            print("✅ candidatures nettoyée")
            
            # Puis les tables principales
            cur.execute("DELETE FROM cvs WHERE source_systeme = TRUE;")
            print("✅ CVs système nettoyés")
            
            cur.execute("DELETE FROM offres WHERE source_systeme = TRUE;")
            print("✅ Offres système nettoyées")
            
            conn.commit()
            print("🎉 Base de données nettoyée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
            conn.rollback()
            traceback.print_exc()
        finally:
            cur.close()
            conn.close()
    
    def verifier_donnees_manuelles(self):
        """Vérifie et charge les données manuellement corrigées"""
        print("\n" + "="*80)
        print("📋 VÉRIFICATION DES DONNÉES MANUELLES")
        print("="*80)
        
        # Chemins des fichiers
        cvs_path = os.path.join(self.chemins['verification_manuelle'], 'cvs_a_corriger.json')
        offres_path = os.path.join(self.chemins['verification_manuelle'], 'offres_a_corriger.json')
        
        if not os.path.exists(cvs_path) or not os.path.exists(offres_path):
            print("❌ Fichiers de données manquants!")
            print(f"   Assurez-vous que ces fichiers existent:")
            print(f"   • {cvs_path}")
            print(f"   • {offres_path}")
            return None, None
        
        # Charger les CVs
        with open(cvs_path, 'r', encoding='utf-8') as f:
            cvs_corriges = json.load(f)
        
        # Charger les offres
        with open(offres_path, 'r', encoding='utf-8') as f:
            offres_corrigees = json.load(f)
        
        # Compter les éléments validés
        cvs_valides = sum(1 for cv in cvs_corriges.values() if cv.get('statut') == 'corrige')
        offres_valides = sum(1 for offre in offres_corrigees.values() if offre.get('statut') == 'corrige')
        
        print(f"📊 Données chargées:")
        print(f"   • CVs total: {len(cvs_corriges)}")
        print(f"   • CVs validés (statut='corrige'): {cvs_valides}")
        print(f"   • Offres total: {len(offres_corrigees)}")
        print(f"   • Offres validées (statut='corrige'): {offres_valides}")
        
        if cvs_valides == 0 and offres_valides == 0:
            print("\n⚠️  ATTENTION: Aucune donnée avec statut='corrige'!")
            print("   Modifiez les fichiers JSON et changez 'statut' à 'corrige' pour les éléments à insérer")
            return None, None
        
        return cvs_corriges, offres_corrigees
    
    def inserer_donnees_base(self, cvs_corriges, offres_corrigees):
        """Insère les données validées en base de données"""
        print("\n" + "="*80)
        print("💾 INSERTION EN BASE DE DONNÉES")
        print("="*80)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        mapping_ids = {
            "cvs": {},
            "offres": {},
            "metadata": {
                "date_insertion": datetime.now().isoformat(),
                "total_cvs": 0,
                "total_offres": 0
            }
        }
        
        # Insertion CVs
        print("📄 INSERTION DES CVs...")
        cvs_inseres = 0
        for cv_id, cv_data in cvs_corriges.items():
            if cv_data.get('statut') == 'corrige':
                try:
                    cur.execute(insert_system_cv(), (
                        cv_data['nom'], 
                        cv_data.get('email', ''), 
                        cv_data['competences'],
                        cv_data['niveau_estime'], 
                        cv_data['localisation'],
                        cv_data['type_contrat'], 
                        cv_data['diplome'],
                        cv_data['annees_experience'], 
                        cv_data['tags_manuels'],
                        cv_data['chemin_pdf'], 
                        cv_data['texte_complet']
                    ))
                    db_id = cur.fetchone()[0]
                    mapping_ids["cvs"][cv_id] = db_id
                    cvs_inseres += 1
                    print(f"   ✅ {cv_id} → ID {db_id}")
                except Exception as e:
                    print(f"   ❌ {cv_id}: {e}")
        
        # Insertion offres
        print("\n💼 INSERTION DES OFFRES...")
        offres_inserees = 0
        for offre_id, offre_data in offres_corrigees.items():
            if offre_data.get('statut') == 'corrige':
                try:
                    cur.execute(insert_system_offre(), (
                        offre_data['titre'], 
                        offre_data['entreprise'],
                        offre_data['competences_requises'], 
                        offre_data['description'],
                        offre_data['localisation'], 
                        offre_data['niveau_souhaite'],
                        offre_data['type_contrat'], 
                        offre_data['diplome_requis'],
                        offre_data['experience_min'], 
                        offre_data['tags_manuels'],
                        offre_data['texte_complet']
                    ))
                    db_id = cur.fetchone()[0]
                    mapping_ids["offres"][offre_id] = db_id
                    offres_inserees += 1
                    print(f"   ✅ {offre_id} → ID {db_id}")
                except Exception as e:
                    print(f"   ❌ {offre_id}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Mettre à jour les métadonnées
        mapping_ids["metadata"]["total_cvs"] = cvs_inseres
        mapping_ids["metadata"]["total_offres"] = offres_inserees
        
        return mapping_ids, cvs_inseres, offres_inserees
    
    def sauvegarder_resultats(self, mapping_ids, cvs_corriges, offres_corrigees):
        """Sauvegarde les résultats finaux"""
        print("\n" + "="*80)
        print("💾 SAUVEGARDE DES RÉSULTATS")
        print("="*80)
        
        # Sauvegarde mapping IDs
        with open(os.path.join(self.chemins['resultats_finals'], 'mapping_ids.json'), 'w') as f:
            json.dump(mapping_ids, f, indent=2)
        
        # Sauvegarde CVs enrichis
        with open(os.path.join(self.chemins['resultats_finals'], 'cvs_enrichis.json'), 'w', encoding='utf-8') as f:
            json.dump(cvs_corriges, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde offres enrichies
        with open(os.path.join(self.chemins['resultats_finals'], 'offres_enrichies.json'), 'w', encoding='utf-8') as f:
            json.dump(offres_corrigees, f, indent=2, ensure_ascii=False)
        
        print("✅ Fichiers sauvegardés:")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'mapping_ids.json')}")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'cvs_enrichis.json')}")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'offres_enrichies.json')}")
    
    def executer(self):
        """Exécute le processus complet d'insertion manuelle"""
        print("🚀 DÉMARRAGE INSERTION MANUELLE")
        print("="*80)
        
        try:
            # 1. Nettoyage de la base
            confirmation = input("🧹 Voulez-vous nettoyer la base de données avant l'insertion? (oui/non): ").strip().lower()
            if confirmation == 'oui':
                self.nettoyer_base_donnees()
            else:
                print("⏭️  Nettoyage ignoré")
            
            # 2. Vérification des données manuelles
            input("\n⏎ Appuyez sur Entrée pour vérifier les données manuelles...")
            cvs_corriges, offres_corrigees = self.verifier_donnees_manuelles()
            
            if not cvs_corriges:
                print("❌ Processus arrêté: aucune donnée valide trouvée")
                return
            
            # 3. Insertion en base
            input("\n⏎ Appuyez sur Entrée pour lancer l'insertion en base...")
            mapping_ids, cvs_inseres, offres_inserees = self.inserer_donnees_base(cvs_corriges, offres_corrigees)
            
            # 4. Sauvegarde des résultats
            self.sauvegarder_resultats(mapping_ids, cvs_corriges, offres_corrigees)
            
            # 5. Résumé final
            print("\n" + "="*80)
            print("🎉 PROCESSUS TERMINÉ AVEC SUCCÈS!")
            print("="*80)
            print(f"📊 RÉSULTATS FINALS:")
            print(f"   • CVs insérés: {cvs_inseres}")
            print(f"   • Offres insérées: {offres_inserees}")
            print(f"   • Total documents: {cvs_inseres + offres_inserees}")
            
            print(f"\n📋 FICHIERS IMPORTANTS:")
            print(f"   • cvs_enrichis.json → Données finales des CVs")
            print(f"   • offres_enrichies.json → Données finales des offres") 
            print(f"   • mapping_ids.json → Correspondance IDs pour le matching")
            
            print(f"\n🎯 PRÊT POUR LE MATCHING:")
            print(f"   • Les données sont maintenant disponibles en base")
            print(f"   • Utilisez mapping_ids.json pour le matching booléen/vectoriel")
            
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    insertion = InsertionManuelle()
    insertion.executer()