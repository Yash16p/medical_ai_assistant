import os
import sys
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from patient_db import PatientDB
from logger import get_logger
from web_search import WebSearchTool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# Load environment variables from .env file
from dotenv import load_dotenv, find_dotenv
# Try to locate a .env file from current working dir upward; fallback to repo root guess
_dotenv_path = find_dotenv(usecwd=True)
if not _dotenv_path:
    _dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(_dotenv_path, override=True)

def _get_openai_key():
    """Return OPENAI_API_KEY from env or .env file, and set it in os.environ."""
    # Built-in fallback (per user request). Avoid printing this value in logs.
    DEFAULT_OPENAI_API_KEY = "REDACTED_OPENAI_KEY"
    key = os.getenv('OPENAI_API_KEY')
    if key:
        return key
    try:
        env_path = _dotenv_path
        if env_path and os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('OPENAI_API_KEY'):
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                os.environ['OPENAI_API_KEY'] = val
                                return val
    except Exception:
        pass
    # Final fallback to built-in token
    if DEFAULT_OPENAI_API_KEY:
        os.environ['OPENAI_API_KEY'] = DEFAULT_OPENAI_API_KEY
        return DEFAULT_OPENAI_API_KEY
    return None

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

logger = get_logger("clinical_agent")

class ClinicalAgent:
    def __init__(self):
        """Initialize the Clinical Agent with database and RAG capabilities."""
        logger.info("Initializing Clinical Agent...")
        
        # Initialize patient database
        self.patient_db = PatientDB()
        
        # Initialize web search tool
        self.web_search = WebSearchTool()
        
        # Initialize RAG system
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_dir = os.path.join(self.base_dir, "data", "faiss_index")
        self.rag_chain = None
        
        logger.info("Clinical Agent initialized successfully")
    
    def _load_rag_pipeline(self):
        """Load FAISS index and build RAG pipeline."""
        if self.rag_chain is None:
            logger.info("Loading RAG pipeline...")
            
            # Explicitly pass API key to avoid environment loading issues
            _api_key = _get_openai_key()
            embeddings = OpenAIEmbeddings(openai_api_key=_api_key)
            vectorstore = FAISS.load_local(self.index_dir, embeddings, allow_dangerous_deserialization=True)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            # Keep retriever for citations later
            self.retriever = retriever

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=_api_key)

            template = """You are an expert clinical nephrologist assistant trained on 'Comprehensive Clinical Nephrology'.
Use the provided medical context to answer clinical questions accurately and professionally.
Always provide evidence-based recommendations and mention when you're uncertain.

Medical Context:
{context}

Clinical Question:
{question}

Clinical Response (provide detailed, evidence-based medical guidance):
"""
            # Create prompt template compatible with LCEL
            prompt = ChatPromptTemplate.from_template(template)

            # Use LCEL to create the chain (LangChain 1.x compatible)
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.runnables import RunnablePassthrough
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            self.rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            logger.info("RAG pipeline loaded successfully")
        
        return self.rag_chain
    
    def get_medical_guidance(self, query: str):
        """Get evidence-based medical guidance using RAG."""
        logger.info(f"Processing medical query: {query}")
        
        try:
            # Check if API key is available
            if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'sk-your-api-key-here':
                logger.warning("OpenAI API key not properly configured")
                return {
                    "status": "error",
                    "query": query,
                    "error": "OpenAI API key not configured",
                    "timestamp": datetime.now().isoformat()
                }
            
            rag_chain = self._load_rag_pipeline()
            response = rag_chain.invoke(query)  # LCEL expects query string directly
            # Collect simple source citations from top retrieved docs
            citations = []
            try:
                if hasattr(self, 'retriever') and self.retriever is not None:
                    docs = self.retriever.get_relevant_documents(query)
                    for d in docs[:4]:
                        src = d.metadata.get('source') or d.metadata.get('file') or 'reference_material'
                        page = d.metadata.get('page')
                        citations.append(f"{src}{f' (page {page})' if page is not None else ''}")
            except Exception:
                pass
            
            result = {
                "status": "success",
                "query": query,
                "guidance": response + (f"\n\nSources:\n- " + "\n- ".join(dict.fromkeys(citations))) if citations else response,
                "timestamp": datetime.now().isoformat(),
                "source": "Comprehensive Clinical Nephrology"
            }
            
            logger.info(f"Medical guidance provided for query: {query[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error getting medical guidance: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_patient_info(self, patient_id: str):
        """Get patient information from database."""
        logger.info(f"Retrieving patient info for ID: {patient_id}")
        
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
                
                logger.info(f"Patient info retrieved for {patient_id}")
                return {"status": "success", "data": patient_data}
            else:
                logger.warning(f"Patient not found: {patient_id}")
                return {"status": "error", "message": "Patient not found"}
                
        except Exception as e:
            logger.error(f"Error retrieving patient info: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_patients(self, query: str):
        """Search patients by name, diagnosis, or symptoms."""
        logger.info(f"Searching patients with query: {query}")
        
        try:
            patients = self.patient_db.search_patients(query)
            
            if patients:
                patient_list = []
                for patient in patients:
                    patient_list.append({
                        "patient_id": patient[1],
                        "name": patient[2],
                        "age": patient[3],
                        "diagnosis": patient[5]
                    })
                
                logger.info(f"Found {len(patients)} patients matching query")
                return {"status": "success", "data": patient_list, "count": len(patients)}
            else:
                logger.info("No patients found matching query")
                return {"status": "success", "data": [], "count": 0}
                
        except Exception as e:
            logger.error(f"Error searching patients: {e}")
            return {"status": "error", "message": str(e)}
    
    def clinical_consultation(self, patient_id: str, clinical_question: str):
        """Provide clinical consultation combining patient data and medical guidance."""
        logger.info(f"Clinical consultation for patient {patient_id}: {clinical_question}")
        
        try:
            # Get patient information
            patient_result = self.get_patient_info(patient_id)
            
            if patient_result["status"] == "error":
                return patient_result
            
            patient_data = patient_result["data"]
            
            # Enhance clinical question with patient context
            enhanced_query = f"""
Patient Context:
- Name: {patient_data['name']}
- Age: {patient_data['age']} years old
- Gender: {patient_data['gender']}
- Current Diagnosis: {patient_data['diagnosis']}
- Symptoms: {patient_data['symptoms']}
- Lab Results: {patient_data['lab_results']}
- Current Medications: {patient_data['medications']}

Clinical Question: {clinical_question}

Please provide specific recommendations considering this patient's current condition.
"""
            
            # Get medical guidance
            guidance_result = self.get_medical_guidance(enhanced_query)
            
            if guidance_result["status"] == "error":
                return guidance_result
            
            # Combine results
            consultation_result = {
                "status": "success",
                "patient_info": patient_data,
                "clinical_question": clinical_question,
                "medical_guidance": guidance_result["guidance"],
                "timestamp": datetime.now().isoformat(),
                "consultation_type": "patient_specific"
            }
            
            logger.info(f"Clinical consultation completed for patient {patient_id}")
            return consultation_result
            
        except Exception as e:
            logger.error(f"Error in clinical consultation: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_medical_question(self, question: str):
        """Extract the actual medical question from patient context if present."""
        # Check if this is a patient context query
        if "Patient Context:" in question and "Patient Question:" in question:
            # Extract just the patient question part
            parts = question.split("Patient Question:")
            if len(parts) > 1:
                # Get the patient question and remove any trailing instructions
                patient_question = parts[1].strip()
                # Remove the "Please provide specific medical guidance..." part
                if "Please provide specific medical guidance" in patient_question:
                    patient_question = patient_question.split("Please provide specific medical guidance")[0].strip()
                return patient_question
        
        # If no patient context, return the original question
        return question.strip()
    
    def general_medical_query(self, question: str):
        """Handle general medical questions with proper RAG-first, web-search fallback logic."""
        logger.info(f"Processing general medical query: {question}")
        
        # Extract the actual medical question from patient context if present
        actual_question = self._extract_medical_question(question)
        logger.info(f"Extracted medical question: {actual_question}")
        
        # Log patient interaction
        self._log_patient_interaction("general_query", actual_question)
        
        # STEP 1: Always try RAG first
        logger.info("Trying RAG (reference materials) first...")
        rag_result = self.get_medical_guidance(question)  # Use full context for RAG
        
        # STEP 2: Accept RAG response by default if present (medical-first policy)
        rag_response = ""
        rag_available = False
        
        if rag_result["status"] == "success":
            rag_response = rag_result["guidance"]
            rag_available = len(rag_response.strip()) >= 20
            logger.info(f"RAG response available: {rag_available}")
        
        # STEP 3: Determine if web search is needed (only for recent/explicitly time-sensitive queries)
        needs_web_search = self.web_search.is_query_suitable_for_web_search(actual_question)
        
        if needs_web_search:
            logger.info("Web search needed - either RAG insufficient or query asks for recent information")
            
            # Try web search with the extracted question only
            web_result = self.web_search.search_medical_literature(actual_question)
            
            if rag_available and web_result.get("status") == "success":
                # CASE 1: Both RAG and web search successful (comprehensive response)
                combined_response = f"""📚 **REFERENCE MATERIALS** (Comprehensive Clinical Nephrology):
{rag_response}

🌐 **RECENT MEDICAL LITERATURE** (Web Search):
This requires recent information. Let me search for you...

{self.web_search.format_web_search_response(web_result, actual_question)}

📋 **SOURCE SUMMARY:**
• Reference Materials: Established medical knowledge from peer-reviewed textbook
• Web Search: Recent research findings and current medical literature"""
                
                return {
                    "status": "success",
                    "question": question,
                    "medical_guidance": combined_response,
                    "sources": ["Reference Materials", "Web Search"],
                    "source_details": {
                        "reference_materials": "Comprehensive Clinical Nephrology (peer-reviewed textbook)",
                        "web_search": "Recent medical literature and research findings"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "consultation_type": "comprehensive"
                }
            
            elif not rag_available and web_result.get("status") == "success":
                # CASE 2: RAG unavailable, web search successful (rare)
                web_fallback_response = f"""This requires recent information. Let me search for you...

🌐 **RECENT MEDICAL LITERATURE** (Web Search):
{self.web_search.format_web_search_response(web_result, actual_question)}

⚠️ **NOTE:** Primary reference materials had insufficient information for this query. Response based on recent medical literature."""
                
                return {
                    "status": "success",
                    "question": question,
                    "medical_guidance": web_fallback_response,
                    "sources": ["Web Search"],
                    "source_details": {
                        "web_search": "Recent medical literature (RAG fallback)"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "consultation_type": "web_fallback"
                }
            
            elif rag_available and web_result.get("status") != "success":
                # CASE 3: RAG sufficient, web search failed (RAG only with note)
                rag_only_response = f"""📚 **REFERENCE MATERIALS** (Comprehensive Clinical Nephrology):
{rag_response}

⚠️ **NOTE:** Recent medical literature search was unavailable. Response based on established medical knowledge from peer-reviewed reference materials."""
                
                return {
                    "status": "success",
                    "question": question,
                    "medical_guidance": rag_only_response,
                    "sources": ["Reference Materials"],
                    "source_details": {
                        "reference_materials": "Comprehensive Clinical Nephrology (peer-reviewed textbook)"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "consultation_type": "reference_only"
                }
            
            else:
                # CASE 4: Both RAG insufficient and web search failed
                return {
                    "status": "error",
                    "question": question,
                    "medical_guidance": "I apologize, but I'm unable to provide sufficient medical guidance for this query. Both reference materials and recent literature searches were insufficient. Please consult with a healthcare professional.",
                    "sources": [],
                    "timestamp": datetime.now().isoformat()
                }
        
        else:
            # CASE 5: RAG used exclusively (default path)
            if rag_result["status"] == "success" and rag_available:
                standard_response = f"""📚 **REFERENCE MATERIALS** (Comprehensive Clinical Nephrology):
{rag_response}

📋 **SOURCE:** This information is from the Comprehensive Clinical Nephrology textbook, a peer-reviewed medical reference."""
                
                return {
                    "status": "success",
                    "question": question,
                    "medical_guidance": standard_response,
                    "sources": ["Reference Materials"],
                    "source_details": {
                        "reference_materials": "Comprehensive Clinical Nephrology (peer-reviewed textbook)"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "consultation_type": "reference_based"
                }
            else:
                # RAG failed completely
                return {
                    "status": "error",
                    "question": question,
                    "medical_guidance": "I apologize, but I'm unable to access medical reference materials at this time. Please consult with a healthcare professional.",
                    "sources": [],
                    "timestamp": datetime.now().isoformat()
                }
    
    def _log_patient_interaction(self, interaction_type: str, query: str, patient_id: str = None):
        """Log patient interactions for audit and analysis."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction_type,
                "query": query[:100] + "..." if len(query) > 100 else query,
                "patient_id": patient_id,
                "agent": "clinical"
            }
            logger.info(f"Patient interaction logged: {log_entry}")
            
            # In production, this would write to a dedicated audit log or database
            # For now, we use the standard logger
            
        except Exception as e:
            logger.error(f"Failed to log patient interaction: {e}")
    
    def search_drug_information(self, drug_name: str):
        """Search for drug information using web search."""
        logger.info(f"Searching drug information for: {drug_name}")
        
        try:
            web_result = self.web_search.search_drug_information(drug_name)
            
            if web_result["status"] == "success":
                drug_info = web_result["information"]
                
                response = f"""**Drug Information for {drug_name.title()}:**

**Drug Class:** {drug_info['class']}
**Indication:** {drug_info['indication']}
**Kidney Considerations:** {drug_info['kidney_considerations']}
**Drug Interactions:** {drug_info['interactions']}

⚠️ **Important**: This information is from web search. Always consult with a pharmacist or physician for complete drug information and interactions."""
                
                return {
                    "status": "success",
                    "drug_name": drug_name,
                    "information": response,
                    "source": "web_search",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return web_result
                
        except Exception as e:
            logger.error(f"Error searching drug information: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }