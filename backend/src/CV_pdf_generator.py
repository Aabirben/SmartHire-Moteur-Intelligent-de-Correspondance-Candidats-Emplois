"""
============================================================================
Générateur de CV - Version Locale
Génère des CV au format LaTeX et PDF
============================================================================
"""

import random
import os
import subprocess
import glob
import logging
from datetime import datetime
import re
from pathlib import Path
import sys

# Ajouter le chemin du projet pour importer settings
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.config.settings import CV_FOLDER, create_directories
    USE_SETTINGS = True
except ImportError:
    print("⚠️  settings.py non trouvé, utilisation du chemin par défaut")
    USE_SETTINGS = False
    CV_FOLDER = PROJECT_ROOT / "data" / "cvs"

# Configuration du logging
def setup_logging(output_dir):
    log_file = f"{output_dir}/generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_file

# Données pour générer des CV variés
prenoms = ["Ahmed", "Fatima", "Youssef", "Salma", "Mehdi", "Amina", "Omar", "Khadija",
           "Karim", "Naima", "Hassan", "Zineb", "Amine", "Laila", "Rachid", "Sofia",
           "Ali", "Meryem", "Hamza", "Sanaa", "Bilal", "Nadia", "Othmane", "Hind",
           "Ayoub", "Imane", "Yassin", "Rim", "Saad", "Meriem"]

noms = ["Alami", "Benali", "Chakir", "Dahane", "El Fassi", "Fathi", "Gharbi", "Hamidi",
        "Idrissi", "Jilali", "Khalil", "Lazrak", "Mahmoudi", "Naciri", "Ouazzani",
        "Qassemi", "Rafik", "Sabri", "Tahiri", "Usman", "Wahbi", "Yazidi", "Ziani",
        "Benjelloun", "El Amrani", "Filali", "Hamdaoui", "Karimi", "Mansouri", "Tazi"]

universites = [
    ("École Mohammadia d'Ingénieurs (EMI)", "Rabat"),
    ("INSEA", "Rabat"),
    ("ENSIAS", "Rabat"),
    ("Université Mohammed V", "Rabat"),
    ("Université Hassan II", "Casablanca"),
    ("ENSAM Casablanca", "Casablanca"),
    ("FST Mohammedia", "Mohammedia"),
    ("Université Cadi Ayyad", "Marrakech"),
    ("ENSA Marrakech", "Marrakech"),
    ("Université Ibn Tofail", "Kenitra")
]

diplomes = ["B.Tech in Computer Science", "Master in Software Engineering",
            "B.Sc in Information Technology", "Master in Data Science",
            "B.Eng in Computer Engineering", "Master in AI and Machine Learning"]

entreprises = [
    ("Capgemini Maroc", "Casablanca"),
    ("CGI Maroc", "Rabat"),
    ("Accenture", "Casablanca"),
    ("Sqli", "Casablanca"),
    ("Majorel", "Rabat"),
    ("Orange Digital Center", "Casablanca"),
    ("OCP Group", "Casablanca"),
    ("BMCE Bank", "Casablanca"),
    ("Maroc Telecom", "Rabat"),
    ("Webhelp", "Casablanca")
]

postes = [
    "Software Development Engineer",
    "Full Stack Developer",
    "Backend Developer",
    "Frontend Developer",
    "DevOps Engineer",
    "Data Engineer",
    "Machine Learning Engineer",
    "Mobile Developer",
    "QA Engineer",
    "Cloud Engineer"
]

competences = {
    "backend": ["Node.js", "Python", "Java", "Go", "Ruby", "PHP", "Django", "Spring Boot", "Express.js", "FastAPI"],
    "frontend": ["React", "Angular", "Vue.js", "JavaScript", "TypeScript", "HTML", "CSS", "jQuery", "Bootstrap", "Tailwind"],
    "mobile": ["Android", "iOS", "React Native", "Flutter", "Kotlin", "Swift", "Java"],
    "database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Oracle", "SQL Server", "Cassandra", "DynamoDB"],
    "devops": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "AWS", "Azure", "GCP", "Terraform", "Ansible"],
    "data": ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Spark", "Hadoop", "Kafka"],
    "tools": ["Git", "JIRA", "Agile", "Scrum", "REST API", "Microservices", "GraphQL", "RabbitMQ"]
}

