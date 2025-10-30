import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.patient_db import PatientDB
from datetime import datetime, timedelta
import random

# Sample data for generating fake patients
FIRST_NAMES = [
    "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", 
    "James", "Maria", "William", "Jennifer", "Richard", "Patricia", "Charles",
    "Linda", "Joseph", "Barbara", "Thomas", "Elizabeth", "Christopher", "Susan",
    "Daniel", "Jessica", "Matthew", "Karen", "Anthony", "Nancy", "Mark", "Betty"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

NEPHROLOGY_DIAGNOSES = [
    "Chronic Kidney Disease Stage 3",
    "Acute Kidney Injury",
    "Diabetic Nephropathy",
    "Hypertensive Nephrosclerosis",
    "Glomerulonephritis",
    "Polycystic Kidney Disease",
    "Nephrotic Syndrome",
    "Kidney Stones",
    "Chronic Kidney Disease Stage 4",
    "End-Stage Renal Disease",
    "Acute Glomerulonephritis",
    "Lupus Nephritis",
    "IgA Nephropathy",
    "Minimal Change Disease",
    "Focal Segmental Glomerulosclerosis"
]

SYMPTOMS_SETS = [
    "Fatigue, swelling in legs and ankles, decreased urine output",
    "Nausea, vomiting, loss of appetite, metallic taste",
    "Shortness of breath, chest pain, irregular heartbeat",
    "Back pain, blood in urine, frequent urination",
    "Foamy urine, protein in urine, high blood pressure",
    "Severe flank pain, nausea, vomiting, fever",
    "Swelling around eyes, weight gain, decreased urine",
    "Muscle cramps, weakness, bone pain, itching",
    "Headaches, blurred vision, dizziness",
    "Difficulty concentrating, sleep problems, restless legs"
]

LAB_RESULTS_TEMPLATES = [
    "Creatinine: {cr} mg/dL, BUN: {bun} mg/dL, eGFR: {egfr} mL/min/1.73m², Proteinuria: {prot}",
    "Serum Creatinine: {cr} mg/dL, Urea: {bun} mg/dL, GFR: {egfr}, Albumin: {alb} g/dL",
    "Kidney function: Cr {cr}, BUN {bun}, eGFR {egfr}, Protein/Creatinine ratio: {pcr}",
    "Renal panel: Creatinine {cr} mg/dL, BUN {bun} mg/dL, eGFR {egfr} mL/min/1.73m²"
]

MEDICATIONS_SETS = [
    "Lisinopril 10mg daily, Furosemide 40mg daily, Sodium bicarbonate 650mg BID",
    "Losartan 50mg daily, Amlodipine 5mg daily, Atorvastatin 20mg daily",
    "Enalapril 5mg BID, Metoprolol 25mg BID, Calcitriol 0.25mcg daily",
    "Valsartan 80mg daily, Hydrochlorothiazide 25mg daily, Allopurinol 100mg daily",
    "Ramipril 2.5mg daily, Carvedilol 6.25mg BID, Sevelamer 800mg TID",
    "Telmisartan 40mg daily, Indapamide 2.5mg daily, Cinacalcet 30mg daily"
]

TREATMENT_PLANS = [
    "Dietary sodium restriction, regular nephrology follow-up, blood pressure monitoring",
    "Fluid restriction, phosphorus binders, vitamin D supplementation, dialysis preparation",
    "ACE inhibitor therapy, diabetes management, cardiovascular risk reduction",
    "Blood pressure control, proteinuria reduction, lifestyle modifications",
    "Immunosuppressive therapy, infection prevention, regular monitoring",
    "Conservative management, symptom control, patient education"
]

DOCTOR_NOTES_TEMPLATES = [
    "Patient presents with {condition}. Recommend close monitoring and medication adjustment. Follow-up in 4 weeks.",
    "Stable chronic condition. Continue current therapy. Patient education provided regarding diet and fluid intake.",
    "Acute presentation requiring immediate intervention. Started on appropriate therapy. Monitor closely.",
    "Progressive disease noted. Discussed treatment options including dialysis preparation. Social work consult.",
    "Good response to current treatment. Continue monitoring kidney function. Lifestyle counseling provided.",
    "Complicated case requiring multidisciplinary approach. Coordinated care with cardiology and endocrinology."
]

def generate_lab_values(diagnosis):
    """Generate realistic lab values based on diagnosis"""
    if "Stage 3" in diagnosis:
        cr = round(random.uniform(1.5, 2.4), 1)
        egfr = random.randint(30, 59)
        bun = random.randint(25, 45)
    elif "Stage 4" in diagnosis:
        cr = round(random.uniform(2.5, 4.9), 1)
        egfr = random.randint(15, 29)
        bun = random.randint(45, 80)
    elif "End-Stage" in diagnosis:
        cr = round(random.uniform(5.0, 12.0), 1)
        egfr = random.randint(5, 14)
        bun = random.randint(80, 150)
    elif "Acute" in diagnosis:
        cr = round(random.uniform(2.0, 8.0), 1)
        egfr = random.randint(10, 45)
        bun = random.randint(30, 100)
    else:
        cr = round(random.uniform(1.2, 3.0), 1)
        egfr = random.randint(25, 75)
        bun = random.randint(20, 60)
    
    # Additional values
    alb = round(random.uniform(2.5, 4.5), 1)
    prot = random.choice(["Negative", "Trace", "1+", "2+", "3+"])
    pcr = round(random.uniform(0.1, 5.0), 1)
    
    template = random.choice(LAB_RESULTS_TEMPLATES)
    return template.format(cr=cr, bun=bun, egfr=egfr, prot=prot, alb=alb, pcr=pcr)

def generate_fake_patients(num_patients=30):
    """Generate fake patient data"""
    db = PatientDB()
    
    for i in range(1, num_patients + 1):
        # Generate basic info
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        age = random.randint(25, 85)
        gender = random.choice(["Male", "Female"])
        diagnosis = random.choice(NEPHROLOGY_DIAGNOSES)
        
        # Generate patient ID
        patient_id = f"NEP{str(i).zfill(4)}"
        
        # Generate symptoms
        symptoms = random.choice(SYMPTOMS_SETS)
        
        # Generate lab results based on diagnosis
        lab_results = generate_lab_values(diagnosis)
        
        # Generate treatment and medications
        treatment_plan = random.choice(TREATMENT_PLANS)
        medications = random.choice(MEDICATIONS_SETS)
        
        # Generate admission date (within last 6 months)
        days_ago = random.randint(1, 180)
        date_admitted = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Generate doctor notes
        doctor_notes = random.choice(DOCTOR_NOTES_TEMPLATES).format(condition=diagnosis.lower())
        
        # Prepare patient data tuple
        patient_data = (
            patient_id, name, age, gender, diagnosis, symptoms,
            lab_results, treatment_plan, medications, date_admitted, doctor_notes
        )
        
        try:
            db.add_patient(patient_data)
            print(f"Added patient {i}: {name} ({patient_id})")
        except Exception as e:
            print(f"Error adding patient {i}: {e}")
    
    print(f"\nSuccessfully generated {num_patients} fake patients!")
    
    # Display some statistics
    all_patients = db.get_all_patients()
    print(f"Total patients in database: {len(all_patients)}")
    
    # Show a sample patient
    if all_patients:
        sample = all_patients[0]
        print(f"\nSample patient record:")
        print(f"ID: {sample[1]}, Name: {sample[2]}, Age: {sample[3]}")
        print(f"Diagnosis: {sample[5]}")
        print(f"Symptoms: {sample[6]}")

if __name__ == "__main__":
    print("Starting patient generation...")
    try:
        generate_fake_patients(30)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()