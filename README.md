# SmartHire

## Moteur Intelligent de Correspondance Candidats–Emplois

**Mini-projet SRI & Big Data – Année universitaire 2025–2026**

SmartHire est un moteur de recherche vertical intelligent dédié au recrutement dans le domaine informatique. Il permet un **matching bidirectionnel** entre les CV des candidats et les offres d’emploi IT, en combinant **recherche booléenne**, **recherche vectorielle** et **classement probabiliste BM25** pour offrir des résultats précis, pertinents et rapides.

---

## 🎯 Objectif du projet

L’objectif principal de SmartHire est d’optimiser le processus de recrutement technique en :

* automatisant le matching candidats ↔ offres,
* comprenant le langage spécifique de l’IT (technologies, stacks, alias),
* garantissant une recherche performante même sur de grands volumes de données,
* offrant une interface claire pour candidats et recruteurs.

Le projet s’inscrit dans le cadre des **Systèmes de Recherche d’Information (SRI)** appliqués au domaine **HR Tech**.

---

## ⚙️ Fonctionnalités essentielles

* 📄 **Indexation automatique des CV (PDF) et des offres (JSON)**
* 🧠 **Pipeline NLP bilingue (FR / EN)** : nettoyage, tokenisation, lemmatisation, normalisation des compétences
* 🔎 **Recherche avancée** :

  * moteur booléen (AND, OR, NOT),
  * moteur vectoriel basé sur BM25,
  * moteur hybride combinant filtrage et ranking
* 🧩 **Filtres métier** : compétences, stack, niveau d’expérience, localisation, type de contrat, mode de travail
* 🔄 **Matching bidirectionnel intelligent** (candidat → offres / recruteur → profils)
* 📊 **Classement par pertinence** avec fusion pondérée des scores
* 🌐 **API REST** documentée (Swagger / OpenAPI)
* 💻 **Interface web React** avec espaces Candidat et Recruteur

---

## 🎬 Démonstration de l’application

🎥 Vidéo de démonstration (1–2 min) :  
[Voir la démo SmartHire](https://youtu.be/pSaQZS3LN4A?si=Voj-4NbUNJ0f13zR)

---

## 🧠 Moteur de recherche (vue d’ensemble)

SmartHire repose sur une architecture modulaire orchestrée par un **Search Orchestrator**, chargé de :

* analyser la requête utilisateur,
* appliquer les filtres,
* choisir dynamiquement le moteur de recherche adapté.

### Moteurs utilisés

* **Recherche booléenne** : filtrage strict et précis (Whoosh)
* **Recherche vectorielle (BM25)** : gestion des requêtes textuelles libres
* **Recherche hybride** :

  1. filtrage initial booléen,
  2. classement par score BM25

Les scores finaux sont fusionnés par une **moyenne pondérée** après normalisation.

---

## 🗂️ Indexation & Données

### Types de documents

* **CV** : PDF (développeurs, ingénieurs, data, DevOps)
* **Offres d’emploi IT** : JSON

### Champs indexés (exemples)

* compétences techniques (boostées),
* titre du poste,
* description,
* localisation,
* années et niveau d’expérience,
* stack technologique.

---

## 🛠️ Technologies utilisées

### Backend

* **Python**
* **Flask** : API REST
* **NLTK** : traitement du langage naturel
* **PyPDF2** : extraction du texte des CV

### Recherche & Données

* **Whoosh** : index inversé, recherche booléenne et BM25F
* **PostgreSQL** : base relationnelle (profils, CV, offres, audit)

### Frontend

* **React** + **Vite**
* **Tailwind CSS** : design responsive

### Outils & autres

* Git & GitHub
* Flask-Bcrypt (sécurité)
* python-dotenv
* JSON & dictionnaires métiers
* Système de logs

---

## 🧑‍💻 Membres du groupe

Projet réalisé par un groupe de **4 membres** :

- [Ghita AIT EL MAMOUNE](https://github.com/ghitaaitm)
- [AABIR BENHAMAMOUCHE](https://github.com/Aabirben)
- [BAHAMD IMANE](https://github.com/imanebahamd)
- [EZZAHRA FADYL](https://github.com/EzzahraF)

---

## 👩‍🏫 Encadrement

Projet encadré par : **Professeur BOUZID SARA**

---

## ✅ Conclusion

SmartHire propose une solution complète et intelligente pour la recherche et le matching dans le recrutement IT. Grâce à une **architecture hybride**, un **pipeline NLP spécialisé** et des **technologies open-source robustes**, l’application offre une recherche précise, rapide et adaptée aux besoins réels des recruteurs et candidats techniques.