projets = [
    ("E-commerce Platform", "Developed a full-stack e-commerce platform with payment integration, product management, and order tracking using React and Node.js with PostgreSQL database."),
    ("Real-time Chat Application", "Built a scalable real-time messaging application supporting group chats, file sharing, and video calls using WebSocket and Redis for message queuing."),
    ("Banking Mobile App", "Created a secure mobile banking application with biometric authentication, transaction history, and fund transfer capabilities for iOS and Android."),
    ("Data Analytics Dashboard", "Implemented an interactive dashboard for business intelligence with real-time data visualization, reporting features, and predictive analytics."),
    ("Hotel Booking System", "Developed an online hotel reservation system with search filters, availability calendar, payment processing, and booking management."),
    ("Inventory Management System", "Built a comprehensive inventory tracking system with barcode scanning, stock alerts, supplier management, and automated reporting."),
    ("Task Management Platform", "Created a collaborative task management tool with kanban boards, time tracking, team collaboration features, and productivity analytics."),
    ("Healthcare Portal", "Developed a patient management system with appointment scheduling, medical records, prescription management, and telemedicine features."),
    ("Learning Management System", "Built an online education platform with course management, video streaming, quiz system, and student progress tracking."),
    ("Social Media Analytics Tool", "Implemented a social media monitoring tool with sentiment analysis, engagement metrics, and automated reporting using NLP.")
]

def sanitize_for_latex(text):
    """Échappe les caractères spéciaux LaTeX"""
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
    }
    for char, replacement in special_chars.items():
        text = text.replace(char, replacement)
    return text

def valider_email(email):
    """Valide le format de l'email"""
    pattern = r'^[a-z0-9.]+@[a-z0-9]+\.[a-z]{2,}$'
    return re.match(pattern, email) is not None

def generer_email(prenom, nom):
    """Génère un email valide"""
    prenom_clean = prenom.replace(" ", "").replace("_", "").lower()
    nom_clean = nom.replace(" ", "").replace("_", "").lower()
    email = f"{prenom_clean}.{nom_clean}@gmail.com"

    if not valider_email(email):
        email = f"user{random.randint(1000, 9999)}@gmail.com"
        logging.warning(f"Email invalide généré, utilisation de: {email}")

    return email

def generer_telephone():
    """Génère un numéro de téléphone marocain valide"""
    prefixes = ["06", "07"]
    return f"+212 {random.choice(prefixes)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"

