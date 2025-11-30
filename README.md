# SmartHire-Moteur-Intelligent-de-Correspondance-Candidats-Emplois
Projet académique – Module SRI (Pr. S. Bouzid) – Génie Informatique 5ème année – ENSA Marrakech – 2025/2026
# SmartHire – Système d'Indexation et de Matching CV/Offres

SmartHire est un système Python permettant d'indexer les CV et les offres d'emploi pour faciliter le **matching automatique**. Il utilise **Whoosh** pour l'indexation et **PyPDF2** pour l'extraction de texte depuis les CV au format PDF.

---

## Fonctionnalités

### 1. Indexation des CV
- Extraction et nettoyage du texte depuis les PDF.
- Détection automatique de :
  - Nom du candidat
  - Titre du profil
  - Localisation (avec villes marocaines supportées)
  - Nombre d'années d'expérience
  - Compétences techniques (avec alias)
  - Projets principaux
  - Résumé professionnel
  - Description détaillée des expériences
- Création d'un index Whoosh enrichi pour le matching.
- Statistiques et logs détaillés pour chaque CV traité.

### 2. Indexation des offres d'emploi
- Indexation des informations clés :
  - Titre du poste (boosté pour importance)
  - Description complète (responsabilités + description)
  - Compétences requises (required + preferred)
  - Localisation
  - Niveau souhaité (Junior, Mid-Level, Senior, Expert)
  - Domaine, entreprise, type de contrat, mode de travail
- Calcul automatique des années d'expérience minimales et maximales selon le niveau.
- Affichage détaillé de chaque offre indexée pour suivi.

### 3. Recherche / Tests
- Possibilité de tester la recherche sur l’index des offres.
- Recherche multi-champs (titre, description, compétences, localisation) avec BM25F.
- Exemple :
```python
search_jobs("python backend developer")
search_jobs("react frontend casablanca")
search_jobs("devops kubernetes senior")
