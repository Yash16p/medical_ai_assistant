from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

# Load environment variables from .env file
from dotenv import load_dotenv, find_dotenv
_dotenv_path = find_dotenv(usecwd=True)
if not _dotenv_path:
    _dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(_dotenv_path)

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from logger import get_logger, get_system_logger

logger = get_logger("fastapi_backend")
system_logger = get_system_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Medical AI Assistant API",
    description="Post-discharge nephrology care assistant with multi-agent system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class PatientQuery(BaseModel):
    patient_name: str

class MedicalQuery(BaseModel):
    question: str
    patient_context: Optional[str] = None

class ConsultationRequest(BaseModel):
    patient_id: str
    clinical_question: str

class PatientSearchRequest(BaseModel):
    query: str

# Response models
class DischargeReport(BaseModel):
    patient_name: str
    discharge_date: str
    primary_diagnosis: str
    medications: List[str]
    dietary_restrictions: str
    follow_up: str
    warning_signs: str
    discharge_instructions: str

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[Any, Any]] = None
    timestamp: str

# Global variables for agents (will be initialized on startup)
langgraph_workflow = None
receptionist_agent = None
clinical_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents and workflow on startup."""
    global langgraph_workflow, receptionist_agent, clinical_agent
    
    logger.info("Initializing Medical AI Assistant API...")
    
    try:
        # Import and initialize LangGraph workflow
        from langgraph_workflow import MedicalAIWorkflow
        langgraph_workflow = MedicalAIWorkflow()
        
        logger.info("LangGraph workflow initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize LangGraph workflow: {e}")
        # Fallback to individual agents
        try:
            # Import agents with correct class names and paths
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
            
            from agents.receptionist import ReceptionistAgent
            from agents.clinical import ClinicalAgent
            
            receptionist_agent = ReceptionistAgent()
            clinical_agent = ClinicalAgent()
            
            logger.info("Enhanced agents initialized successfully")
        except Exception as fallback_error:
            logger.error(f"Failed to initialize fallback agents: {fallback_error}")
            
            # Create minimal working agents
            try:
                from patient_lookup import PatientLookupTool
                from rag_tool import query_rag
                from web_search import WebSearchTool
                
                class MinimalReceptionist:
                    def __init__(self):
                        self.patient_lookup = PatientLookupTool()
                    
                    def post_discharge_greeting(self, patient_name):
                        # Use database directly instead of JSON file
                        try:
                            from patient_db import PatientDB
                            db = PatientDB()
                            
                            # Search for patient in database
                            patients = db.search_patients(patient_name)
                            
                            if patients and len(patients) > 0:
                                # Get the first matching patient
                                patient = patients[0]
                                
                                # Convert database format to discharge report format
                                discharge_report = {
                                    "patient_name": patient[2],  # name
                                    "discharge_date": patient[10],  # date_admitted
                                    "primary_diagnosis": patient[5],  # diagnosis
                                    "medications": patient[8].split(', ') if patient[8] else [],  # medications
                                    "dietary_restrictions": "Low sodium (2g/day), fluid restriction as advised",
                                    "follow_up": "Nephrology clinic in 1-2 weeks",
                                    "warning_signs": "Swelling, shortness of breath, decreased urine output",
                                    "discharge_instructions": "Take medications as prescribed, monitor symptoms"
                                }
                                
                                greeting = f"Hi {discharge_report['patient_name']}! I found your discharge report from {discharge_report['discharge_date']} for {discharge_report['primary_diagnosis']}. How are you feeling today? Are you following your medication schedule?"
                                return {"status": "success", "greeting": greeting, "discharge_report": discharge_report}
                            
                            return {"status": "not_found", "greeting": f"Hello! I couldn't find your discharge report for '{patient_name}'. Could you please verify your name spelling?"}
                        except Exception as e:
                            return {"status": "error", "greeting": f"Hello! I'm having trouble accessing your records. Please try again later."}
                
                class MinimalClinical:
                    def __init__(self):
                        self.web_search = WebSearchTool()
                    
                    def general_medical_query(self, question):
                        try:
                            # Try RAG first
                            rag_result = query_rag(question)
                            if rag_result and isinstance(rag_result, str) and len(rag_result.strip()) > 0:
                                return {
                                    "status": "success",
                                    "medical_guidance": rag_result,
                                    "sources": ["Medical Textbook"]
                                }
                            
                            # Fallback to web search
                            if self.web_search.is_query_suitable_for_web_search(question):
                                web_result = self.web_search.search_medical_literature(question)
                                if web_result and web_result.get("status") == "success":
                                    formatted_response = self.web_search.format_web_search_response(web_result, question)
                                    return {
                                        "status": "success", 
                                        "medical_guidance": formatted_response,
                                        "sources": ["Web Search"]
                                    }
                            
                            return {"status": "error", "medical_guidance": "I couldn't find relevant medical information."}
                        except Exception as e:
                            return {"status": "error", "medical_guidance": f"Error processing query: {str(e)}"}
                
                receptionist_agent = MinimalReceptionist()
                clinical_agent = MinimalClinical()
                
                logger.info("Minimal agents initialized successfully")
                
            except Exception as minimal_error:
                logger.error(f"Failed to initialize minimal agents: {minimal_error}")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Medical AI Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "patient_greeting": "/api/patient/greeting",
            "discharge_report": "/api/patient/discharge-report",
            "medical_query": "/api/medical/query",
            "consultation": "/api/medical/consultation",
            "patient_search": "/api/patient/search"
        }
    }

@app.post("/api/patient/greeting", response_model=APIResponse)
async def patient_greeting(request: PatientQuery):
    """Initial patient greeting and discharge report retrieval."""
    logger.info(f"Patient greeting request for: {request.patient_name}")
    
    try:
        if langgraph_workflow:
            # Use LangGraph workflow
            result = await langgraph_workflow.process_patient_greeting(request.patient_name)
        else:
            # Fallback to individual agents
            if not receptionist_agent:
                raise HTTPException(status_code=500, detail="Receptionist agent not initialized")
            
            result = receptionist_agent.post_discharge_greeting(request.patient_name)
        
        return APIResponse(
            status=result.get("status", "success"),
            message=result.get("greeting", "Greeting processed"),
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Patient greeting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patient/discharge-report", response_model=APIResponse)
async def get_discharge_report(request: PatientQuery):
    """Retrieve patient discharge report."""
    logger.info(f"Discharge report request for: {request.patient_name}")
    
    try:
        if langgraph_workflow:
            result = await langgraph_workflow.get_discharge_report(request.patient_name)
        else:
            if not receptionist_agent:
                raise HTTPException(status_code=500, detail="Receptionist agent not initialized")
            
            result = receptionist_agent.get_discharge_report(request.patient_name)
        
        return APIResponse(
            status=result.get("status", "success"),
            message=result.get("message", "Discharge report retrieved"),
            data=result.get("data"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Discharge report retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/medical/query", response_model=APIResponse)
async def medical_query(request: MedicalQuery):
    """Process medical questions using Clinical AI Agent."""
    logger.info(f"Medical query: {request.question}")
    
    try:
        if langgraph_workflow:
            result = await langgraph_workflow.process_medical_query(
                request.question, 
                request.patient_context
            )
        else:
            if not clinical_agent:
                raise HTTPException(status_code=500, detail="Clinical agent not initialized")
            
            result = clinical_agent.general_medical_query(request.question)
        
        return APIResponse(
            status=result.get("status", "success"),
            message="Medical guidance provided",
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Medical query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/medical/consultation", response_model=APIResponse)
async def patient_consultation(request: ConsultationRequest):
    """Provide patient-specific medical consultation."""
    logger.info(f"Consultation request for patient {request.patient_id}: {request.clinical_question}")
    
    try:
        if langgraph_workflow:
            result = await langgraph_workflow.process_consultation(
                request.patient_id,
                request.clinical_question
            )
        else:
            if not clinical_agent:
                raise HTTPException(status_code=500, detail="Clinical agent not initialized")
            
            result = clinical_agent.clinical_consultation(
                request.patient_id,
                request.clinical_question
            )
        
        return APIResponse(
            status=result.get("status", "success"),
            message="Clinical consultation completed",
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Patient consultation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patient/search", response_model=APIResponse)
async def search_patients(request: PatientSearchRequest):
    """Search for patients by name, diagnosis, or symptoms."""
    logger.info(f"Patient search: {request.query}")
    
    try:
        if langgraph_workflow:
            result = await langgraph_workflow.search_patients(request.query)
        else:
            if not receptionist_agent:
                raise HTTPException(status_code=500, detail="Receptionist agent not initialized")
            
            result = receptionist_agent.search_patients_by_condition(request.query)
        
        return APIResponse(
            status=result.get("status", "success"),
            message=f"Search completed for: {request.query}",
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Patient search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Simple chat endpoint for Streamlit frontend
class ChatMessage(BaseModel):
    message: str

# Global conversation state (in production, use Redis or database)
conversation_states = {}

@app.post("/chat")
async def chat_endpoint(request: ChatMessage):
    """Main chat endpoint with proper conversation flow."""
    logger.info(f"Chat message: {request.message}")
    
    try:
        if langgraph_workflow:
            # Use LangGraph workflow for complete conversation handling
            result = await langgraph_workflow.process_message(request.message)
            
            return {
                "response": result.get("response", "I'm sorry, I couldn't process that."),
                "agent_used": result.get("agent_used", "Unknown"),
                "sources": result.get("sources", []),
                "status": "success"
            }
        else:
            # Implement proper conversation flow with session management
            session_id = "streamlit_session"  # Single session for Streamlit demo
            
            message = request.message.strip()
            
            # Check if this looks like a patient ID or name (reset or select)
            # Patient ID pattern like NEP0008
            import re
            patient_id_match = re.search(r"\b[A-Z]{3}\d{3,}\b", message)
            words = message.split()
            medical_keywords = [
                "pain", "swelling", "worried", "concerned", "concern", "hurt", "ache",
                "problem", "issue", "symptoms", "feel", "sick", "nausea", "vomit", "vomiting", "fever", "temperature",
                "trouble", "difficulty", "blood", "urine", "breathing",
                "chest", "shortness", "dizzy", "tired", "fatigue", "help",
                "what", "how", "why", "when", "should", "can", "is", "am"
            ]
            
            is_likely_name = (
                len(words) >= 2 and len(words) <= 3 and
                not any(keyword in message.lower() for keyword in medical_keywords) and
                any(word[0].isupper() for word in words)  # At least one capitalized word
            )
            
            # Initialize or reset conversation state
            if session_id not in conversation_states or is_likely_name:
                conversation_states[session_id] = {
                    "stage": "initial",  # initial -> patient_found -> medical_routing
                    "patient_name": None,
                    "patient_data": None
                }
            
            state = conversation_states[session_id]
            
            # Stage 1: Initial greeting and patient lookup
            if state["stage"] == "initial":
                # If message contains a patient ID directly, resolve immediately
                if patient_id_match and receptionist_agent:
                    pid = patient_id_match.group(0)
                    result = receptionist_agent.find_patient_by_id(pid)
                    if result.get("status") == "success":
                        state["stage"] = "patient_found"
                        # Normalize to discharge report shape expected later
                        pdata = result.get("data")
                        state["patient_name"] = pdata.get("name")
                        state["patient_data"] = {
                            "patient_name": pdata.get("name"),
                            "discharge_date": pdata.get("date_admitted"),
                            "primary_diagnosis": pdata.get("diagnosis"),
                            "medications": pdata.get("medications").split(', ') if pdata.get("medications") else []
                        }
                        return {
                            "response": f"Hi {pdata.get('name')}! I found your discharge report for {pdata.get('diagnosis')}. How are you feeling today? Are you following your medication schedule?",
                            "agent_used": "Receptionist Agent",
                            "sources": [],
                            "status": "success"
                        }
                if is_likely_name:
                    # This looks like a patient name - try to find them
                    if receptionist_agent:
                        # Log system flow
                        system_logger.log_system_flow(
                            "api_patient_lookup_start",
                            f"Starting patient lookup for: {message}",
                            session_id
                        )
                        
                        result = receptionist_agent.post_discharge_greeting(message, session_id)
                        
                        if result.get("status") == "success":
                            # Patient found - move to next stage
                            state["stage"] = "patient_found"
                            state["patient_name"] = message
                            state["patient_data"] = result.get("discharge_report")
                            
                            # Log successful patient identification
                            system_logger.log_user_interaction(
                                session_id=session_id,
                                user_message=message,
                                agent_response=result.get("greeting"),
                                agent_used="Receptionist Agent",
                                sources=[],
                                metadata={"patient_found": True, "patient_name": state["patient_data"]["patient_name"]}
                            )
                            
                            return {
                                "response": result.get("greeting"),
                                "agent_used": "Receptionist Agent",
                                "sources": [],
                                "status": "success"
                            }
                        elif result.get("status") == "multiple_found":
                            # Multiple matches: ask for patient ID selection
                            candidates = result.get("patients", [])
                            state["stage"] = "awaiting_patient_id"
                            state["candidates"] = candidates
                            options = "\n".join([f"- {c.get('patient_id')}: {c.get('name')} (age {c.get('age')}, dx {c.get('diagnosis')})" for c in candidates[:6]])
                            prompt = (
                                f"I found multiple patients with that name. Please reply with your patient ID (e.g., NEP0008).\n" 
                                f"Matches:\n{options}"
                            )
                            return {
                                "response": prompt,
                                "agent_used": "Receptionist Agent",
                                "sources": [],
                                "status": "success"
                            }
                        else:
                            # Patient not found - stay in initial stage
                            system_logger.log_user_interaction(
                                session_id=session_id,
                                user_message=message,
                                agent_response=result.get("greeting"),
                                agent_used="Receptionist Agent",
                                sources=[],
                                metadata={"patient_found": False, "lookup_status": result.get("status")}
                            )
                            
                            return {
                                "response": result.get("greeting"),
                                "agent_used": "Receptionist Agent", 
                                "sources": [],
                                "status": "success"
                            }
                    else:
                        return {
                            "response": "I'm sorry, the receptionist system is not available.",
                            "agent_used": "System",
                            "sources": [],
                            "status": "error"
                        }
                else:
                    # This doesn't look like a patient name - ask for their name first
                    if receptionist_agent:
                        greeting_result = receptionist_agent.greet_patient()
                        
                        # Log initial greeting
                        system_logger.log_user_interaction(
                            session_id=session_id,
                            user_message=message,
                            agent_response=greeting_result.get("message"),
                            agent_used="Receptionist Agent",
                            sources=[],
                            metadata={"initial_greeting": True, "user_message_type": "non_name"}
                        )
                        
                        return {
                            "response": greeting_result.get("message"),
                            "agent_used": "Receptionist Agent",
                            "sources": [],
                            "status": "success"
                        }
                    else:
                        return {
                            "response": "Hello! I'm your post-discharge care assistant. What's your name?",
                            "agent_used": "System",
                            "sources": [],
                            "status": "success"
                        }
            
            # Stage 1.5: Awaiting patient ID selection
            elif state["stage"] == "awaiting_patient_id":
                pid_match = re.search(r"\b[A-Z]{3}\d{3,}\b", message)
                if pid_match and receptionist_agent:
                    pid = pid_match.group(0)
                    lookup = receptionist_agent.find_patient_by_id(pid)
                    if lookup.get("status") == "success":
                        pdata = lookup.get("data")
                        state["stage"] = "patient_found"
                        state["patient_name"] = pdata.get("name")
                        state["patient_data"] = {
                            "patient_name": pdata.get("name"),
                            "discharge_date": pdata.get("date_admitted"),
                            "primary_diagnosis": pdata.get("diagnosis"),
                            "medications": pdata.get("medications").split(', ') if pdata.get("medications") else []
                        }
                        return {
                            "response": f"Thank you. I found your record ({pid}). How are you feeling today? Are you following your medication schedule?",
                            "agent_used": "Receptionist Agent",
                            "sources": [],
                            "status": "success"
                        }
                # Reprompt if invalid
                return {
                    "response": "Please reply with your patient ID (e.g., NEP0008) from the list I provided.",
                    "agent_used": "Receptionist Agent",
                    "sources": [],
                    "status": "success"
                }

            # Stage 2: Patient found, handle their response
            elif state["stage"] == "patient_found":
                # Check if this is a medical concern
                medical_keywords = [
                    # Symptom keywords
                    "pain", "swelling", "worried", "concerned", "concern", "hurt", "ache",
                    "problem", "issue", "symptoms", "feel", "sick", "nausea", "vomit", "vomiting", "fever", "temperature",
                    "trouble", "difficulty", "blood", "urine", "breathing",
                    "chest", "shortness", "dizzy", "tired", "fatigue",
                    
                    # Medical condition keywords
                    "disease", "condition", "syndrome", "disorder", "infection",
                    "cancer", "tumor", "diabetes", "hypertension", "kidney",
                    "heart", "cardiac", "arrest", "stroke", "seizure",
                    
                    # Medical question keywords
                    "treatment", "medication", "medicine", "therapy", "surgery",
                    "diagnosis", "test", "examination", "procedure", "operation",
                    
                    # Medical history/research keywords
                    "when did", "when was", "history of", "first case", "discovered",
                    "invented", "developed", "research", "study", "clinical"
                ]
                
                message_lower = message.lower()
                is_medical_concern = any(keyword in message_lower for keyword in medical_keywords)
                
                if is_medical_concern:
                    # Route to Clinical Agent with proper handoff
                    state["stage"] = "medical_routing"
                    
                    # Log agent handoff
                    system_logger.log_agent_handoff(
                        from_agent="Receptionist Agent",
                        to_agent="Clinical Agent",
                        reason="Medical concern detected in patient message",
                        context=f"Patient: {state['patient_data']['patient_name']}, Message: {message[:100]}...",
                        session_id=session_id
                    )
                    
                    # Receptionist routing message
                    routing_message = "This sounds like a medical concern. Let me connect you with our Clinical AI Agent."
                    
                    # Get clinical response
                    if clinical_agent:
                        # Determine if question is patient-specific or general
                        patient_specific_indicators = [
                            "i am", "i'm", "my", "me", "should i", "can i", "what should i do",
                            "am i", "do i need", "is my", "are my", "will i", "how do i"
                        ]
                        
                        general_question_indicators = [
                            "what is", "what are", "how does", "when did", "when was", "where",
                            "who", "why does", "explain", "define", "history of", "first case",
                            "discovery of", "invented", "developed"
                        ]
                        
                        message_lower = message.lower()
                        is_patient_specific = any(indicator in message_lower for indicator in patient_specific_indicators)
                        is_general_question = any(indicator in message_lower for indicator in general_question_indicators)
                        
                        if is_general_question and not is_patient_specific:
                            # General medical question - don't use patient context
                            clinical_result = clinical_agent.general_medical_query(message)
                        else:
                            # Patient-specific question - use patient context
                            enhanced_query = f"""
