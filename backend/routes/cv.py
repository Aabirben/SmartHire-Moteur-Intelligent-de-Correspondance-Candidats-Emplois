from flask import Blueprint, request, jsonify
from supabase import create_client
from config import Config
import pdfplumber  # For PDF extraction
import spacy  # For NLP

cv_bp = Blueprint('cv', __name__)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
nlp = spacy.load("fr_core_news_md")  # French model as per your project

@cv_bp.route('/upload', methods=['POST'])
def upload_cv():
    file = request.files['file']
    user_id = request.form['user_id']  # From auth token in real app

    try:
        # Upload to Supabase storage
        file_path = f"{user_id}/{file.filename}"
        supabase.storage.from_("cvs").upload(file_path, file.read())

        # Extract text from PDF
        with pdfplumber.open(file) as pdf:
            extracted_text = "\n".join(page.extract_text() for page in pdf.pages)

        # Basic NLP for skills (placeholder)
        doc = nlp(extracted_text)
        skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]  # Custom entity recognition needed

        # Insert to DB
        response = supabase.table("cvs").insert({
            "user_id": user_id,
            "filename": file.filename,
            "file_path": file_path,
            "extracted_text": extracted_text,
            "skills": skills,
            "experience_years": 5  # Placeholder; extract from NLP
        }).execute()

        # TODO: Implement full indexation here (e.g., Whoosh indexation pipeline)
        # Example: indexer.index_cv(response.data[0])

        return jsonify({"message": "CV uploaded and processed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400