def generer_resume(poste, years, skills):
    """Génère un résumé professionnel basé sur le poste et l'expérience"""
    
    # Limiter les compétences à 3 maximum pour le résumé
    main_skills = ", ".join(skills[:3]) if len(skills) >= 3 else ", ".join(skills)
    
    # Templates de résumés selon le poste
    templates = {
        "Software Development Engineer": (
            f"{years}+ years experienced Software Development Engineer skilled in building "
            f"scalable applications and microservices. Proficient in {main_skills} with a "
            f"strong focus on performance optimization and clean code practices."
        ),
        
        "Full Stack Developer": (
            f"Full Stack Developer with {years}+ years of experience creating responsive web "
            f"applications. Expertise in {main_skills}, delivering end-to-end solutions from "
            f"design to deployment."
        ),
        
        "Backend Developer": (
            f"Backend Developer with {years}+ years specializing in server-side technologies "
            f"and database design. Strong expertise in {main_skills}, focused on building "
            f"robust and scalable backend systems."
        ),
        
        "Frontend Developer": (
            f"Frontend Developer with {years}+ years of experience building modern, responsive "
            f"user interfaces. Proficient in {main_skills}, passionate about creating seamless "
            f"user experiences."
        ),
        
        "DevOps Engineer": (
            f"DevOps Engineer with {years}+ years of experience in automation and cloud "
            f"infrastructure. Expert in {main_skills}, focused on CI/CD pipelines and "
            f"infrastructure optimization."
        ),
        
        "Data Engineer": (
            f"Data Engineer with {years}+ years of experience building data pipelines and "
            f"warehouses. Skilled in {main_skills}, specialized in ETL processes and data "
            f"architecture."
        ),
        
        "Machine Learning Engineer": (
            f"Machine Learning Engineer with {years}+ years of experience developing ML models "
            f"and AI solutions. Proficient in {main_skills}, focused on model deployment and "
            f"production systems."
        ),
        
        "Mobile Developer": (
            f"Mobile Developer with {years}+ years of experience creating native and "
            f"cross-platform mobile applications. Expert in {main_skills}, passionate about "
            f"mobile UX and performance."
        ),
        
        "QA Engineer": (
            f"QA Engineer with {years}+ years of experience in test automation and quality "
            f"assurance. Skilled in {main_skills}, dedicated to ensuring software quality "
            f"and reliability."
        ),
        
        "Cloud Engineer": (
            f"Cloud Engineer with {years}+ years of experience in cloud architecture and "
            f"infrastructure. Proficient in {main_skills}, specialized in scalable cloud "
            f"solutions."
        )
    }
    
    # Retourner le template approprié ou un template par défaut
    return templates.get(poste, 
        f"Software Engineer with {years}+ years of experience in software development. "
        f"Proficient in {main_skills}, committed to delivering high-quality solutions."
    )

def generer_taches(poste):
    """Génère des tâches pertinentes selon le poste"""
    taches_par_poste = {
        "Software Development Engineer": [
            "Designed and implemented scalable microservices architecture handling 10K+ requests per second",
            "Developed RESTful APIs for mobile and web applications with comprehensive documentation",
            "Optimized database queries reducing response time by 40\\% through indexing and query refactoring",
            "Implemented CI/CD pipelines using Jenkins and Docker for automated testing and deployment"
        ],
        "Full Stack Developer": [
            "Built responsive web applications using React and Node.js with Redux state management",
            "Developed user authentication system with JWT and OAuth2 integration",
            "Implemented real-time features using WebSocket for live notifications and updates",
            "Created admin dashboard with analytics, reporting, and data visualization capabilities"
        ],
        "Backend Developer": [
            "Architected and developed backend services using Python Django and PostgreSQL",
            "Implemented caching strategies with Redis reducing database load by 60\\%",
            "Developed message queue system using RabbitMQ for asynchronous task processing",
            "Built RESTful APIs following best practices with proper error handling and validation"
        ],
        "Frontend Developer": [
            "Developed modern UI components using React with TypeScript and Material-UI",
            "Implemented responsive designs ensuring cross-browser compatibility and mobile optimization",
            "Integrated third-party APIs and services for enhanced functionality",
            "Optimized application performance achieving 95+ Lighthouse scores"
        ],
        "DevOps Engineer": [
            "Managed AWS infrastructure including EC2, S3, RDS, and Lambda services",
            "Implemented Kubernetes clusters for container orchestration and auto-scaling",
            "Automated deployment processes reducing deployment time from hours to minutes",
            "Set up monitoring and alerting systems using Prometheus and Grafana"
        ],
        "Data Engineer": [
            "Built ETL pipelines processing millions of records daily using Apache Spark",
            "Designed and implemented data warehouses using PostgreSQL and Redshift",
            "Developed data quality frameworks ensuring data accuracy and consistency",
            "Created data visualization dashboards for business intelligence using Power BI"
        ],
        "Machine Learning Engineer": [
            "Developed ML models for prediction and classification achieving 90\\%+ accuracy",
            "Implemented NLP solutions for text analysis and sentiment detection",
            "Built recommendation systems using collaborative filtering and deep learning",
            "Deployed ML models to production using Flask and Docker containers"
        ],
        "Mobile Developer": [
            "Developed native Android applications using Kotlin and Jetpack Compose",
            "Built cross-platform mobile apps using React Native for iOS and Android",
            "Implemented offline-first architecture with local database and sync mechanisms",
            "Integrated push notifications, analytics, and crash reporting services"
        ],
        "QA Engineer": [
            "Designed and executed comprehensive test plans for web and mobile applications",
            "Automated testing using Selenium, Cypress, and JUnit frameworks",
            "Performed API testing using Postman and developed automated test scripts",
            "Implemented continuous testing in CI/CD pipelines ensuring quality releases"
        ],
        "Cloud Engineer": [
            "Migrated on-premise infrastructure to AWS cloud reducing costs by 30\\%",
            "Implemented Infrastructure as Code using Terraform for cloud resource management",
            "Designed highly available and fault-tolerant cloud architectures",
            "Managed cloud security including IAM, VPC, and encryption configurations"
        ]
    }

    taches_disponibles = taches_par_poste.get(poste, [
        "Developed and maintained software applications following best practices",
        "Collaborated with cross-functional teams in agile environment",
        "Participated in code reviews and technical documentation",
        "Implemented new features based on business requirements"
    ])

    return random.sample(taches_disponibles, min(3, len(taches_disponibles)))

