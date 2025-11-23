🚀 SmartHire – Interface Complète (Branche ui)

l’interface complète et fonctionnelle de SmartHire .

✨ Fonctionnalités incluses
🔐 Authentification

Connexion / inscription (candidat & recruteur)

Validation stricte et sécurisée

🧑‍💼 Dashboard Candidat

Upload de CV (PDF uniquement)

Matching automatique avec explication

Radar Chart des compétences

Score explicable (transparence algorithmique)

Analyse de skill gaps + recommandations

🧑‍💻 Dashboard Recruteur

Création d'offres

Liste des candidats postulants

Heatmap explicative du matching

Détection automatique du niveau (Junior / Mid / Senior)

Messagerie intégrée

💬 Messagerie

Interface temps réel (mockée mais entièrement fonctionnelle)

🔍 Recherche avancée

Filtres booléens : AND / OR / NOT

⚠️ Toute l’interface est 100 % mockée → fonctionne SANS backend réel.

⚡ Démarrer l’interface (≤ 5 minutes)
# 1. Cloner le projet et aller sur la branche ui
git clone https://github.com/Aabirben/SmartHire-Moteur-Intelligent-de-Correspondance-Candidats-Emplois.git
cd SmartHire-Moteur-Intelligent-de-Correspondance-Candidats-Emplois
git checkout ui

# 2. Aller dans le frontend
cd frontend

# 3. Installer les dépendances
npm install
# ou : yarn install / pnpm install

# 4. Lancer le projet
npm run dev


➡️ Ouvre http://localhost:5173
 → le site fonctionne immédiatement !

🔌 Connecter votre backend (FastAPI / Flask) plus tard

Le frontend est déjà prêt pour un backend réel.
Voici les endpoints attendus :

🔑 Auth
POST /api/auth/login
POST /api/auth/signup

📄 CV & Matching
POST /api/cv/upload
→ retourne : compétences extraites + recommandations de jobs

💼 Offres d’emploi
GET  /api/jobs
POST /api/jobs
GET  /api/jobs/{id}/applicants

🔍 Recherche
GET /api/search/jobs
GET /api/search/candidates

💬 Messagerie
GET /api/messages
POST /api/messages

🔄 Passer du mock au backend réel

Supprimer ou commenter les données mock dans
src/utils/mockData.ts

Créer src/lib/api.ts avec axios / fetch :

const api = axios.create({
  baseURL: "http://localhost:8000"
});


Remplacer les appels mock par les appels API réels
(déjà centralisés → 10 minutes de travail maximum)

🧩 Composants clés du projet
Composant	Chemin	Rôle
SkillRadarChart.tsx	src/components/charts/	Comparaison visuelle : compétences candidat ↔ job
ExplainableScoreBreakdown.tsx	src/components/charts/	Score global + poids de chaque critère
SkillGapList.tsx	src/components/matching/	Compétences manquantes + suggestions
AdvancedSearchFilters.tsx	src/components/search/	Recherche booléenne (AND / OR / NOT)
LevelDetectionCard.tsx	src/components/matching/	Détection du niveau (Junior / Mid / Senior)
ChatInterface.tsx	src/components/messaging/	Messagerie temps réel mockée
