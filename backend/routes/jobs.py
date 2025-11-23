from flask import Blueprint, request, jsonify
from supabase import create_client
from config import Config

jobs_bp = Blueprint('jobs', __name__)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

@jobs_bp.route('/post', methods=['POST'])
def post_job():
    data = request.json
    posted_by = data['posted_by']  # From auth

    try:
        response = supabase.table("jobs").insert({
            "title": data['title'],
            "company": data['company'],
            "description": data['description'],
            "location": data.get('location'),
            "salary_min": data.get('salary_min'),
            "salary_max": data.get('salary_max'),
            "remote": data.get('remote', False),
            "required_skills": data.get('required_skills', []),
            "posted_by": posted_by
        }).execute()

        # TODO: Implement job indexation here (e.g., Whoosh index for search)
        # Example: indexer.index_job(response.data[0])

        return jsonify({"message": "Job posted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@jobs_bp.route('/search', methods=['GET'])
def search_jobs():
    query = request.args.get('query', '')

    try:
        # TODO: Implement full search with RI models (e.g., BM25, vector search)
        # Placeholder: basic Supabase search
        response = supabase.table("jobs").select("*").ilike("title", f"%{query}%").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400