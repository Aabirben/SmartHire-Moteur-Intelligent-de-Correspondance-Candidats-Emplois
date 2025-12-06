#!/usr/bin/env python3
"""
LANCEUR PRINCIPAL - Processus d'indexation manuelle complet
"""

import os
import json
import sys
from datetime import datetime

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from database.shared_queries import insert_system_cv, insert_system_offre

class OrchestrateurIndexation:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.chemins = {
            'traitement_auto': os.path.join(self.base_path, 'traitement_auto'),
            'verification_manuelle': os.path.join(self.base_path, 'verification_manuelle'), 
            'resultats_finals': os.path.join(self.base_path, 'resultats_finals')
        }
        
        # Créer les dossiers
        for chemin in self.chemins.values():
            os.makedirs(chemin, exist_ok=True)
    
    def preparer_donnees_validation(self):
        """Prépare les données pour la validation manuelle"""
        print("\n" + "="*80)
        print("PRÉPARATION DES DONNÉES POUR VALIDATION")
        print("="*80)
        
        fichier_json = os.path.join(self.chemins['traitement_auto'], 'resultats_indexation_auto.json')
        
        if not os.path.exists(fichier_json):
            print("❌ Fichier JSON introuvable!")
            print("📋 Exécutez d'abord: python index-manuelle/traitement_auto/generer_json_auto.py")
            return None, None
        
        with open(fichier_json, 'r', encoding='utf-8') as f:
            resultats = json.load(f)
        
        cvs_auto = resultats.get('cvs_auto', {})
        offres_auto = resultats.get('offres_auto', {})
        
        print(f"✅ {len(cvs_auto)} CVs et {len(offres_auto)} offres chargés")
        
        # Préparer les données pour validation (statut = 'a_corriger')
        cvs_a_valider = {}
        for cv_id, cv_data in cvs_auto.items():
            cv_data['statut'] = 'a_corriger'
            cvs_a_valider[cv_id] = cv_data
        
        offres_a_valider = {}
        for offre_id, offre_data in offres_auto.items():
            offre_data['statut'] = 'a_corriger'
            offres_a_valider[offre_id] = offre_data
        
        # Sauvegarder pour validation
        with open(os.path.join(self.chemins['verification_manuelle'], 'cvs_a_corriger.json'), 'w', encoding='utf-8') as f:
            json.dump(cvs_a_valider, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(self.chemins['verification_manuelle'], 'offres_a_corriger.json'), 'w', encoding='utf-8') as f:
            json.dump(offres_a_valider, f, indent=2, ensure_ascii=False)
        
        print("📁 Fichiers de validation créés:")
        print(f"   • {os.path.join(self.chemins['verification_manuelle'], 'cvs_a_corriger.json')}")
        print(f"   • {os.path.join(self.chemins['verification_manuelle'], 'offres_a_corriger.json')}")
        
        return cvs_a_valider, offres_a_valider
    
    def lancer_validation_manuelle(self):
        """Lance l'interface de validation"""
        print("\n" + "="*80)
        print("VALIDATION MANUELLE")
        print("="*80)
        
        # Importer et lancer l'interface de validation
        try:
            from verification_manuelle.correcteur_manuel import InterfaceValidation
            validateur = InterfaceValidation(self.chemins)
            validateur.lancer_interface()
        except Exception as e:
            print(f"❌ Erreur interface validation: {e}")
            print("📋 Validation manuelle - Instructions:")
            print("   1. Ouvrez les fichiers:")
            print(f"      - {os.path.join(self.chemins['verification_manuelle'], 'cvs_a_corriger.json')}")
            print(f"      - {os.path.join(self.chemins['verification_manuelle'], 'offres_a_corriger.json')}")
            print("   2. Modifiez les champs si nécessaire")
            print("   3. Changez 'statut' de 'a_corriger' à 'corrige' pour les éléments validés")
            input("\n⏎ Appuyez sur Entrée quand la validation est terminée...")
        
        # Charger les résultats après validation
        try:
            with open(os.path.join(self.chemins['verification_manuelle'], 'cvs_a_corriger.json'), 'r', encoding='utf-8') as f:
                cvs_corriges = json.load(f)
            
            with open(os.path.join(self.chemins['verification_manuelle'], 'offres_a_corriger.json'), 'r', encoding='utf-8') as f:
                offres_corrigees = json.load(f)
            
            cvs_valides = sum(1 for cv in cvs_corriges.values() if cv.get('statut') == 'corrige')
            offres_valides = sum(1 for offre in offres_corrigees.values() if offre.get('statut') == 'corrige')
            
            print(f"📊 Validation terminée:")
            print(f"   • CVs validés: {cvs_valides}/{len(cvs_corriges)}")
            print(f"   • Offres validées: {offres_valides}/{len(offres_corrigees)}")
            
            return cvs_corriges, offres_corrigees
            
        except Exception as e:
            print(f"❌ Erreur chargement résultats validation: {e}")
            return {}, {}
    
    def inserer_en_base(self, cvs_corriges, offres_corrigees):
        """Insère les données validées en base"""
        print("\n" + "="*80)
        print("INSERTION BASE DE DONNÉES")
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
        
        # Sauvegarde résultats
        with open(os.path.join(self.chemins['resultats_finals'], 'mapping_ids.json'), 'w') as f:
            json.dump(mapping_ids, f, indent=2)
        
        with open(os.path.join(self.chemins['resultats_finals'], 'cvs_enrichis.json'), 'w', encoding='utf-8') as f:
            json.dump(cvs_corriges, f, indent=2, ensure_ascii=False)
        
        with open(os.path.join(self.chemins['resultats_finals'], 'offres_enrichies.json'), 'w', encoding='utf-8') as f:
            json.dump(offres_corrigees, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"   • CVs insérés: {cvs_inseres}")
        print(f"   • Offres insérées: {offres_inserees}")
        print(f"   • Total: {cvs_inseres + offres_inserees}")
        
        print(f"\n💾 FICHIERS SAUVEGARDÉS:")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'mapping_ids.json')}")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'cvs_enrichis.json')}")
        print(f"   • {os.path.join(self.chemins['resultats_finals'], 'offres_enrichies.json')}")
        
        return mapping_ids
    
    def executer(self):
        """Exécute le processus complet"""
        print("🚀 DÉMARRAGE INDEXATION MANUELLE")
        print("="*80)
        
        try:
            # 1. Préparation données
            cvs_auto, offres_auto = self.preparer_donnees_validation()
            if not cvs_auto:
                return
            
            # 2. Validation manuelle
            input("\n⏎ Appuyez sur Entrée pour lancer la validation manuelle...")
            cvs_corriges, offres_corrigees = self.lancer_validation_manuelle()
            
            if not cvs_corriges:
                print("❌ Aucune donnée à insérer")
                return
            
            # 3. Insertion base
            input("\n⏎ Appuyez sur Entrée pour l'insertion en base...")
            resultat_insertion = self.inserer_en_base(cvs_corriges, offres_corrigees)
            
            print("\n🎉 PROCESSUS TERMINÉ AVEC SUCCÈS!")
            print("📋 Les données sont maintenant disponibles pour:")
            print("   • Matching booléen")
            print("   • Matching vectoriel") 
            print("   • Recherche par compétences")
            
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    orchestrateur = OrchestrateurIndexation()
    orchestrateur.executer()