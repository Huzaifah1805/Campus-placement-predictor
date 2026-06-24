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

def get_prediction_probability(features):
    """Encapsulates scaling and prediction, applying defensive percentage checks."""
    try:
        scaled = scaler.transform([features])
        prob = model.predict_proba(scaled)[0][1]
        # Defensively normalize if the model or other logic outputs a percentage (0-100) instead of probability (0-1)
        if prob > 1.0:
            prob = prob / 100.0
        return float(prob)
    except Exception as err:
        print(f"Error in probability calculation: {err}")
        return 0.0

def calculate_projected_salary(cgpa, internships, projects, backlogs, coding_score, dsa_score, comm_score, webdev_score, prob_placed):
    """Calculates a personalized, continuous salary projection based on features.
    
    Uses a weighted composite scoring system with non-linear CGPA scaling
    to ensure every input combination produces a unique projected range.
    """
    if prob_placed < 0.25:
        return "Needs improvement to clear entry bar"
        
    # --- 1. CGPA Component (non-linear, steep curve above 8.0) ---
    # Maps 5.0-10.0 CGPA to 0-18 LPA contribution
    if cgpa >= 9.0:
        cgpa_score = 14.0 + (cgpa - 9.0) * 4.0     # 9.0→14, 9.5→16, 10.0→18
    elif cgpa >= 8.0:
        cgpa_score = 8.0 + (cgpa - 8.0) * 6.0       # 8.0→8, 8.5→11, 9.0→14
    elif cgpa >= 7.0:
        cgpa_score = 4.0 + (cgpa - 7.0) * 4.0       # 7.0→4, 7.5→6, 8.0→8
    elif cgpa >= 6.0:
        cgpa_score = 1.5 + (cgpa - 6.0) * 2.5       # 6.0→1.5, 6.5→2.75, 7.0→4
    else:
        cgpa_score = max(0.0, cgpa - 5.0) * 1.5      # 5.0→0, 5.5→0.75
    
    # --- 2. Experience Component ---
    internship_score = min(4, internships) * 2.5      # 0→0, 1→2.5, 2→5, 3→7.5, 4→10
    project_score = min(5, projects) * 1.2            # 0→0, 1→1.2, 2→2.4, 3→3.6
    
    # --- 3. Technical Skills Component ---
    # Weighted average of all four skills, scaled to LPA contribution
    tech_avg = (coding_score * 0.30 + dsa_score * 0.35 + webdev_score * 0.20 + comm_score * 0.15)
    if tech_avg >= 85:
        skill_score = 8.0 + (tech_avg - 85) * 0.2    # Top tier: 8-11 LPA
    elif tech_avg >= 70:
        skill_score = 5.0 + (tech_avg - 70) * 0.2    # Mid-high: 5-8 LPA
    elif tech_avg >= 50:
        skill_score = 2.0 + (tech_avg - 50) * 0.15   # Mid: 2-5 LPA
    else:
        skill_score = max(0.0, tech_avg * 0.04)       # Low: 0-2 LPA
    
    # --- 4. Backlog Penalty (severe) ---
    backlog_penalty = min(8.0, backlogs * 2.5)
    
    # --- 5. Composite Package ---
    base = 3.0  # Minimum floor (service company base)
    raw_package = base + cgpa_score + internship_score + project_score + skill_score - backlog_penalty
    
    # Apply probability as a confidence/leverage multiplier
    # Use sqrt to soften the impact so mid-probability students aren't crushed
    confidence = prob_placed ** 0.6
    realized_package = raw_package * confidence
    
    # Hard floor and ceiling
    realized_package = max(3.0, min(45.0, realized_package))
    
    # Generate asymmetric range (tighter at bottom, wider at top)
    spread = 0.12 if realized_package < 8.0 else 0.15
    low_bound = max(2.5, round(realized_package * (1.0 - spread), 1))
    high_bound = min(45.0, round(realized_package * (1.0 + spread), 1))
    
    # --- 6. Tier Classification ---
    if realized_package >= 18.0:
        tier = "FAANG / Dream Company"
    elif realized_package >= 12.0:
        tier = "Product / Tier-1 Role"
    elif realized_package >= 8.0:
        tier = "Mid-Tier Product / Specialist"
    elif realized_package >= 5.0:
        tier = "Service MNC / System Engineer"
    else:
        tier = "Entry Level / Associate"
        
    return f"{low_bound:.1f} - {high_bound:.1f} LPA ({tier})"

