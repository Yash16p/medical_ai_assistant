import os
import sys
from datetime import datetime, timedelta
import re

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from patient_db import PatientDB
from logger import get_logger, get_system_logger
import json

logger = get_logger("receptionist_agent")
system_logger = get_system_logger()

class ReceptionistAgent:
    def __init__(self):
        """Initialize the Receptionist Agent with patient database access."""
        logger.info("Initializing Receptionist Agent...")
        
        # Initialize patient database
        self.patient_db = PatientDB()
        
        # Load discharge reports
        self.discharge_reports = self._load_discharge_reports()
        
        # Common greeting responses
        self.greetings = [
            "Hello! I'm your post-discharge care assistant. What's your name?",
            "Good day! I'm here to help with your post-discharge care. May I have your name?",
            "Welcome! I'm here to assist with your discharge follow-up. What's your name?"
        ]
        
        logger.info("Receptionist Agent initialized successfully")
    
    def greet_patient(self):
        """Provide a friendly greeting."""
        import random
        greeting = random.choice(self.greetings)
        logger.info("Greeting provided to patient/visitor")
        return {
            "status": "success",
            "message": greeting,
            "timestamp": datetime.now().isoformat()
        }
    
    def post_discharge_greeting(self, patient_name, session_id=None):
        """Generate personalized greeting after finding patient discharge report."""
        logger.info(f"Generating post-discharge greeting for: {patient_name}")
        
        # Log system flow
        system_logger.log_system_flow(
            "receptionist_greeting_start",
            f"Receptionist agent starting greeting process for: {patient_name}",
            session_id
        )
        
        # Use enhanced patient data retrieval tool
        from patient_lookup import PatientDataRetrievalTool
        patient_tool = PatientDataRetrievalTool()
        
        # Get discharge report
        discharge_result = patient_tool.get_discharge_report(patient_name, session_id)
        
        if discharge_result["status"] == "success":
            report = discharge_result["data"]
            
            # Generate personalized greeting
            greeting = f"Hi {report['patient_name']}! I found your discharge report from {report['discharge_date']} for {report['primary_diagnosis']}. How are you feeling today? Are you following your medication schedule?"
            
            logger.info(f"Generated personalized greeting for {patient_name}")
            
            # Log successful patient identification
            system_logger.log_system_flow(
                "receptionist_patient_found",
                f"Successfully found patient: {report['patient_name']} - {report['primary_diagnosis']}",
                session_id
            )
            
            return {
                "status": "success",
                "greeting": greeting,
                "discharge_report": report,
                "timestamp": datetime.now().isoformat()
            }
        
        elif discharge_result["status"] == "not_found":
            # Patient not found
            greeting = f"Hello! I couldn't find your discharge report for '{patient_name}'. Could you please verify your name spelling?"
            
            logger.warning(f"No discharge report found for: {patient_name}")
            
            # Log failed patient lookup
            system_logger.log_system_flow(
                "receptionist_patient_not_found",
                f"Patient not found: {patient_name}",
                session_id
            )
            
            return {
                "status": "not_found",
                "greeting": greeting,
                "timestamp": datetime.now().isoformat()
            }
        
        elif discharge_result["status"] == "multiple_found":
            # Multiple patients found
            greeting = f"Hello! I found multiple patients with the name '{patient_name}'. Could you please provide your full name or patient ID?"
            
            logger.warning(f"Multiple patients found for: {patient_name}")
            
            # Log multiple patients found
            system_logger.log_system_flow(
                "receptionist_multiple_patients",
                f"Multiple patients found for: {patient_name}, count: {discharge_result.get('count', 0)}",
                session_id
            )
            
            return {
                "status": "multiple_found",
                "greeting": greeting,
                "patients": discharge_result.get("patients", []),
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            # Error occurred
            greeting = f"Hello! I'm having trouble accessing your records. Please try again later."
            
            logger.error(f"Error during patient lookup for {patient_name}: {discharge_result.get('error', 'Unknown error')}")
            
            # Log error
            system_logger.log_system_flow(
                "receptionist_lookup_error",
                f"Error during patient lookup for {patient_name}: {discharge_result.get('error', 'Unknown error')}",
                session_id
            )
            
            return {
                "status": "error",
                "greeting": greeting,
                "error": discharge_result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
    
    def _log_patient_interaction(self, interaction_type: str, details: str):
        """Log patient interactions for audit and analysis."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction_type,
                "details": details,
                "agent": "receptionist"
            }
            logger.info(f"Patient interaction logged: {log_entry}")
            
            # In production, this would write to a dedicated audit log or database
            # For now, we use the standard logger
            
        except Exception as e:
            logger.error(f"Failed to log patient interaction: {e}")
    
    def find_patient_by_name(self, name: str):
        """Search for a patient by name with fuzzy matching."""
        logger.info(f"Searching for patient by name: {name}")
        
        try:
            # Try exact match first
            patients = self.patient_db.search_patients(name)
            
            if not patients:
                # Try partial matching
                name_parts = name.lower().split()
                for part in name_parts:
                    if len(part) > 2:  # Only search meaningful parts
                        patients = self.patient_db.search_patients(part)
                        if patients:
                            break
            
            if patients:
                if len(patients) == 1:
                    patient = patients[0]
                    patient_data = {
                        "patient_id": patient[1],
                        "name": patient[2],
                        "age": patient[3],
                        "gender": patient[4],
                        "diagnosis": patient[5],
                        "symptoms": patient[6],
                        "lab_results": patient[7],
                        "treatment_plan": patient[8],
                        "medications": patient[9],
                        "date_admitted": patient[10],
                        "doctor_notes": patient[11]
                    }
                    
                    logger.info(f"Patient found: {patient_data['name']} ({patient_data['patient_id']})")
                    return {
                        "status": "success",
                        "data": patient_data,
                        "message": f"Found patient: {patient_data['name']}"
                    }
                else:
                    # Multiple patients found
                    patient_list = []
                    for patient in patients:
                        patient_list.append({
                            "patient_id": patient[1],
                            "name": patient[2],
                            "age": patient[3],
                            "diagnosis": patient[5]
                        })
                    
                    logger.info(f"Multiple patients found for name: {name}")
                    return {
                        "status": "multiple",
                        "data": patient_list,
                        "message": f"Found {len(patients)} patients. Please specify which one:",
                        "count": len(patients)
                    }
            else:
                logger.warning(f"No patient found for name: {name}")
                return {
                    "status": "not_found",
                    "message": f"Sorry, I couldn't find any patient named '{name}'. Could you please check the spelling or provide more details?"
                }
                
        except Exception as e:
            logger.error(f"Error searching for patient: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble accessing the patient database. Please try again in a moment."
            }
    
    def find_patient_by_id(self, patient_id: str):
        """Find a patient by their ID."""
        logger.info(f"Looking up patient by ID: {patient_id}")
        
        try:
            patient = self.patient_db.get_patient(patient_id)
            
            if patient:
                patient_data = {
                    "patient_id": patient[1],
                    "name": patient[2],
                    "age": patient[3],
                    "gender": patient[4],
                    "diagnosis": patient[5],
                    "symptoms": patient[6],
                    "lab_results": patient[7],
                    "treatment_plan": patient[8],
                    "medications": patient[9],
                    "date_admitted": patient[10],
                    "doctor_notes": patient[11]
                }
                
                logger.info(f"Patient found by ID: {patient_data['name']} ({patient_id})")
                return {
                    "status": "success",
                    "data": patient_data,
                    "message": f"Found patient: {patient_data['name']}"
                }
            else:
                logger.warning(f"No patient found with ID: {patient_id}")
                return {
                    "status": "not_found",
                    "message": f"Sorry, I couldn't find a patient with ID '{patient_id}'. Please check the ID and try again."
                }
                
        except Exception as e:
            logger.error(f"Error looking up patient by ID: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble accessing the patient database. Please try again in a moment."
            }
    
    def search_patients_by_condition(self, condition: str):
        """Search for patients by medical condition."""
        logger.info(f"Searching patients by condition: {condition}")
        
        try:
            patients = self.patient_db.search_patients(condition)
            
            if patients:
                patient_list = []
                for patient in patients:
                    patient_list.append({
                        "patient_id": patient[1],
                        "name": patient[2],
                        "age": patient[3],
                        "diagnosis": patient[5],
                        "date_admitted": patient[10]
                    })
                
                logger.info(f"Found {len(patients)} patients with condition: {condition}")
                return {
                    "status": "success",
                    "data": patient_list,
                    "message": f"Found {len(patients)} patients with '{condition}'",
                    "count": len(patients)
                }
            else:
                logger.info(f"No patients found with condition: {condition}")
                return {
                    "status": "not_found",
                    "message": f"No patients found with condition '{condition}'"
                }
                
        except Exception as e:
            logger.error(f"Error searching by condition: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble searching the patient database. Please try again."
            }
    
    def get_clinic_statistics(self):
        """Get basic clinic statistics for reception dashboard."""
        logger.info("Generating clinic statistics")
        
        try:
            all_patients = self.patient_db.get_all_patients()
            
            # Basic counts
            total_patients = len(all_patients)
            
            # Age distribution
            ages = [patient[3] for patient in all_patients]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            # Gender distribution
            genders = [patient[4] for patient in all_patients]
            male_count = genders.count("Male")
            female_count = genders.count("Female")
            
            # Most common diagnoses
            diagnoses = [patient[5] for patient in all_patients]
            diagnosis_counts = {}
            for diagnosis in diagnoses:
                diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
            
            # Sort diagnoses by frequency
            top_diagnoses = sorted(diagnosis_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            statistics = {
                "total_patients": total_patients,
                "average_age": round(avg_age, 1),
                "gender_distribution": {
                    "male": male_count,
                    "female": female_count
                },
                "top_diagnoses": [{"diagnosis": d[0], "count": d[1]} for d in top_diagnoses]
            }
            
            logger.info("Clinic statistics generated successfully")
            return {
                "status": "success",
                "data": statistics,
                "message": "Clinic statistics ready"
            }
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            return {
                "status": "error",
                "message": "Error generating clinic statistics"
            }
    
    def _load_discharge_reports(self):
        """Load discharge reports from JSON file."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            reports_file = os.path.join(base_dir, "data", "discharge_reports.json")
            
            if os.path.exists(reports_file):
                with open(reports_file, 'r', encoding='utf-8') as f:
                    reports = json.load(f)
                logger.info(f"Loaded {len(reports)} discharge reports")
                return {report['patient_name'].lower(): report for report in reports}
            else:
                logger.warning("Discharge reports file not found")
                return {}
        except Exception as e:
            logger.error(f"Error loading discharge reports: {e}")
            return {}
    
    def get_discharge_report(self, patient_name: str):
        """Retrieve discharge report for a patient from database."""
        logger.info(f"Retrieving discharge report for: {patient_name}")
        
        try:
            # Search for patient in database
            patients = self.patient_db.search_patients(patient_name)
            
            if patients and len(patients) > 0:
                # Get the first matching patient
                patient = patients[0]
                
                # Convert database format to discharge report format
                report = {
                    "patient_name": patient[2],  # name
                    "discharge_date": patient[10],  # date_admitted
                    "primary_diagnosis": patient[5],  # diagnosis
                    "medications": patient[8].split(', ') if patient[8] else [],  # medications
                    "dietary_restrictions": "Low sodium (2g/day), fluid restriction as advised",
                    "follow_up": "Nephrology clinic in 1-2 weeks",
                    "warning_signs": "Swelling, shortness of breath, decreased urine output",
                    "discharge_instructions": "Take medications as prescribed, monitor symptoms"
                }
                
                logger.info(f"Discharge report found for {patient_name}")
                return {
                    "status": "success",
                    "data": report,
                    "message": f"Found discharge report for {report['patient_name']}"
                }
            
            logger.warning(f"No discharge report found for: {patient_name}")
            return {
                "status": "not_found",
                "message": f"I couldn't find a discharge report for '{patient_name}'. Could you please check the spelling?"
            }
                
        except Exception as e:
            logger.error(f"Error retrieving discharge report: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble accessing the discharge reports. Please try again."
            }
    