Patient Context:
- Name: {state['patient_data']['patient_name']}
- Diagnosis: {state['patient_data']['primary_diagnosis']}
- Medications: {', '.join(state['patient_data']['medications'])}
- Discharge Date: {state['patient_data']['discharge_date']}

Patient Question: {message}

Please provide specific medical guidance considering this patient's discharge information.
"""
                            clinical_result = clinical_agent.general_medical_query(enhanced_query)
                        
                        if clinical_result.get("status") == "success":
                            # Combine routing message with clinical response
                            full_response = f"{routing_message}\n\n**Clinical Agent Response:**\n{clinical_result.get('medical_guidance')}"
                            
                            # Log complete interaction
                            system_logger.log_user_interaction(
                                session_id=session_id,
                                user_message=message,
                                agent_response=full_response,
                                agent_used="Receptionist → Clinical Agent",
                                sources=clinical_result.get("sources", []),
                                metadata={
                                    "patient_name": state['patient_data']['patient_name'],
                                    "medical_concern": True,
                                    "consultation_type": clinical_result.get("consultation_type", "unknown"),
                                    "agent_handoff": True
                                }
                            )
                            
                            return {
                                "response": full_response,
                                "agent_used": "Receptionist → Clinical Agent",
                                "sources": clinical_result.get("sources", []),
                                "source_details": clinical_result.get("source_details", {}),
                                "consultation_type": clinical_result.get("consultation_type", "unknown"),
                                "status": "success"
                            }
                        else:
                            # Surface clinical agent error instead of generic message
                            error_msg = clinical_result.get("medical_guidance") or "The clinical agent could not process this query."
                            system_logger.log_user_interaction(
                                session_id=session_id,
                                user_message=message,
                                agent_response=error_msg,
                                agent_used="Clinical Agent (error)",
                                sources=clinical_result.get("sources", []),
                                metadata={
                                    "patient_name": state['patient_data']['patient_name'],
                                    "medical_concern": True,
                                    "consultation_error": True
                                }
                            )
                            return {
                                "response": f"{routing_message}\n\n{error_msg}",
                                "agent_used": "Receptionist → Clinical Agent",
                                "sources": clinical_result.get("sources", []),
                                "status": "error"
                            }
                    
                    return {
                        "response": f"{routing_message}\n\nI'm sorry, the clinical system is not available right now.",
                        "agent_used": "Receptionist Agent",
                        "sources": [],
                        "status": "success"
                    }
                else:
                    # Non-medical response from receptionist
                    general_responses = [
                        "That's good to hear! Please continue following your discharge instructions.",
                        "Thank you for the update. Remember to take your medications as prescribed.",
                        "I'm glad you're doing well. Don't forget your follow-up appointment.",
                        "That sounds positive. Keep monitoring your symptoms as advised."
                    ]
                    
                    import random
                    response = random.choice(general_responses)
                    response += " If you have any medical concerns, please let me know."
                    
                    return {
                        "response": response,
                        "agent_used": "Receptionist Agent",
                        "sources": [],
                        "status": "success"
                    }
            
            # Stage 3: Medical routing - Clinical Agent handles everything
            elif state["stage"] == "medical_routing":
                if clinical_agent:
                    # Determine if question is patient-specific or general
                    patient_specific_indicators = [
                        "i am", "i'm", "my", "me", "should i", "can i", "what should i do",
                        "am i", "do i need", "is my", "are my", "will i", "how do i"
                    ]
                    
                    general_question_indicators = [
                        "what is", "what are", "how does", "when did", "when was", "where",
                        "who", "why does", "explain", "define", "history of", "first case",
                        "discovery of", "invented", "developed"
                    ]
                    
                    message_lower = message.lower()
                    is_patient_specific = any(indicator in message_lower for indicator in patient_specific_indicators)
                    is_general_question = any(indicator in message_lower for indicator in general_question_indicators)
                    
                    if is_general_question and not is_patient_specific:
                        # General medical question - don't use patient context
                        result = clinical_agent.general_medical_query(message)
                    else:
                        # Patient-specific question - use patient context
                        enhanced_query = f"""
