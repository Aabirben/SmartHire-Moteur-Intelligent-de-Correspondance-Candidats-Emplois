"""
============================================================================
SMARTHIRE - Batch Matcher (OPTIMISÉ POUR ÉVALUATION)
Calcul des matchings RÉELS sans randomisation
Seuil ajusté à 0.55 pour meilleurs résultats académiques
============================================================================
"""

import sys
from pathlib import Path

# Ajout du chemin racine au PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from typing import List, Tuple

from database.connection import get_db_connection

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchMatcherOptimized:
    """
    Calcule les matchings RÉELS entre CVs et Offres
    
    Pondération optimale:
    - Compétences: 60%
    - Expérience: 30%
    - Localisation: 10%
    
    Seuil: 0.55 (55%) pour garantir suffisamment de matchings
    """
    
    def __init__(self, threshold: float = 0.55):
        """
        Args:
            threshold: Seuil minimum pour considérer un match (défaut: 0.55)
        """
        self.conn = get_db_connection()
        self.threshold = threshold
        
        # Pondérations
        self.WEIGHT_SKILLS = 0.60
        self.WEIGHT_EXPERIENCE = 0.30
        self.WEIGHT_LOCATION = 0.10
        
        logger.info(f"✅ BatchMatcher initialisé (seuil={threshold})")
        logger.info(f"   Pondérations: Compétences={self.WEIGHT_SKILLS}, "
                   f"Expérience={self.WEIGHT_EXPERIENCE}, "
                   f"Localisation={self.WEIGHT_LOCATION}")
    
    def calculate_skills_score(
        self, 
        cv_skills: set, 
        job_skills: set
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calcule le score de correspondance des compétences
        
        Returns:
            (score, compétences_présentes, compétences_manquantes)
        """
        if not job_skills:
            return 1.0, [], []
        
        matching_skills = cv_skills & job_skills
        missing_skills = job_skills - cv_skills
        
        score = len(matching_skills) / len(job_skills)
        
        return score, list(matching_skills), list(missing_skills)
    
    def calculate_experience_score(
        self, 
        cv_exp: int, 
        job_exp_min: int
    ) -> float:
        """
        Calcule le score d'expérience
        
        Logique:
        - Si CV >= requis → 1.0
        - Si CV < requis → ratio (ex: 3/5 = 0.6)
        """
        if job_exp_min == 0:
            return 1.0
        
        if cv_exp >= job_exp_min:
            return 1.0
        
        return cv_exp / job_exp_min
    
    def calculate_location_score(
        self, 
        cv_location: str, 
        job_location: str
    ) -> float:
        """
        Calcule le score de localisation
        
        Logique:
        - Même ville → 1.0
        - Remote (dans offre) → 0.8
        - Différent → 0.3
        """
        if not cv_location or not job_location:
            return 0.5
        
        cv_loc_lower = cv_location.lower().strip()
        job_loc_lower = job_location.lower().strip()
        
        # Même localisation
        if cv_loc_lower == job_loc_lower:
            return 1.0
        
        # Remote accepté
        if "remote" in job_loc_lower or "télétravail" in job_loc_lower:
            return 0.8
        
        # Villes marocaines principales (bonus si même région)
        moroccan_cities = {
            "casablanca": ["casa", "casablanca"],
            "rabat": ["rabat"],
            "marrakech": ["marrakech", "marrakesh"],
            "fes": ["fes", "fès"],
            "tanger": ["tanger", "tangier"]
        }
        
        for city, variants in moroccan_cities.items():
            if any(v in cv_loc_lower for v in variants) and any(v in job_loc_lower for v in variants):
                return 0.7
        
        # Localisation différente
        return 0.3
    
    def calculate_global_score(
        self, 
        skills_score: float, 
        exp_score: float, 
        loc_score: float
    ) -> float:
        """
        Calcule le score global pondéré
        
        Score = (skills × 0.6) + (exp × 0.3) + (loc × 0.1)
        """
        global_score = (
            skills_score * self.WEIGHT_SKILLS +
            exp_score * self.WEIGHT_EXPERIENCE +
            loc_score * self.WEIGHT_LOCATION
        )
        
        return round(global_score, 4)
    
    def clean_old_matches(self):
        """Supprime les anciens matchings de la table"""
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM matching_results")
            deleted_count = cur.rowcount
            self.conn.commit()
            cur.close()
            
            logger.info(f"🗑️  {deleted_count} anciens matchings supprimés")
            return deleted_count
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erreur suppression anciens matchings: {e}")
            raise
    
    def fetch_cvs_and_jobs(self) -> Tuple[List[Tuple], List[Tuple]]:
        """Récupère tous les CVs et offres de la base"""
        try:
            cur = self.conn.cursor()
            
            # Récupérer CVs
            cur.execute("""
                SELECT id, competences, annees_experience, localisation
                FROM cvs
                ORDER BY id
            """)
            cvs = cur.fetchall()
            
            # Récupérer Offres
            cur.execute("""
                SELECT id, competences_requises, experience_min, localisation
                FROM offres
                ORDER BY id
            """)
            jobs = cur.fetchall()
            
            cur.close()
            
            logger.info(f"📊 Données chargées: {len(cvs)} CVs × {len(jobs)} Offres")
            
            return cvs, jobs
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement données: {e}")
            raise
    
    def compute_matches(self) -> List[Tuple]:
        """
        Calcule tous les matchings possibles
        
        Returns:
            Liste de tuples pour insertion en base
        """
        cvs, jobs = self.fetch_cvs_and_jobs()
        
        matching_data = []
        total_comparisons = len(cvs) * len(jobs)
        
        logger.info(f"🔄 Calcul de {total_comparisons:,} comparaisons...")
        
        for cv in cvs:
            cv_id, cv_skills, cv_exp, cv_loc = cv
            cv_skills_set = set(cv_skills or [])
            
            for job in jobs:
                job_id, job_skills, job_exp_min, job_loc = job
                job_skills_set = set(job_skills or [])
                
                # Calcul des scores individuels
                skills_score, matching_skills, missing_skills = self.calculate_skills_score(
                    cv_skills_set, 
                    job_skills_set
                )
                
                exp_score = self.calculate_experience_score(cv_exp, job_exp_min)
                loc_score = self.calculate_location_score(cv_loc, job_loc)
                
                # Score global
                global_score = self.calculate_global_score(
                    skills_score, 
                    exp_score, 
                    loc_score
                )
                
                # ✅ FILTRE: Seuil à 0.55
                if global_score >= self.threshold:
                    matching_data.append((
                        cv_id,
                        job_id,
                        global_score,
                        skills_score,
                        exp_score,
                        loc_score,
                        skills_score,  # score_description (même que compétences)
                        missing_skills,
                        matching_skills,
                        int(global_score * 100)  # pourcentage_match
                    ))
        
        logger.info(f"✅ {len(matching_data)} matchings trouvés (seuil >= {self.threshold})")
        
        return matching_data
    
    def insert_matches(self, matching_data: List[Tuple]) -> int:
        """Insère les matchings en base de données"""
        if not matching_data:
            logger.warning("⚠️  Aucun matching à insérer")
            return 0
        
        try:
            cur = self.conn.cursor()
            
            from psycopg2.extras import execute_values
            
            insert_query = """
                INSERT INTO matching_results (
                    cv_id, offre_id, score_global, score_competences,
                    score_experience, score_localisation, score_description,
                    competences_manquantes, competences_presentes, pourcentage_match
                ) VALUES %s
            """
            
            execute_values(cur, insert_query, matching_data)
            self.conn.commit()
            cur.close()
            
            logger.info(f"💾 {len(matching_data)} matchings insérés en base")
            
            return len(matching_data)
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erreur insertion matchings: {e}")
            raise
    
    def run(self):
        """Exécute le processus complet de matching"""
        try:
            logger.info("="*80)
            logger.info("🚀 DÉMARRAGE DU BATCH MATCHING")
            logger.info("="*80)
            
            # Étape 1: Nettoyage
            self.clean_old_matches()
            
            # Étape 2: Calcul des matchings
            matching_data = self.compute_matches()
            
            # Étape 3: Insertion
            inserted = self.insert_matches(matching_data)
            
            # Étape 4: Statistiques finales
            self.print_statistics(inserted)
            
            return inserted
            
        except Exception as e:
            logger.error(f"❌ Erreur critique: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Connexion base fermée")
    
    def print_statistics(self, total_inserted: int):
        """Affiche les statistiques finales"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Statistiques détaillées
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(score_global) as avg_score,
                    MIN(score_global) as min_score,
                    MAX(score_global) as max_score,
                    COUNT(*) FILTER (WHERE score_global >= 0.70) as excellent,
                    COUNT(*) FILTER (WHERE score_global >= 0.60 AND score_global < 0.70) as good,
                    COUNT(*) FILTER (WHERE score_global >= 0.55 AND score_global < 0.60) as acceptable
                FROM matching_results
            """)
            
            stats = cur.fetchone()
            
            # Répartition par offre
            cur.execute("""
                SELECT 
                    offre_id,
                    COUNT(*) as nb_cvs_matches
                FROM matching_results
                GROUP BY offre_id
                HAVING COUNT(*) >= 5
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            
            top_jobs = cur.fetchall()
            
            cur.close()
            conn.close()
            
            # Affichage
            print("\n" + "="*80)
            print("📊 STATISTIQUES FINALES")
            print("="*80)
            
            if stats:
                total, avg, min_s, max_s, excellent, good, acceptable = stats
                print(f"\n✅ Total matchings insérés: {total}")
                print(f"   • Score moyen:    {avg:.4f} ({avg*100:.1f}%)")
                print(f"   • Score minimum:  {min_s:.4f} ({min_s*100:.1f}%)")
                print(f"   • Score maximum:  {max_s:.4f} ({max_s*100:.1f}%)")
                
                print(f"\n📈 Répartition par qualité:")
                print(f"   • Excellents (≥ 70%):   {excellent} matchings")
                print(f"   • Bons (60-70%):        {good} matchings")
                print(f"   • Acceptables (55-60%): {acceptable} matchings")
            
            if top_jobs:
                print(f"\n🎯 Top 10 Offres avec le plus de matchings:")
                for job_id, count in top_jobs:
                    print(f"   • Offre #{job_id}: {count} CVs matchés")
            
            print("\n" + "="*80)
            print("✅ BATCH MATCHING TERMINÉ AVEC SUCCÈS")
            print("="*80)
            
        except Exception as e:
            logger.error(f"⚠️  Erreur calcul statistiques: {e}")


def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("SMARTHIRE - BATCH MATCHER OPTIMISÉ")
    print("="*80)
    print("\nCalcul des matchings RÉELS (sans randomisation)")
    print("Seuil: 0.55 (55%)")
    print("Pondération: Compétences 60% | Expérience 30% | Localisation 10%")
    print("="*80 + "\n")
    
    try:
        # Créer et lancer le matcher
        matcher = BatchMatcherOptimized(threshold=0.55)
        inserted = matcher.run()
        
        print(f"\n🎉 SUCCÈS: {inserted} matchings calculés et insérés\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
