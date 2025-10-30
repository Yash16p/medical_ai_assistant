import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from logger import get_logger, get_system_logger

logger = get_logger("patient_lookup")
system_logger = get_system_logger()

class PatientDataRetrievalTool:
    """Enhanced patient data retrieval tool with comprehensive logging and error handling."""
    
    def __init__(self):
        self.db_path = "backend/data/patients.db"
        logger.info("Patient Data Retrieval Tool initialized")
    
    def lookup_patient_by_name(self, name: str, session_id: str = None) -> Dict[str, Any]:
        """
        Lookup patient by name or patient ID with comprehensive logging and error handling.
        
        Args:
            name: Patient name or patient ID to search for
            session_id: Session identifier for logging
            
        Returns:
            Structured response with patient data or error information
        """
        start_time = time.time()
        logger.info(f"Starting patient lookup for: {name}")
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_start", 
            f"Initiating patient lookup for: {name}",
            session_id
        )
        
        try:
            # Database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if input looks like a patient ID (starts with NEP followed by digits)
            is_patient_id = name.strip().upper().startswith('NEP') and name.strip()[3:].isdigit()
            
            if is_patient_id:
                # Search by patient ID
                search_query = '''
                    SELECT * FROM patients 
                    WHERE UPPER(patient_id) = UPPER(?)
                    ORDER BY name
                '''
                search_params = name.strip()
                search_type = "patient_id"
            else:
                # Search by name
                search_query = '''
                    SELECT * FROM patients 
                    WHERE LOWER(name) LIKE LOWER(?)
                    ORDER BY name
                '''
                search_params = f'%{name.strip()}%'
                search_type = "name"
            
            cursor.execute(search_query, (search_params,))
            results = cursor.fetchall()
            conn.close()
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log database access
            system_logger.log_database_access(
                operation="SELECT",
                table="patients",
                query_params={f"{search_type}_search": name},
                result_count=len(results),
                success=True
            )
            
            # Handle different result scenarios
            if not results:
                return self._handle_no_patient_found(name, execution_time, session_id, search_type)
            elif len(results) == 1:
                return self._handle_single_patient_found(results[0], name, execution_time, session_id)
            else:
                return self._handle_multiple_patients_found(results, name, execution_time, session_id)
                
        except sqlite3.Error as db_error:
            execution_time = (time.time() - start_time) * 1000
            return self._handle_database_error(db_error, name, execution_time, session_id)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self._handle_general_error(e, name, execution_time, session_id)
    
    def lookup_patient_by_id(self, patient_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Lookup patient by patient ID with comprehensive logging and error handling.
        
        Args:
            patient_id: Patient ID to search for (e.g., NEP0001)
            session_id: Session identifier for logging
            
        Returns:
            Structured response with patient data or error information
        """
        start_time = time.time()
        logger.info(f"Starting patient lookup by ID: {patient_id}")
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_by_id_start", 
            f"Initiating patient lookup for ID: {patient_id}",
            session_id
        )
        
        try:
            # Database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search by patient ID (exact match)
            search_query = '''
                SELECT * FROM patients 
                WHERE UPPER(patient_id) = UPPER(?)
            '''
            
            cursor.execute(search_query, (patient_id.strip(),))
            results = cursor.fetchall()
            conn.close()
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log database access
            system_logger.log_database_access(
                operation="SELECT",
                table="patients",
                query_params={"patient_id_search": patient_id},
                result_count=len(results),
                success=True
            )
            
            # Handle result
            if not results:
                return self._handle_no_patient_found(patient_id, execution_time, session_id, "patient_id")
            else:
                return self._handle_single_patient_found(results[0], patient_id, execution_time, session_id)
                
        except sqlite3.Error as db_error:
            execution_time = (time.time() - start_time) * 1000
            return self._handle_database_error(db_error, patient_id, execution_time, session_id)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self._handle_general_error(e, patient_id, execution_time, session_id)
    
    def get_discharge_report(self, patient_name: str, session_id: str = None) -> Dict[str, Any]:
        """
        Get structured discharge report data for a patient.
        
        Args:
            patient_name: Name of the patient
            session_id: Session identifier for logging
            
        Returns:
            Structured discharge report or error information
        """
        logger.info(f"Retrieving discharge report for: {patient_name}")
        
        # First lookup the patient
        lookup_result = self.lookup_patient_by_name(patient_name, session_id)
        
        if lookup_result["status"] != "success":
            return lookup_result
        
        # Convert patient data to discharge report format
        patient_data = lookup_result["data"]
        
        try:
            discharge_report = {
                "patient_name": patient_data["name"],
                "patient_id": patient_data["patient_id"],
                "discharge_date": patient_data["date_admitted"],
                "primary_diagnosis": patient_data["diagnosis"],
                "medications": self._parse_medications(patient_data["medications"]),
                "lab_results": patient_data["lab_results"],
                "treatment_plan": patient_data["treatment_plan"],
                "symptoms": patient_data["symptoms"],
                "doctor_notes": patient_data["doctor_notes"],
                "dietary_restrictions": "Low sodium (2g/day), fluid restriction as advised",
                "follow_up": "Nephrology clinic in 1-2 weeks",
                "warning_signs": "Swelling, shortness of breath, decreased urine output",
                "discharge_instructions": "Take medications as prescribed, monitor symptoms"
            }
            
            # Log successful discharge report retrieval
            system_logger.log_information_retrieval(
                source_type="database",
                query=f"discharge_report:{patient_name}",
                success=True,
                result_summary=f"Retrieved discharge report for {patient_data['name']} - {patient_data['diagnosis']}",
                response_length=len(str(discharge_report))
            )
            
            logger.info(f"Discharge report successfully retrieved for {patient_name}")
            
            return {
                "status": "success",
                "data": discharge_report,
                "message": f"Discharge report retrieved for {patient_data['name']}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error formatting discharge report for {patient_name}: {e}")
            return {
                "status": "error",
                "message": "Error formatting discharge report data",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _handle_no_patient_found(self, name: str, execution_time: float, session_id: str = None, search_type: str = "name") -> Dict[str, Any]:
        """Handle case where no patient is found."""
        logger.warning(f"No patient found for {search_type}: {name}")
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_no_results",
            f"No patient found matching {search_type}: {name}",
            session_id
        )
        
        if search_type == "patient_id":
            message = f"No patient found with ID '{name}'. Please verify the patient ID is correct."
            suggestions = [
                "Check the patient ID format (e.g., NEP0001)",
                "Verify the ID with reception",
                "Try searching by patient name instead"
            ]
        else:
            message = f"No patient found with name '{name}'. Please verify the name spelling."
            suggestions = [
                "Check the spelling of the patient name",
                "Try using just the first or last name",
                "Contact reception for assistance"
            ]
        
        return {
            "status": "not_found",
            "message": message,
            "suggestions": suggestions,
            "search_type": search_type,
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_single_patient_found(self, patient_row: tuple, name: str, execution_time: float, session_id: str = None) -> Dict[str, Any]:
        """Handle case where exactly one patient is found."""
        # Format patient data
        patient_data = {
            "patient_id": patient_row[1],
            "name": patient_row[2],
            "age": patient_row[3],
            "gender": patient_row[4],
            "diagnosis": patient_row[5],
            "symptoms": patient_row[6],
            "lab_results": patient_row[7],
            "treatment_plan": patient_row[8],
            "medications": patient_row[9],
            "date_admitted": patient_row[10],
            "doctor_notes": patient_row[11]
        }
        
        logger.info(f"Patient found: {patient_data['name']} ({patient_data['patient_id']})")
        
        # Log successful information retrieval
        system_logger.log_information_retrieval(
            source_type="database",
            query=f"patient_lookup:{name}",
            success=True,
            result_summary=f"Found patient: {patient_data['name']} - {patient_data['diagnosis']}",
            response_length=len(str(patient_data)),
            retrieval_time_ms=execution_time
        )
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_success",
            f"Successfully found patient: {patient_data['name']} ({patient_data['patient_id']})",
            session_id
        )
        
        return {
            "status": "success",
            "data": patient_data,
            "message": f"Patient found: {patient_data['name']}",
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_multiple_patients_found(self, patient_rows: List[tuple], name: str, execution_time: float, session_id: str = None) -> Dict[str, Any]:
        """Handle case where multiple patients are found."""
        logger.warning(f"Multiple patients found for name: {name} (count: {len(patient_rows)})")
        
        # Format patient summaries
        patient_summaries = []
        for row in patient_rows:
            patient_summaries.append({
                "patient_id": row[1],
                "name": row[2],
                "age": row[3],
                "diagnosis": row[5],
                "date_admitted": row[10]
            })
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_multiple_results",
            f"Multiple patients found for name: {name}, count: {len(patient_rows)}",
            session_id
        )
        
        return {
            "status": "multiple_found",
            "message": f"Multiple patients found with name '{name}'. Please specify which patient:",
            "patients": patient_summaries,
            "count": len(patient_rows),
            "suggestions": [
                "Use the full name if available",
                "Provide additional identifying information",
                "Contact reception for assistance"
            ],
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_database_error(self, error: sqlite3.Error, name: str, execution_time: float, session_id: str = None) -> Dict[str, Any]:
        """Handle database errors."""
        logger.error(f"Database error during patient lookup for {name}: {error}")
        
        # Log database access failure
        system_logger.log_database_access(
            operation="SELECT",
            table="patients",
            query_params={"name_search": name},
            result_count=0,
            success=False,
            error=str(error)
        )
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_database_error",
            f"Database error during lookup for {name}: {str(error)}",
            session_id
        )
        
        return {
            "status": "error",
            "message": "Database error occurred while searching for patient",
            "error_type": "database_error",
            "error": str(error),
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_general_error(self, error: Exception, name: str, execution_time: float, session_id: str = None) -> Dict[str, Any]:
        """Handle general errors."""
        logger.error(f"General error during patient lookup for {name}: {error}")
        
        # Log system flow
        system_logger.log_system_flow(
            "patient_lookup_general_error",
            f"General error during lookup for {name}: {str(error)}",
            session_id
        )
        
        return {
            "status": "error",
            "message": "An unexpected error occurred while searching for patient",
            "error_type": "general_error",
            "error": str(error),
            "execution_time_ms": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_medications(self, medications_str: str) -> List[str]:
        """Parse medications string into list."""
        if not medications_str:
            return []
        
        # Split by common delimiters
        medications = medications_str.replace(';', ',').split(',')
        return [med.strip() for med in medications if med.strip()]

# Backward compatibility
class PatientLookupTool(PatientDataRetrievalTool):
    """Backward compatibility wrapper."""
    
    def find_by_name(self, name: str):
        """Legacy method for backward compatibility."""
        result = self.lookup_patient_by_name(name)
        
        if result["status"] == "success":
            return {"status": "success", "data": result["data"]}
        else:
            return {"status": "error", "message": result["message"]}