Patient Context:
- Name: {state['patient_data']['patient_name']}
- Diagnosis: {state['patient_data']['primary_diagnosis']}
- Medications: {', '.join(state['patient_data']['medications'])}
- Discharge Date: {state['patient_data']['discharge_date']}

Patient Question: {message}

Please provide specific medical guidance considering this patient's discharge information.
"""
                        result = clinical_agent.general_medical_query(enhanced_query)
                    
                    if result.get("status") == "success":
                        return {
                            "response": result.get("medical_guidance"),
                            "agent_used": "Clinical Agent",
                            "sources": result.get("sources", []),
                            "source_details": result.get("source_details", {}),
                            "consultation_type": result.get("consultation_type", "unknown"),
                            "status": "success"
                        }
                
                return {
                    "response": "I'm sorry, I couldn't provide medical guidance at this time.",
                    "agent_used": "Clinical Agent",
                    "sources": [],
                    "source_details": {},
                    "status": "error"
                }
            
            # Fallback
            return {
                "response": "I'm sorry, I didn't understand. Could you please rephrase?",
                "agent_used": "System",
                "sources": [],
                "status": "success"
            }
        
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}")
        return {
            "response": f"I'm sorry, there was an error processing your message: {str(e)}",
            "agent_used": "System",
            "sources": [],
            "status": "error"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "langgraph_workflow": langgraph_workflow is not None,
            "receptionist_agent": receptionist_agent is not None,
            "clinical_agent": clinical_agent is not None
        }
    }

@app.get("/debug/conversation")
async def debug_conversation():
    """Debug endpoint to check conversation states."""
    return {
        "conversation_states": conversation_states,
        "total_sessions": len(conversation_states)
    }

@app.post("/debug/reset")
async def reset_conversation():
    """Reset conversation state for debugging."""
    global conversation_states
    conversation_states = {}
    return {"message": "Conversation state reset", "timestamp": datetime.now().isoformat()}

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "langgraph_workflow": langgraph_workflow is not None,
            "receptionist_agent": receptionist_agent is not None,
            "clinical_agent": clinical_agent is not None
        }
    }

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        if langgraph_workflow:
            stats = await langgraph_workflow.get_system_stats()
        else:
            # Fallback stats
            from patient_db import PatientDB
            db = PatientDB()
            all_patients = db.get_all_patients()
            
            stats = {
                "total_patients": len(all_patients),
                "system_status": "operational",
                "agents_active": {
                    "receptionist": receptionist_agent is not None,
                    "clinical": clinical_agent is not None
                }
            }
        
        return APIResponse(
            status="success",
            message="System statistics retrieved",
            data=stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)