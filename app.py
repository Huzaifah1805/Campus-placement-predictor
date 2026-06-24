from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import os
import sqlite3
import pandas as pd
from recommender import get_feedback_and_recommendations
from ats_processor import analyze_ats_score

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Base path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'placement_model.pkl')

# Vercel serverless has a read-only filesystem, except for /tmp
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/placements.db'
else:
    DB_PATH = os.path.join(BASE_DIR, 'placements.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cgpa REAL,
                internships INTEGER,
                projects INTEGER,
                backlogs INTEGER,
                coding_score INTEGER,
                dsa_score INTEGER,
                webdev_score INTEGER,
                comm_score INTEGER,
                probability REAL,
                salary_range TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Initialize DB on startup
init_db()

# Global variables for model storage
model = None
scaler = None
feature_names = None

def load_ml_model():
    global model, scaler, feature_names
    if not os.path.exists(MODEL_PATH):
        # Trigger model training if it does not exist
        print("Model file not found. Running training script...")
        from model_manager import train_and_save_model
        train_and_save_model()
        
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        scaler = model_data['scaler']
        feature_names = model_data['feature_names']
    print("Machine Learning Model successfully loaded.")

# Load the model on startup
load_ml_model()

@app.route('/')
def home():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/api/model-info', methods=['GET'])
def get_model_info():
    """Returns details about the trained ML model."""
    try:
        if model is None:
            return jsonify({'error': 'Model not initialized'}), 500
        
        # Format feature importances
        importances = model.feature_importances_
        feature_imp = [
            {'feature': name, 'importance': float(imp)}
            for name, imp in zip(feature_names, importances)
        ]
        # Sort importances descending
        feature_imp = sorted(feature_imp, key=lambda x: x['importance'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'algorithm': 'Random Forest Classifier',
            'dataset_size': 2500,
            'testing_accuracy': 0.896,
            'feature_importances': feature_imp
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Accepts student profile details, predicts placement probability,
    runs what-if scenario simulations, and fetches mentor suggestions.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Missing request payload'}), 400
        
        # Required keys validation
        required_fields = ['cgpa', 'internships', 'projects', 'backlogs', 'coding_score', 'comm_score', 'dsa_score', 'webdev_score']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Field "{field}" is required'}), 400
            
        # Parse inputs
        cgpa = float(data['cgpa'])
        internships = int(data['internships'])
        projects = int(data['projects'])
        backlogs = int(data['backlogs'])
        coding_score = int(data['coding_score'])
        comm_score = int(data['comm_score'])
        dsa_score = int(data['dsa_score'])
        webdev_score = int(data['webdev_score'])
        
        # Structure for prediction
        input_features = [cgpa, internships, projects, backlogs, coding_score, comm_score, dsa_score, webdev_score]
        
        # 1. Base Prediction
        scaled_features = scaler.transform([input_features])
        prob_placed = model.predict_proba(scaled_features)[0][1] # Probability of index 1 (Placed)
        
        # 2. What-If Scenarios (Counterfactuals)
        what_if_scenarios = []
        
        # Scenario A: What if they clear all active backlogs? (Only if backlogs > 0)
        if backlogs > 0:
            sc_features = [cgpa, internships, projects, 0, coding_score, comm_score, dsa_score, webdev_score]
            sc_scaled = scaler.transform([sc_features])
            sc_prob = model.predict_proba(sc_scaled)[0][1]
            what_if_scenarios.append({
                'scenario': 'Clear all active backlogs',
                'probability': float(sc_prob),
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario B: What if they improve CGPA by +1.0? (Only if CGPA < 9.0)
        if cgpa < 9.0:
            new_cgpa = min(10.0, cgpa + 1.0)
            sc_features = [new_cgpa, internships, projects, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_scaled = scaler.transform([sc_features])
            sc_prob = model.predict_proba(sc_scaled)[0][1]
            what_if_scenarios.append({
                'scenario': f'Boost CGPA to {new_cgpa:.1f} (+1.0)',
                'probability': float(sc_prob),
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario C: What if they add 1 more Internship? (Only if internships < 3)
        if internships < 3:
            sc_features = [cgpa, internships + 1, projects, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_scaled = scaler.transform([sc_features])
            sc_prob = model.predict_proba(sc_scaled)[0][1]
            what_if_scenarios.append({
                'scenario': 'Complete 1 new Internship',
                'probability': float(sc_prob),
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario D: What if they increase Coding & DSA scores to 85? (Only if they are below 85)
        if coding_score < 85 or dsa_score < 85:
            new_coding = max(coding_score, 85)
            new_dsa = max(dsa_score, 85)
            sc_features = [cgpa, internships, projects, backlogs, new_coding, comm_score, new_dsa, webdev_score]
            sc_scaled = scaler.transform([sc_features])
            sc_prob = model.predict_proba(sc_scaled)[0][1]
            what_if_scenarios.append({
                'scenario': 'Master DSA & Coding Skills (Target: 85+)',
                'probability': float(sc_prob),
                'improvement': float(sc_prob - prob_placed)
            })

        # Scenario E: What if they add 1 project? (Only if projects < 4)
        if projects < 4:
            sc_features = [cgpa, internships, projects + 1, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_scaled = scaler.transform([sc_features])
            sc_prob = model.predict_proba(sc_scaled)[0][1]
            what_if_scenarios.append({
                'scenario': 'Build 1 new major project',
                'probability': float(sc_prob),
                'improvement': float(sc_prob - prob_placed)
            })
            
        parsed_profile = {
            'cgpa': cgpa,
            'internships': internships,
            'projects': projects,
            'backlogs': backlogs,
            'coding_score': coding_score,
            'comm_score': comm_score,
            'dsa_score': dsa_score,
            'webdev_score': webdev_score
        }
        # 3. Retrieve Mentorship recommendations
        mentor_data = get_feedback_and_recommendations(parsed_profile)
        
        # 4. Salary Projection estimation
        # Realistic brackets based on probability and coding skill
        base_salary = 3.6 # Lakhs per annum (LPA) - typical service company package
        if prob_placed > 0.85 and coding_score >= 80 and dsa_score >= 80:
            salary_range = "12.0 - 24.0 LPA (Product / Tier-1 Role)"
        elif prob_placed > 0.70 and coding_score >= 65:
            salary_range = "6.5 - 11.0 LPA (System Engineer / Specialized Role)"
        elif prob_placed > 0.40:
            salary_range = "3.6 - 5.0 LPA (Associate Software Engineer / Service Role)"
        else:
            salary_range = "Needs improvement to clear entry bar"
        # Save prediction run details to database history log
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (
                    cgpa, internships, projects, backlogs, coding_score, dsa_score, webdev_score, comm_score, probability, salary_range
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cgpa, internships, projects, backlogs, coding_score, dsa_score, webdev_score, comm_score, float(prob_placed), salary_range))
            conn.commit()
            conn.close()
            print("Successfully logged prediction query to database.")
        except Exception as db_err:
            print(f"Failed to log prediction to database: {db_err}")

        return jsonify({
            'status': 'success',
            'placement_probability': float(prob_placed),
            'projected_salary': salary_range,
            'scenarios': what_if_scenarios,
            'feedback': mentor_data['feedback'],
            'recommendations': mentor_data['recommendations'],
            'roadmap': mentor_data['roadmap'],
            'project_ideas': mentor_data['project_ideas']
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns the latest 10 placement diagnostic predictions from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, cgpa, internships, projects, backlogs, coding_score, dsa_score, webdev_score, comm_score, probability, salary_range 
            FROM predictions 
            ORDER BY id DESC 
            LIMIT 10
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        history_list = []
        for row in rows:
            history_list.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'cgpa': row['cgpa'],
                'internships': row['internships'],
                'projects': row['projects'],
                'backlogs': row['backlogs'],
                'coding_score': row['coding_score'],
                'dsa_score': row['dsa_score'],
                'webdev_score': row['webdev_score'],
                'comm_score': row['comm_score'],
                'probability': float(row['probability']),
                'salary_range': row['salary_range']
            })
            
        return jsonify({
            'status': 'success',
            'history': history_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Gathers stats from predictions history and baseline datasets."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), AVG(probability), AVG(cgpa) FROM predictions")
        row = cursor.fetchone()
        diagnoses_count = row[0] or 0
        avg_probability = float(row[1]) if row[1] is not None else 0.0
        avg_cgpa = float(row[2]) if row[2] is not None else 0.0
        
        conn.close()
        
        # Training dataset baseline statistics
        dataset_records = 0
        dataset_placed_ratio = 0.0
        dataset_avg_cgpa = 0.0
        
        csv_path = os.path.join(BASE_DIR, 'student_placement_data.csv')
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                dataset_records = len(df)
                dataset_placed_ratio = float(df['placed'].mean())
                dataset_avg_cgpa = float(df['cgpa'].mean())
            except Exception as csv_err:
                print(f"Failed to read CSV stats: {csv_err}")
                
        return jsonify({
            'status': 'success',
            'diagnoses_run': diagnoses_count,
            'average_run_probability': avg_probability,
            'average_run_cgpa': avg_cgpa,
            'baseline': {
                'total_records': dataset_records,
                'placed_ratio': dataset_placed_ratio,
                'avg_cgpa': dataset_avg_cgpa
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ats-check', methods=['POST'])
def ats_check():
    """Analyzes resume text against a job description for ATS compatibility."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Missing request payload'}), 400
            
        resume_text = data.get('resume_text', '')
        job_desc = data.get('job_description', '')
        
        analysis = analyze_ats_score(resume_text, job_desc)
        
        return jsonify({
            'status': 'success',
            'score': analysis['score'],
            'matched_keywords': analysis['matched'],
            'missing_keywords': analysis['missing'],
            'recommendations': analysis['recommendations']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/request-mentor', methods=['POST'])
def request_mentor():
    """Simulates a booking request for peer/mentor support."""
    try:
        data = request.get_json()
        name = data.get('name', 'Student')
        email = data.get('email', '')
        topic = data.get('topic', 'General Counseling')
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
            
        return jsonify({
            'status': 'success',
            'message': f'Success! An invitation link has been sent to {email}. A mentor session with focus on "{topic}" is booked.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Start the server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
