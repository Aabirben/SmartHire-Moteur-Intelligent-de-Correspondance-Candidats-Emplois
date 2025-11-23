from flask import Blueprint, request, jsonify
from supabase import create_client
from config import Config

applications_bp = Blueprint('applications', __name__)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

@applications_bp.route('/apply', methods=['POST'])
def apply():
    data = request.json
    try:
        response = supabase.table("applications").insert({
            "job_id": data['job_id'],
            "candidate_id": data['candidate_id'],
            "cv_id": data['cv_id'],
            "match_score": data.get('match_score', 0),
            "status": "pending"
        }).execute()

        # TODO: Implement matching/scoring with RI models here
        # Example: scorer.calculate_match(response.data[0])

        return jsonify({"message": "Application submitted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@applications_bp.route('/messages/send', methods=['POST'])
def send_message():
    data = request.json
    try:
        response = supabase.table("messages").insert({
            "application_id": data['application_id'],
            "sender_id": data['sender_id'],
            "content": data['content']
        }).execute()
        return jsonify({"message": "Message sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400