#!/usr/bin/env python3
"""
UPLOAD ET INDEXATION - Pour les nouveaux CVs/offres
"""

import os
import json
import shutil
from datetime import datetime
from database.connection import get_db_connection
from database.shared_queries import insert_system_cv, insert_system_offre

class GestionNouveauxDocuments:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
    
    def ajouter_nouveau_cv(self, pdf_path, donnees_manuelles):
        """
        Ajoute un nouveau CV avec validation manuelle
        
        Args:
            pdf_path: Chemin vers le PDF
            donnees_manuelles: Dict avec les données validées manuellement
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Générer un ID unique
            cv_id = f"cv_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Insérer en base
            cur.execute(insert_system_cv(), (
                donnees_manuelles['nom'],
                donnees_manuelles.get('email', ''),
                donnees_manuelles['competences'],
                donnees_manuelles['niveau_estime'],
                donnees_manuelles['localisation'],
                donnees_manuelles['type_contrat'],
                donnees_manuelles['diplome'],
                donnees_manuelles['annees_experience'],
                donnees_manuelles['tags_manuels'],
                f"/cvs/{os.path.basename(pdf_path)}",
                donnees_manuelles.get('texte_complet', '')
            ))
            
            db_id = cur.fetchone()[0]
            conn.commit()
            
            print(f"✅ Nouveau CV ajouté: ID {db_id}")
            return db_id
            
        except Exception as e:
            print(f"❌ Erreur ajout CV: {e}")
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()
    
    def ajouter_nouvelle_offre(self, donnees_manuelles):
        """
        Ajoute une nouvelle offre avec validation manuelle
        """
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Générer un ID unique
            offre_id = f"offre_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Insérer en base
            cur.execute(insert_system_offre(), (
                donnees_manuelles['titre'],
                donnees_manuelles['entreprise'],
                donnees_manuelles['competences_requises'],
                donnees_manuelles['description'],
                donnees_manuelles['localisation'],
                donnees_manuelles['niveau_souhaite'],
                donnees_manuelles['type_contrat'],
                donnees_manuelles['diplome_requis'],
                donnees_manuelles['experience_min'],
                donnees_manuelles['tags_manuels'],
                donnees_manuelles.get('texte_complet', '')
            ))
            
            db_id = cur.fetchone()[0]
            conn.commit()
            
            print(f"✅ Nouvelle offre ajoutée: ID {db_id}")
            return db_id
            
        except Exception as e:
            print(f"❌ Erreur ajout offre: {e}")
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()
    
    def interface_ajout_manuel(self):
        """Interface pour ajouter manuellement un CV/offre"""
        print("\n" + "="*80)
        print("➕ AJOUT MANUEL DE DOCUMENT")
        print("="*80)
        print("1. 📄 Ajouter un CV")
        print("2. 💼 Ajouter une offre")
        print("3. ↩️ Retour")
        
        choix = input("\n🎯 Choisissez une option: ").strip()
        
        if choix == '1':
            self.ajouter_cv_manuel()
        elif choix == '2':
            self.ajouter_offre_manuelle()
    
    def ajouter_cv_manuel(self):
        """Interface pour ajouter un CV manuellement"""
        print("\n📄 AJOUT MANUEL D'UN CV")
        print("="*50)
        
        donnees = {}
        donnees['nom'] = input("👤 Nom: ").strip()
        donnees['email'] = input("📧 Email: ").strip()
        donnees['localisation'] = input("📍 Localisation: ").strip()
        donnees['niveau_estime'] = input("🎯 Niveau (junior/intermediaire/senior/expert): ").strip()
        donnees['annees_experience'] = int(input("📅 Années d'expérience: ").strip())
        donnees['type_contrat'] = input("📄 Type de contrat (cdi/cdd/freelance): ").strip()
        donnees['diplome'] = input("🎓 Diplôme: ").strip()
        
        competences = input("🛠️ Compétences (séparées par des virgules): ").strip()
        donnees['competences'] = [c.strip() for c in competences.split(',')]
        
        tags = input("🏷️ Tags (séparés par des virgules): ").strip()
        donnees['tags_manuels'] = [t.strip() for t in tags.split(',')]
        
        donnees['texte_complet'] = input("📝 Description complète: ").strip()
        
        # Demander le PDF
        pdf_path = input("📁 Chemin vers le PDF (optionnel): ").strip()
        
        confirmation = input("\n❓ Confirmer l'ajout? (oui/non): ").strip().lower()
        if confirmation == 'oui':
            if pdf_path and os.path.exists(pdf_path):
                resultat = self.ajouter_nouveau_cv(pdf_path, donnees)
            else:
                # Ajouter sans PDF
                donnees['chemin_pdf'] = ""
                resultat = self.ajouter_nouveau_cv("", donnees)
            
            if resultat:
                print("✅ CV ajouté avec succès!")
        else:
            print("❌ Ajout annulé")
    
    def ajouter_offre_manuelle(self):
        """Interface pour ajouter une offre manuellement"""
        print("\n💼 AJOUT MANUEL D'UNE OFFRE")
        print("="*50)
        
        donnees = {}
        donnees['titre'] = input("💼 Titre du poste: ").strip()
        donnees['entreprise'] = input("🏢 Entreprise: ").strip()
        donnees['localisation'] = input("📍 Localisation: ").strip()
        donnees['niveau_souhaite'] = input("🎯 Niveau souhaité (junior/intermediaire/senior/expert): ").strip()
        donnees['experience_min'] = int(input("📅 Expérience minimale (années): ").strip())
        donnees['type_contrat'] = input("📄 Type de contrat (cdi/cdd/freelance): ").strip()
        donnees['diplome_requis'] = input("🎓 Diplôme requis: ").strip()
        
        competences = input("🛠️ Compétences requises (séparées par des virgules): ").strip()
        donnees['competences_requises'] = [c.strip() for c in competences.split(',')]
        
        tags = input("🏷️ Tags (séparés par des virgules): ").strip()
        donnees['tags_manuels'] = [t.strip() for t in tags.split(',')]
        
        donnees['description'] = input("📝 Description: ").strip()
        donnees['texte_complet'] = donnees['description']
        
        confirmation = input("\n❓ Confirmer l'ajout? (oui/non): ").strip().lower()
        if confirmation == 'oui':
            resultat = self.ajouter_nouvelle_offre(donnees)
            if resultat:
                print("✅ Offre ajoutée avec succès!")
        else:
            print("❌ Ajout annulé")

if __name__ == "__main__":
    gestionnaire = GestionNouveauxDocuments()
    gestionnaire.interface_ajout_manuel()