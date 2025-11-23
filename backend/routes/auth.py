from flask import Blueprint, request, jsonify
from supabase import create_client
from config import Config

auth_bp = Blueprint('auth', __name__)
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')

    try:
        response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {
                    'full_name': full_name,
                    'role': role
                }
            }
        })
        return jsonify({"message": "User created", "user": response.user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        return jsonify({"message": "Logged in", "session": response.session}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        supabase.auth.sign_out()
        return jsonify({"message": "Logged out"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400