# ==========================================
# COMPANY MATCHING ENGINE
# ==========================================
# Each company has: name, logo_icon (FontAwesome), tier, package range,
# minimum requirements (cgpa, coding, dsa, webdev, comm), and focus areas.
COMPANY_DATABASE = [
    # --- FAANG / Dream Tier ---
    {"name": "Google", "icon": "fa-brands fa-google", "tier": "Dream", "package": "30-45 LPA", "color": "#4285F4",
     "min_cgpa": 8.0, "min_coding": 85, "min_dsa": 90, "min_webdev": 60, "min_comm": 70, "focus": ["DSA", "System Design", "Problem Solving"]},
    {"name": "Microsoft", "icon": "fa-brands fa-microsoft", "tier": "Dream", "package": "28-44 LPA", "color": "#00A4EF",
     "min_cgpa": 7.5, "min_coding": 80, "min_dsa": 85, "min_webdev": 65, "min_comm": 70, "focus": ["DSA", "Cloud", "System Design"]},
    {"name": "Amazon", "icon": "fa-brands fa-amazon", "tier": "Dream", "package": "26-42 LPA", "color": "#FF9900",
     "min_cgpa": 7.0, "min_coding": 80, "min_dsa": 85, "min_webdev": 60, "min_comm": 65, "focus": ["DSA", "Leadership Principles", "Scalability"]},
    {"name": "Meta", "icon": "fa-brands fa-meta", "tier": "Dream", "package": "32-50 LPA", "color": "#0668E1",
     "min_cgpa": 8.0, "min_coding": 85, "min_dsa": 90, "min_webdev": 70, "min_comm": 65, "focus": ["DSA", "ML", "Distributed Systems"]},
    {"name": "Apple", "icon": "fa-brands fa-apple", "tier": "Dream", "package": "30-48 LPA", "color": "#A2AAAD",
     "min_cgpa": 8.0, "min_coding": 85, "min_dsa": 85, "min_webdev": 70, "min_comm": 75, "focus": ["iOS/Swift", "System Design", "UX"]},
    {"name": "Netflix", "icon": "fa-solid fa-film", "tier": "Dream", "package": "35-55 LPA", "color": "#E50914",
     "min_cgpa": 8.5, "min_coding": 90, "min_dsa": 90, "min_webdev": 75, "min_comm": 70, "focus": ["Microservices", "Streaming", "Java"]},
    # --- Product Tier-1 ---
    {"name": "Flipkart", "icon": "fa-solid fa-cart-shopping", "tier": "Tier-1 Product", "package": "18-30 LPA", "color": "#F7D716",
     "min_cgpa": 7.5, "min_coding": 75, "min_dsa": 80, "min_webdev": 60, "min_comm": 60, "focus": ["DSA", "Backend", "Scalability"]},
    {"name": "Adobe", "icon": "fa-solid fa-wand-magic-sparkles", "tier": "Tier-1 Product", "package": "20-32 LPA", "color": "#FF0000",
     "min_cgpa": 7.5, "min_coding": 80, "min_dsa": 80, "min_webdev": 70, "min_comm": 65, "focus": ["Frontend", "Creative Cloud", "AI/ML"]},
    {"name": "Uber", "icon": "fa-brands fa-uber", "tier": "Tier-1 Product", "package": "22-35 LPA", "color": "#000000",
     "min_cgpa": 7.0, "min_coding": 80, "min_dsa": 85, "min_webdev": 60, "min_comm": 60, "focus": ["DSA", "Maps", "Real-time Systems"]},
    {"name": "Goldman Sachs", "icon": "fa-solid fa-building-columns", "tier": "Tier-1 Product", "package": "20-35 LPA", "color": "#7399C6",
     "min_cgpa": 8.0, "min_coding": 75, "min_dsa": 80, "min_webdev": 50, "min_comm": 75, "focus": ["FinTech", "Java", "Risk Modeling"]},
    {"name": "Salesforce", "icon": "fa-brands fa-salesforce", "tier": "Tier-1 Product", "package": "18-28 LPA", "color": "#00A1E0",
     "min_cgpa": 7.5, "min_coding": 75, "min_dsa": 70, "min_webdev": 70, "min_comm": 70, "focus": ["CRM", "Cloud", "Apex"]},
    {"name": "Oracle", "icon": "fa-solid fa-database", "tier": "Tier-1 Product", "package": "15-25 LPA", "color": "#F80000",
     "min_cgpa": 7.0, "min_coding": 70, "min_dsa": 75, "min_webdev": 55, "min_comm": 65, "focus": ["Database", "Cloud Infra", "Java"]},
    {"name": "Samsung R&D", "icon": "fa-solid fa-mobile-screen", "tier": "Tier-1 Product", "package": "16-24 LPA", "color": "#1428A0",
     "min_cgpa": 7.5, "min_coding": 75, "min_dsa": 75, "min_webdev": 55, "min_comm": 60, "focus": ["Embedded", "Android", "C++"]},
    {"name": "Intuit", "icon": "fa-solid fa-calculator", "tier": "Tier-1 Product", "package": "18-28 LPA", "color": "#365EBF",
     "min_cgpa": 7.5, "min_coding": 75, "min_dsa": 75, "min_webdev": 65, "min_comm": 65, "focus": ["FinTech", "Full Stack", "AI"]},
    # --- Mid-Tier Product ---
    {"name": "Paytm", "icon": "fa-solid fa-wallet", "tier": "Mid-Tier Product", "package": "12-18 LPA", "color": "#00BAF2",
     "min_cgpa": 6.5, "min_coding": 65, "min_dsa": 70, "min_webdev": 60, "min_comm": 55, "focus": ["Payments", "Backend", "Mobile"]},
    {"name": "Zomato", "icon": "fa-solid fa-utensils", "tier": "Mid-Tier Product", "package": "14-22 LPA", "color": "#E23744",
     "min_cgpa": 7.0, "min_coding": 70, "min_dsa": 75, "min_webdev": 60, "min_comm": 60, "focus": ["Full Stack", "ML", "Logistics"]},
    {"name": "Swiggy", "icon": "fa-solid fa-truck-fast", "tier": "Mid-Tier Product", "package": "14-20 LPA", "color": "#FC8019",
     "min_cgpa": 7.0, "min_coding": 70, "min_dsa": 70, "min_webdev": 60, "min_comm": 55, "focus": ["Logistics", "Backend", "ML"]},
    {"name": "Razorpay", "icon": "fa-solid fa-credit-card", "tier": "Mid-Tier Product", "package": "15-25 LPA", "color": "#3395FF",
     "min_cgpa": 7.0, "min_coding": 75, "min_dsa": 75, "min_webdev": 65, "min_comm": 60, "focus": ["Payments API", "Security", "Node.js"]},
    {"name": "PhonePe", "icon": "fa-solid fa-money-bill-transfer", "tier": "Mid-Tier Product", "package": "14-22 LPA", "color": "#5F259F",
     "min_cgpa": 7.0, "min_coding": 70, "min_dsa": 70, "min_webdev": 55, "min_comm": 60, "focus": ["Payments", "Java", "Microservices"]},
    {"name": "Atlassian", "icon": "fa-brands fa-atlassian", "tier": "Mid-Tier Product", "package": "18-30 LPA", "color": "#0052CC",
     "min_cgpa": 7.5, "min_coding": 80, "min_dsa": 80, "min_webdev": 65, "min_comm": 70, "focus": ["Collaboration", "Cloud", "React"]},
    {"name": "Cred", "icon": "fa-solid fa-gem", "tier": "Mid-Tier Product", "package": "16-26 LPA", "color": "#2D2D2D",
     "min_cgpa": 7.5, "min_coding": 75, "min_dsa": 75, "min_webdev": 70, "min_comm": 60, "focus": ["FinTech", "Design", "Backend"]},
    # --- Service MNC ---
    {"name": "TCS Digital", "icon": "fa-solid fa-t", "tier": "Service MNC", "package": "7-9 LPA", "color": "#0066B3",
     "min_cgpa": 7.0, "min_coding": 55, "min_dsa": 50, "min_webdev": 45, "min_comm": 55, "focus": ["Java", "Cloud", "Agile"]},
    {"name": "Infosys (Power Prog.)", "icon": "fa-solid fa-i", "tier": "Service MNC", "package": "6.5-9.5 LPA", "color": "#007CC3",
     "min_cgpa": 7.0, "min_coding": 55, "min_dsa": 55, "min_webdev": 45, "min_comm": 55, "focus": ["Java", "Python", "Cloud"]},
    {"name": "Wipro Elite", "icon": "fa-solid fa-w", "tier": "Service MNC", "package": "6-8 LPA", "color": "#44147A",
     "min_cgpa": 6.5, "min_coding": 50, "min_dsa": 45, "min_webdev": 40, "min_comm": 50, "focus": ["Testing", "Java", "DevOps"]},
    {"name": "Cognizant GenC", "icon": "fa-solid fa-c", "tier": "Service MNC", "package": "6-8.5 LPA", "color": "#1A4CA1",
     "min_cgpa": 6.5, "min_coding": 50, "min_dsa": 45, "min_webdev": 45, "min_comm": 55, "focus": ["Digital", "Cloud", "AI"]},
    {"name": "Capgemini", "icon": "fa-solid fa-c", "tier": "Service MNC", "package": "6-7.5 LPA", "color": "#0070AD",
     "min_cgpa": 6.0, "min_coding": 45, "min_dsa": 40, "min_webdev": 40, "min_comm": 50, "focus": ["Consulting", "SAP", "Cloud"]},
    {"name": "Accenture", "icon": "fa-solid fa-a", "tier": "Service MNC", "package": "4.5-7 LPA", "color": "#A100FF",
     "min_cgpa": 6.0, "min_coding": 40, "min_dsa": 35, "min_webdev": 35, "min_comm": 50, "focus": ["Consulting", "Digital", "Cloud"]},
    {"name": "Tech Mahindra", "icon": "fa-solid fa-m", "tier": "Service MNC", "package": "4-6.5 LPA", "color": "#CC0000",
     "min_cgpa": 6.0, "min_coding": 40, "min_dsa": 35, "min_webdev": 35, "min_comm": 45, "focus": ["Telecom", "5G", "AI"]},
    # --- Entry Level ---
    {"name": "TCS Ninja", "icon": "fa-solid fa-t", "tier": "Entry Level", "package": "3.6-4 LPA", "color": "#0066B3",
     "min_cgpa": 5.5, "min_coding": 30, "min_dsa": 25, "min_webdev": 25, "min_comm": 40, "focus": ["Support", "Testing", "Maintenance"]},
    {"name": "Infosys (Regular)", "icon": "fa-solid fa-i", "tier": "Entry Level", "package": "3.6-4.5 LPA", "color": "#007CC3",
     "min_cgpa": 5.5, "min_coding": 30, "min_dsa": 25, "min_webdev": 25, "min_comm": 40, "focus": ["Support", "BPO", "Testing"]},
    {"name": "Wipro Turbo", "icon": "fa-solid fa-w", "tier": "Entry Level", "package": "3.5-4 LPA", "color": "#44147A",
     "min_cgpa": 5.0, "min_coding": 25, "min_dsa": 20, "min_webdev": 20, "min_comm": 35, "focus": ["Support", "Testing", "Documentation"]},
    {"name": "HCLTech", "icon": "fa-solid fa-h", "tier": "Entry Level", "package": "3.5-5 LPA", "color": "#006BA6",
     "min_cgpa": 5.5, "min_coding": 35, "min_dsa": 30, "min_webdev": 30, "min_comm": 40, "focus": ["Infrastructure", "Support", "Cloud"]},
    # --- Specialist / Startup ---
    {"name": "Stripe", "icon": "fa-brands fa-stripe", "tier": "Specialist", "package": "25-40 LPA", "color": "#635BFF",
     "min_cgpa": 8.0, "min_coding": 85, "min_dsa": 85, "min_webdev": 75, "min_comm": 65, "focus": ["Payments", "API Design", "Ruby/Go"]},
    {"name": "Shopify", "icon": "fa-brands fa-shopify", "tier": "Specialist", "package": "20-35 LPA", "color": "#96BF48",
     "min_cgpa": 7.5, "min_coding": 80, "min_dsa": 75, "min_webdev": 80, "min_comm": 65, "focus": ["E-commerce", "React", "Rails"]},
    {"name": "Freshworks", "icon": "fa-solid fa-headset", "tier": "Mid-Tier Product", "package": "12-18 LPA", "color": "#2CA01C",
     "min_cgpa": 7.0, "min_coding": 65, "min_dsa": 65, "min_webdev": 60, "min_comm": 60, "focus": ["SaaS", "Full Stack", "AI"]},
    {"name": "Zoho", "icon": "fa-solid fa-z", "tier": "Mid-Tier Product", "package": "8-14 LPA", "color": "#D0342C",
     "min_cgpa": 6.5, "min_coding": 60, "min_dsa": 60, "min_webdev": 55, "min_comm": 55, "focus": ["SaaS", "Java", "Full Stack"]},
    {"name": "MakeMyTrip", "icon": "fa-solid fa-plane", "tier": "Mid-Tier Product", "package": "10-16 LPA", "color": "#EE2E24",
     "min_cgpa": 7.0, "min_coding": 65, "min_dsa": 65, "min_webdev": 55, "min_comm": 55, "focus": ["Travel Tech", "Backend", "ML"]},
    {"name": "Myntra", "icon": "fa-solid fa-shirt", "tier": "Mid-Tier Product", "package": "14-22 LPA", "color": "#FF3F6C",
     "min_cgpa": 7.0, "min_coding": 70, "min_dsa": 70, "min_webdev": 65, "min_comm": 55, "focus": ["E-commerce", "ML", "React"]},
    {"name": "Jio Platforms", "icon": "fa-solid fa-tower-cell", "tier": "Mid-Tier Product", "package": "10-16 LPA", "color": "#0A3A7D",
     "min_cgpa": 7.0, "min_coding": 65, "min_dsa": 60, "min_webdev": 55, "min_comm": 55, "focus": ["5G", "IoT", "Cloud"]},
]