def generer_cv(numero):
    """Génère un CV complet avec toutes les informations"""
    try:
        prenom = random.choice(prenoms)
        nom = random.choice(noms)

        # Nettoyer pour les noms de fichiers
        prenom_file = prenom.replace(" ", "_")
        nom_file = nom.replace(" ", "_")

        email = generer_email(prenom, nom)
        telephone = generer_telephone()

        # Éducation
        universite, ville_univ = random.choice(universites)
        diplome = random.choice(diplomes)
        cgpa = round(random.uniform(7.5, 9.5), 2)
        annee_debut = random.randint(2014, 2018)
        annee_fin = annee_debut + random.choice([3, 4, 5])

        # Expériences (1 à 3 expériences)
        nb_experiences = random.randint(1, 3)
        experiences = []

        annee_exp = 2024
        for i in range(nb_experiences):
            entreprise, ville_ent = random.choice(entreprises)
            poste = random.choice(postes)
            mois_debut = random.choice(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
            annee_debut_exp = annee_exp - random.randint(1, 3)

            # 70% de chances d'avoir "Present" pour la première expérience
            if i == 0 and random.random() < 0.7:
                periode = f"{mois_debut} {annee_debut_exp} - Present"
            else:
                mois_fin = random.choice(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
                annee_fin_exp = annee_debut_exp + random.randint(1, 2)
                periode = f"{mois_debut} {annee_debut_exp} - {mois_fin} {annee_fin_exp}"

            annee_exp = annee_debut_exp
            taches = generer_taches(poste)

            experiences.append({
                "entreprise": entreprise,
                "ville": ville_ent,
                "poste": poste,
                "periode": periode,
                "taches": taches
            })

        # Projets
        projets_selectionnes = random.sample(projets, 2)

        # Compétences selon les expériences
        comp_proficient = []
        comp_comfortable = []

        for exp in experiences:
            if "Backend" in exp["poste"] or "Full Stack" in exp["poste"]:
                comp_proficient.extend(random.sample(competences["backend"], 2))
                comp_comfortable.extend(random.sample(competences["database"], 2))
            elif "Frontend" in exp["poste"]:
                comp_proficient.extend(random.sample(competences["frontend"], 3))
                comp_comfortable.extend(random.sample(competences["tools"], 2))
            elif "Mobile" in exp["poste"]:
                comp_proficient.extend(random.sample(competences["mobile"], 2))
                comp_comfortable.extend(random.sample(competences["frontend"], 2))
            elif "DevOps" in exp["poste"]:
                comp_proficient.extend(random.sample(competences["devops"], 3))
                comp_comfortable.extend(random.sample(competences["database"], 2))
            elif "Data" in exp["poste"] or "Machine Learning" in exp["poste"]:
                comp_proficient.extend(random.sample(competences["data"], 3))
                comp_comfortable.extend(random.sample(competences["tools"], 2))
            else:
                comp_proficient.extend(random.sample(competences["backend"], 2))
                comp_comfortable.extend(random.sample(competences["tools"], 2))

        # Enlever les doublons et limiter
        comp_proficient = list(set(comp_proficient))[:5]
        comp_comfortable = list(set(comp_comfortable))[:5]
        
        # Générer résumé professionnel
        years = max(1, min(annee_fin - annee_debut, 6))
        all_skills = comp_proficient + comp_comfortable
        professional_summary = generer_resume(experiences[0]["poste"], years, all_skills)

        # Générer le CV LaTeX
        cv_latex = generer_latex(prenom, nom, email, telephone, universite, ville_univ,
                                 diplome, cgpa, annee_debut, annee_fin, experiences,
                                 projets_selectionnes, comp_proficient, comp_comfortable, professional_summary)

        return cv_latex, f"{prenom_file}_{nom_file}"

    except Exception as e:
        logging.error(f"Erreur lors de la génération du CV {numero}: {e}")
        raise

def generer_latex(prenom, nom, email, telephone, universite, ville_univ, diplome,
                  cgpa, annee_debut, annee_fin, experiences, projets, comp_proficient, comp_comfortable, professional_summary):
    """Génère le code LaTeX du CV"""

    latex = r"""%-------------------------
% Resume in Latex
% Author : CV Generator
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[pdftex]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.375in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

%-------------------------
% Custom commands
\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-4pt}}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING-----------------
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{\href{https://www.linkedin.com/}{\Large """ + prenom + " " + nom + r"""}} & Email : \href{mailto:""" + email + r"""}{""" + email + r"""}\\
  \href{https://www.linkedin.com/}{{linkedin.com/in/""" + prenom.lower().replace(" ", "") + nom.lower().replace(" ", "") + r"""}} & Mobile : """ + telephone + r""" \\
\end{tabular*}

%-----------PROFESSIONAL SUMMARY-----------------
\section{Professional Summary}
""" + professional_summary + r"""

%-----------EDUCATION-----------------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {""" + universite + r"""}{""" + ville_univ + r"""}
      {""" + diplome + r""";  CGPA: """ + str(cgpa) + r"""}{July. """ + str(annee_debut) + r""" -- May. """ + str(annee_fin) + r"""}
  \resumeSubHeadingListEnd


%-----------EXPERIENCE-----------------
\section{Experience}
  \resumeSubHeadingListStart
"""

    for exp in experiences:
        latex += r"""
    \resumeSubheading
      {""" + exp["entreprise"] + r"""}{""" + exp["ville"] + r"""}
      {""" + exp["poste"] + r"""}{""" + exp["periode"] + r"""}
      \resumeItemListStart
"""
        for idx, tache in enumerate(exp["taches"]):
            latex += r"""        \resumeItem{Task """ + str(idx + 1) + r"""}
          {""" + tache + r"""}
"""

        latex += r"""      \resumeItemListEnd
"""

    latex += r"""
  \resumeSubHeadingListEnd

%-----------PROJECTS-----------------
\section{Projects}
  \resumeSubHeadingListStart
"""

    for projet_nom, projet_desc in projets:
        latex += r"""    \resumeSubItem{""" + projet_nom + r"""}
      {""" + projet_desc + r"""}
"""

    latex += r"""  \resumeSubHeadingListEnd

%--------PROGRAMMING SKILLS------------
\section{Skills}
 \resumeSubHeadingListStart
    \item{
     \textbf{Proficient}{: """ + ", ".join(comp_proficient) + r""" }
    }
    \item{
     \textbf{Comfortable}{: """ + ", ".join(comp_comfortable) + r"""}
    }
 \resumeSubHeadingListEnd

%-------------------------------------------
\end{document}"""

    return latex

def generer_tous_les_cv(nb_cv=50, output_dir=None):
    """Génère tous les CV et les sauvegarde"""
    if output_dir is None:
        # Utiliser CV_FOLDER depuis settings.py
        output_dir = CV_FOLDER
        if USE_SETTINGS:
            # Créer tous les dossiers définis dans settings
            create_directories()
    else:
        output_dir = Path(output_dir)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = setup_logging(output_dir)

        logging.info("="*60)
        logging.info(f"🚀 Génération de {nb_cv} CV en cours...")
        logging.info(f"📂 Stockage dans: {output_dir}")
        if USE_SETTINGS:
            logging.info(f"✅ Utilisation de settings.py (CV_FOLDER)")
        logging.info(f"📝 Log: {log_file}")
        logging.info("="*60)

        cv_generes = []

        for i in range(1, nb_cv + 1):
            try:
                cv_content, nom_fichier = generer_cv(i)
                filename = output_dir / f"CV_{i:02d}_{nom_fichier}.tex"

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(cv_content)

                cv_generes.append(str(filename))
                logging.info(f"✓ CV {i}/{nb_cv} généré: {nom_fichier}")

            except Exception as e:
                logging.error(f"✗ Échec CV {i}/{nb_cv}: {e}")

        logging.info("="*60)
        logging.info(f"✅ {len(cv_generes)}/{nb_cv} fichiers .tex générés avec succès!")
        logging.info(f"📁 Emplacement: {output_dir}")
        logging.info("="*60)

        return str(output_dir), cv_generes

    except Exception as e:
        logging.error(f"❌ Erreur critique: {e}")
        raise

def verifier_latex():
    """Vérifie si LaTeX est installé"""
    try:
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def compiler_cv(tex_file, output_dir, timeout=30):
    """Compile un fichier .tex en PDF"""
    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode',
             f'-output-directory={output_dir}', str(tex_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False
        )

        pdf_file = str(tex_file).replace('.tex', '.pdf')
        return os.path.exists(pdf_file)

    except subprocess.TimeoutExpired:
        logging.warning(f"Timeout lors de la compilation de {os.path.basename(tex_file)}")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de la compilation: {e}")
        return False

def compiler_tous_les_cv(output_dir):
    """Compile tous les fichiers .tex en PDF"""
    print("\n" + "="*60)
    print("📄 Compilation des CV en PDF...")
    print("="*60 + "\n")

    tex_files = sorted(glob.glob(f"{output_dir}/CV_*.tex"))

    if not tex_files:
        logging.error("Aucun fichier .tex trouvé!")
        return

    pdf_success = 0
    pdf_failed = 0

    for i, tex_file in enumerate(tex_files, 1):
        nom_fichier = os.path.basename(tex_file)
        print(f"[{i}/{len(tex_files)}] Compilation de {nom_fichier}...", end=" ")

        if compiler_cv(tex_file, output_dir):
            pdf_success += 1
            print("✓")
        else:
            pdf_failed += 1
            print("✗")

        # Nettoyer les fichiers auxiliaires
        for ext in ['.aux', '.log', '.out']:
            aux_file = tex_file.replace('.tex', ext)
            if os.path.exists(aux_file):
                try:
                    os.remove(aux_file)
                except Exception as e:
                    logging.warning(f"Impossible de supprimer {aux_file}: {e}")

    print("\n" + "="*60)
    print("✅ COMPILATION TERMINÉE!")
    print("="*60)
    logging.info(f"📁 Emplacement: {output_dir}")
    logging.info(f"📝 Fichiers .tex: {len(tex_files)}")
    logging.info(f"📄 Fichiers .pdf: {pdf_success}")
    if pdf_failed > 0:
        logging.warning(f"⚠️  Échecs: {pdf_failed}")
    print("="*60)

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    try:
        # Générer les CV
        output_dir, cv_files = generer_tous_les_cv(50)

        # Vérifier et compiler si LaTeX est disponible
        if verifier_latex():
            print("\n✅ LaTeX détecté, compilation en cours...")
            compiler_tous_les_cv(output_dir)
        else:
            print("\n⚠️  LaTeX non détecté sur le système")
            print("Pour compiler les CV en PDF, installez LaTeX :")
            print("  - Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra")
            print("  - macOS: brew install --cask mactex")
            print("  - Windows: https://miktex.org/download")
            print(f"\n📄 Les fichiers .tex ont été générés dans: {output_dir}")

    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        logging.exception("Erreur fatale")