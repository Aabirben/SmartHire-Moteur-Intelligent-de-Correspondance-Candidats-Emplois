"""
============================================================================
SMARTHIRE - Job Offer PDF Generator
Génération automatique de PDF pour les offres d'emploi
============================================================================
"""

import os
import re
import json
import unicodedata
import subprocess
from pathlib import Path

from backend.config.settings import JOB_FOLDER


# =======================================================================
# 🔧 UTILITAIRES : NORMALISATION DOMAINES / EMAILS
# =======================================================================

def slugify_for_email(s: str) -> str:
    """Nettoie un nom pour être utilisé dans une adresse email."""
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-z0-9._-]', '', s)
    return s or "company"


def sanitize_domain_for_filename(s: str) -> str:
    """Empêche les caractères illégaux dans les filenames."""
    s = re.sub(r'[^A-Za-z0-9_-]', '_', s)
    return s[:50]


# =======================================================================
# 📝 CLASSE GÉNÉRATRICE DE PDF
# =======================================================================

class JobOfferPDFGenerator:

    def __init__(self, base_output_dir=None):
        """
        base_output_dir = dossier principal où seront stockés les PDF
        Par défaut : JOB_FOLDER défini dans settings.py
        """
        self.output_dir = Path(base_output_dir or JOB_FOLDER) / "offers_pdfs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    def escape_latex(self, text):
        """
        Échappe les caractères spéciaux LaTeX (hors URL).
        """
        if not text:
            return ""
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    # -------------------------------------------------------------------
    def generate_latex_document(self, job_offer):
        """
        Construit un document LaTeX complet.
        """

        title = self.escape_latex(job_offer.get("title", ""))
        company = self.escape_latex(job_offer.get("company", {}).get("name", ""))
        location = self.escape_latex(job_offer.get("location", ""))
        job_id = self.escape_latex(job_offer.get("job_id", ""))

        salary_min = job_offer.get("salary_min", 0)
        salary_max = job_offer.get("salary_max", 0)

        requirements = job_offer.get("requirements", [])
        responsibilities = job_offer.get("responsibilities", [])

        # --- Email Safe ---
        raw_email = job_offer.get("contact_email", "")
        escaped_email = self.escape_latex(raw_email)

        latex = r"""
\documentclass[12pt]{article}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{setspace}
\usepackage{xcolor}
\usepackage{lipsum}

\geometry{a4paper, margin=1in}

\begin{document}

\begin{center}
    {\LARGE \textbf{""" + title + r"""}} \\[1em]
    {\large """ + company + r""" - """ + location + r"""}
\end{center}

\vspace{1em}

\section*{Job Summary}
\begin{spacing}{1.2}
""" + self.escape_latex(job_offer.get("description", "")) + r"""
\end{spacing}

\section*{Responsibilities}
\begin{itemize}
"""

        for resp in responsibilities:
            latex += r"\item " + self.escape_latex(resp) + "\n"

        latex += r"""
\end{itemize}

\section*{Requirements}
\begin{itemize}
"""

        for req in requirements:
            latex += r"\item " + self.escape_latex(req) + "\n"

        latex += r"""
\end{itemize}

\section*{Salary Range}
""" + f"{salary_min} MAD - {salary_max} MAD" + r"""

\section*{How to Apply}
To apply for this position, please send your resume and cover letter to:

\vspace{0.5em}
\textbf{Email:} \href{mailto:""" + raw_email + r"""}{\texttt{""" + escaped_email + r"""}} 

\vspace{0.5em}
\textbf{Subject:} Application for """ + title + " - " + job_id + r"""

\end{document}
"""

        return latex

    # -------------------------------------------------------------------
    def compile_pdf(self, tex_file: str, output_dir: str):
        """
        Compile un fichier LaTeX en PDF via pdflatex (2 passes).
        """

        try:
            cmd = ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file]

            for _ in range(2):  # double pass
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60
                )

            base = os.path.splitext(os.path.basename(tex_file))[0]

            for ext in ['.aux', '.log', '.out', '.toc']:
                f = os.path.join(output_dir, base + ext)
                if os.path.exists(f):
                    os.remove(f)

            return os.path.exists(os.path.join(output_dir, base + ".pdf"))

        except Exception as e:
            print(f"⚠️ Erreur compilation LaTeX : {e}")
            return False

    # -------------------------------------------------------------------
    def generate_pdfs(self, jobs: list, auto_email=True):
        """
        Génère les PDF d'une liste d'offres.
        """

        tex_dir = self.output_dir / "tex"
        pdf_dir = self.output_dir / "pdf"

        tex_dir.mkdir(parents=True, exist_ok=True)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        for i, job in enumerate(jobs, 1):
            company = job.get("company", {}).get("name", "Unknown Company")

            safe_company = slugify_for_email(company)
            job["contact_email"] = f"careers@{safe_company}.ma"

            safe_domain = sanitize_domain_for_filename(job.get("domain", "job"))
            clean_title = sanitize_domain_for_filename(job.get("title", "offer"))

            tex_file = tex_dir / f"Job_{i:02d}_{safe_domain}_{clean_title}.tex"

            latex = self.generate_latex_document(job)
            tex_file.write_text(latex, encoding="utf-8")

            print(f"📄 Génération PDF {i}/{len(jobs)} : {tex_file.name}")

            self.compile_pdf(str(tex_file), str(pdf_dir))

        print("\n✅ Tous les PDF ont été générés avec succès !")
