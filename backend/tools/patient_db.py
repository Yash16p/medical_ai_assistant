import sqlite3
import os
from datetime import datetime, timedelta
import random

class PatientDB:
    def __init__(self, db_path="backend/data/patients.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with patient table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                lab_results TEXT NOT NULL,
                treatment_plan TEXT NOT NULL,
                medications TEXT NOT NULL,
                date_admitted TEXT NOT NULL,
                doctor_notes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_patient(self, patient_data):
        """Add a new patient to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO patients (patient_id, name, age, gender, diagnosis, symptoms, 
                                lab_results, treatment_plan, medications, date_admitted, doctor_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', patient_data)
        
        conn.commit()
        conn.close()
    
    def get_patient(self, patient_id):
        """Get a patient by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result
    
    def get_all_patients(self):
        """Get all patients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients')
        results = cursor.fetchall()
        
        conn.close()
        return results
    
    def search_patients(self, query):
        """Search patients by name, diagnosis, or symptoms"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM patients 
            WHERE name LIKE ? OR diagnosis LIKE ? OR symptoms LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        return results