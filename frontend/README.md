Markdown# SmartHire – Interface complète (branche ui)
 **l’interface complète et fonctionnelle** du projet SmartHire (version 2025) avec toute la transparence algorithmique demandée.

### Ce que vous avez déjà dans cette branche
- Authentification (candidat / recruteur) avec validation stricte  
- Dashboard candidat : upload CV (PDF uniquement), matching automatique, radar chart, score explicable, skill gaps  
- Dashboard recruteur : création d’offres, vue des candidats postulants avec heatmap, niveau auto-détecté, messagerie  
- Messagerie temps réel (mockée mais 100 % fonctionnelle)  
- Recherche avancée avec filtres booléens (AND / OR / NOT)
  
- Tout est 100 % mocké → fonctionne sans backend réel

### Comment lancer l’interface (5 minutes max)

```bash
# 1. Cloner et aller sur la branche ui
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
→ Ouvre http://localhost:5173 → tout fonctionne immédiatement !
Comment connecter VOTRE backend plus tard (quand vous serez prêtes)
Le frontend est déjà prêt à parler à un vrai backend FastAPI/Flask.
Endpoints attendus (utilisés dans src/utils/mockData.ts et les composants) :

POST /api/auth/login et /api/auth/signup
POST /api/cv/upload → renvoie compétences extraites + jobs recommandés
GET/POST /api/jobs → liste et création d’offres
GET /api/jobs/{id}/applicants
GET /api/search/jobs et /api/search/candidates
GET/POST /api/messages

Étapes pour passer du mock au vrai backend :

Supprimer ou commenter les données mock dans src/utils/mockData.ts
Créer un fichier src/lib/api.ts avec axios/fetch pointant vers votre backend (http://localhost:8000 ou autre)
Remplacer les appels mock par les vrais appels API

→ Le code est déjà très bien structuré, ça prendra 10 minutes max.
Les composants clés que vous allez adorer

ComposantEmplacementRôleSkillRadarChart.tsxsrc/components/charts/Comparaison visuelle compétences candidat ↔ jobExplainableScoreBreakdown.tsxsrc/components/charts/Score total + contribution détaillée de chaque critèreSkillGapList.tsxsrc/components/matching/Compétences manquantes + suggestions de formationAdvancedSearchFilters.tsxsrc/components/search/Recherche booléenne avancée (AND / OR / NOT)           LavalLevelDetectionCard.tsxsrc/components/matching/Niveau (Junior / Mid / Senior) détecté automatiquementChatInterface.tsxsrc/components/messaging/Messagerie complète candidat ↔ recruteur