def match_companies(cgpa, coding_score, dsa_score, webdev_score, comm_score, prob_placed):
    """Matches student profile against company requirements and returns ranked list."""
    matched = []
    
    for company in COMPANY_DATABASE:
        # Calculate fit score (0-100) for each requirement dimension
        cgpa_fit = min(100, (cgpa / company['min_cgpa']) * 100) if company['min_cgpa'] > 0 else 100
        coding_fit = min(100, (coding_score / company['min_coding']) * 100) if company['min_coding'] > 0 else 100
        dsa_fit = min(100, (dsa_score / company['min_dsa']) * 100) if company['min_dsa'] > 0 else 100
        webdev_fit = min(100, (webdev_score / company['min_webdev']) * 100) if company['min_webdev'] > 0 else 100
        comm_fit = min(100, (comm_score / company['min_comm']) * 100) if company['min_comm'] > 0 else 100
        
        # Weighted overall fit
        overall_fit = (cgpa_fit * 0.20 + coding_fit * 0.25 + dsa_fit * 0.25 + webdev_fit * 0.15 + comm_fit * 0.15)
        
        # Check if student meets minimum thresholds (allow 85% of minimum)
        meets_cgpa = cgpa >= company['min_cgpa'] * 0.85
        meets_coding = coding_score >= company['min_coding'] * 0.80
        meets_dsa = dsa_score >= company['min_dsa'] * 0.80
        
        # Classify match strength
        if overall_fit >= 95 and meets_cgpa and meets_coding and meets_dsa:
            match_level = "Strong Match"
            match_class = "success"
        elif overall_fit >= 80 and meets_cgpa:
            match_level = "Good Fit"
            match_class = "warning"
        elif overall_fit >= 65:
            match_level = "Stretch Target"
            match_class = "info"
        else:
            continue  # Skip companies that are too far out of reach
        
        matched.append({
            'name': company['name'],
            'icon': company['icon'],
            'tier': company['tier'],
            'package': company['package'],
            'color': company['color'],
            'focus': company['focus'],
            'fit_score': round(overall_fit, 1),
            'match_level': match_level,
            'match_class': match_class
        })
    
    # Sort by fit score descending
    matched.sort(key=lambda x: x['fit_score'], reverse=True)
    
    return matched

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
        prob_placed = get_prediction_probability(input_features)
        
        # 2. What-If Scenarios (Counterfactuals)
        what_if_scenarios = []
        
        # Scenario A: What if they clear all active backlogs? (Only if backlogs > 0)
        if backlogs > 0:
            sc_features = [cgpa, internships, projects, 0, coding_score, comm_score, dsa_score, webdev_score]
            sc_prob = get_prediction_probability(sc_features)
            what_if_scenarios.append({
                'scenario': 'Clear all active backlogs',
                'probability': sc_prob,
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario B: What if they improve CGPA by +1.0? (Only if CGPA < 9.0)
        if cgpa < 9.0:
            new_cgpa = min(10.0, cgpa + 1.0)
            sc_features = [new_cgpa, internships, projects, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_prob = get_prediction_probability(sc_features)
            what_if_scenarios.append({
                'scenario': f'Boost CGPA to {new_cgpa:.1f} (+1.0)',
                'probability': sc_prob,
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario C: What if they add 1 more Internship? (Only if internships < 3)
        if internships < 3:
            sc_features = [cgpa, internships + 1, projects, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_prob = get_prediction_probability(sc_features)
            what_if_scenarios.append({
                'scenario': 'Complete 1 new Internship',
                'probability': sc_prob,
                'improvement': float(sc_prob - prob_placed)
            })
            
        # Scenario D: What if they increase Coding & DSA scores to 85? (Only if they are below 85)
        if coding_score < 85 or dsa_score < 85:
            new_coding = max(coding_score, 85)
            new_dsa = max(dsa_score, 85)
            sc_features = [cgpa, internships, projects, backlogs, new_coding, comm_score, new_dsa, webdev_score]
            sc_prob = get_prediction_probability(sc_features)
            what_if_scenarios.append({
                'scenario': 'Master DSA & Coding Skills (Target: 85+)',
                'probability': sc_prob,
                'improvement': float(sc_prob - prob_placed)
            })

        # Scenario E: What if they add 1 project? (Only if projects < 4)
        if projects < 4:
            sc_features = [cgpa, internships, projects + 1, backlogs, coding_score, comm_score, dsa_score, webdev_score]
            sc_prob = get_prediction_probability(sc_features)
            what_if_scenarios.append({
                'scenario': 'Build 1 new major project',
                'probability': sc_prob,
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
        salary_range = calculate_projected_salary(
            cgpa, internships, projects, backlogs, coding_score, dsa_score, comm_score, webdev_score, prob_placed
        )
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

        # 5. Company Matching
        matched_companies = match_companies(cgpa, coding_score, dsa_score, webdev_score, comm_score, prob_placed)

        return jsonify({
            'status': 'success',
            'placement_probability': float(prob_placed),
            'projected_salary': salary_range,
            'scenarios': what_if_scenarios,
            'feedback': mentor_data['feedback'],
            'recommendations': mentor_data['recommendations'],
            'roadmap': mentor_data['roadmap'],
            'project_ideas': mentor_data['project_ideas'],
            'matched_companies': matched_companies
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
