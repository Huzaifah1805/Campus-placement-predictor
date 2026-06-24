import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# Set random seed for reproducibility
np.random.seed(42)

# Get base directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_synthetic_data(num_samples=2000):
    """
    Generates a realistic synthetic dataset representing student placement profiles.
    """
    data = []
    for _ in range(num_samples):
        # Generate features
        cgpa = round(np.random.uniform(5.0, 10.0), 2)
        internships = int(np.random.choice([0, 1, 2, 3], p=[0.5, 0.35, 0.12, 0.03]))
        projects = int(np.random.choice([0, 1, 2, 3, 4], p=[0.15, 0.4, 0.3, 0.1, 0.05]))
        backlogs = int(np.random.choice([0, 1, 2, 3, 4, 5], p=[0.75, 0.15, 0.06, 0.02, 0.01, 0.01]))
        
        # Skill scores (out of 100)
        coding_score = int(np.clip(np.random.normal(60, 18), 20, 100))
        comm_score = int(np.clip(np.random.normal(65, 15), 30, 100))
        dsa_score = int(np.clip(np.random.normal(55, 20), 10, 100))
        webdev_score = int(np.clip(np.random.normal(58, 18), 10, 100))
        
        # Calculate logit for probability
        utility = 0.0
        
        # CGPA impact (severe penalty below 6.0, boost above 8.0)
        if cgpa < 6.0:
            utility -= 3.5
        elif cgpa < 7.0:
            utility -= 1.0
        elif cgpa >= 8.5:
            utility += 2.0
            
        utility += 1.5 * (cgpa - 7.5)  # continuous CGPA effect
        
        # Backlog penalty (severe)
        if backlogs > 0:
            utility -= 2.2 * backlogs
            
        # Internships and Projects boosts
        utility += 1.6 * internships
        utility += 0.8 * projects
        
        # Technical/Communication Skills contribution
        utility += 0.04 * (coding_score - 60)
        utility += 0.035 * (dsa_score - 55)
        utility += 0.025 * (comm_score - 65)
        utility += 0.015 * (webdev_score - 58)
        
        # Combined skill synergy boost (e.g. good coding + good DSA)
        if coding_score > 75 and dsa_score > 75:
            utility += 1.5
            
        # Sigmoid probability
        prob = 1.0 / (1.0 + np.exp(-utility))
        
        # Add slight randomness/noise
        placed = 1 if np.random.random() < prob else 0
        
        data.append({
            'cgpa': cgpa,
            'internships': internships,
            'projects': projects,
            'backlogs': backlogs,
            'coding_score': coding_score,
            'comm_score': comm_score,
            'dsa_score': dsa_score,
            'webdev_score': webdev_score,
            'placed': placed
        })
        
    df = pd.DataFrame(data)
    return df

def train_and_save_model():
    print("Generating synthetic student data...")
    df = generate_synthetic_data(2500)
    
    # Save the synthetic dataset for references in base dir
    csv_path = os.path.join(BASE_DIR, "student_placement_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path}")
    
    # Separate features and target
    X = df.drop(columns=['placed'])
    y = df['placed']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest Classifier
    print("Training RandomForest Classifier...")
    model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    train_acc = model.score(X_train_scaled, y_train)
    test_acc = model.score(X_test_scaled, y_test)
    print(f"Training Accuracy: {train_acc:.4f}")
    print(f"Testing Accuracy: {test_acc:.4f}")
    
    # Save model and scaler
    model_data = {
        'model': model,
        'scaler': scaler,
        'feature_names': list(X.columns)
    }
    
    pkl_path = os.path.join(BASE_DIR, "placement_model.pkl")
    with open(pkl_path, "wb") as f:
        pickle.dump(model_data, f)
    print(f"Model and Scaler successfully saved to {pkl_path}")
    
    # Print feature importances
    importances = model.feature_importances_
    for name, imp in zip(X.columns, importances):
        print(f"Feature: {name:15s} Importance: {imp:.4f}")

if __name__ == "__main__":
    train_and_save_model()
