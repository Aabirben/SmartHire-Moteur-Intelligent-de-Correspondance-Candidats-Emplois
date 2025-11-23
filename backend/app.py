from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.cv import cv_bp
from routes.jobs import jobs_bp
from routes.applications import applications_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, origins=app.config["CORS_ORIGINS"])

# Register blueprints (routes)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(cv_bp, url_prefix='/api/cv')
app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
app.register_blueprint(applications_bp, url_prefix='/api/applications')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True)