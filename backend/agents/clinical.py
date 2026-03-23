import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from patient_db import PatientDB
from logger import get_logger
from web_search import WebSearchTool
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv, find_dotenv

_dotenv_path = find_dotenv(usecwd=True)
if not _dotenv_path:
    _dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_dotenv_path, override=True)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

logger = get_logger("clinical_agent")


def _get_gemini_key():
    key = os.getenv('GEMINI_API_KEY')
    if key:
        return key
    try:
        if _dotenv_path and os.path.exists(_dotenv_path):
            with open(_dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('GEMINI_API_KEY'):
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                os.environ['GEMINI_API_KEY'] = val
                                return val
    except Exception:
        pass
    return None


class ClinicalAgent:
    def __init__(self):
        logger.info("Initializing Clinical Agent...")
        self.patient_db = PatientDB()
        self.web_search = WebSearchTool()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_dir = os.path.join(self.base_dir, "data", "faiss_index")
        self.rag_chain = None
        self.retriever = None
        logger.info("Clinical Agent initialized successfully")

    def _load_rag_pipeline(self):
        if self.rag_chain is None:
            logger.info("Loading RAG pipeline...")
            _api_key = _get_gemini_key()
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})
            vectorstore = FAISS.load_local(self.index_dir, embeddings, allow_
            self.retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=_api_key)
            template = """You are an expert clinical nephrologist assistant trained on Comprehensive Clinical Nephrology.
Use the provided medical context to answer clinical questions accurately and professionally.

Medical Context:
{context}

Clinical Question:
{question}

Clinical Response:
"""
            prompt = ChatPromptTemplate.from_template(template)

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            self.rag_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            logger.info("RAG pipeline loaded successfully")
        return self.rag_chain

    def get_medical_guidance(self, query: str):
        logger.info(f"Processing medical query: {query[:80]}")
        try:
            if not _get_gemini_key():
                return {"status": "error", "query": query, "error": "Gemini API key not configured", "timestamp": datetime.now().isoformat()}
            rag_chain = self._load_rag_pipeline()
            response = rag_chain.invoke(query)
            citations = []
            try:
                if self.retriever:
                    docs = self.retriever.invoke(query)
                    for d in docs[:4]:
                        src = d.metadata.get('source') or 'reference_material'
                        page = d.metadata.get('page')
                        citations.append(f"{src}{f' (page {page})' if page is not None else ''}")
            except Exception:
                pass
            guidance = response
            if citations:
                guidance += "\n\nSources:\n- " + "\n- ".join(dict.fromkeys(citations))
            return {"status": "success", "query": query, "guidance": guidance, "timestamp": datetime.now().isoformat(), "source": "Comprehensive Clinical Nephrology"}
        except Exception as e:
            logger.error(f"Error getting medical guidance: {e}")
            return {"status": "error", "query": query, "error": str(e), "timestamp": datetime.now().isoformat()}

    def get_patient_info(self, patient_id: str):
        try:
            patient = self.patient_db.get_patient(patient_id)
            if patient:
                return {"status": "success", "data": {"patient_id": patient[1], "name": patient[2], "age": patient[3], "gender": patient[4], "diagnosis": patient[5], "symptoms": patient[6], "lab_results": patient[7], "treatment_plan": patient[8], "medications": patient[9], "date_admitted": patient[10], "doctor_notes": patient[11]}}
            return {"status": "error", "message": "Patient not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search_patients(self, query: str):
        try:
            patients = self.patient_db.search_patients(query)
            if patients:
                return {"status": "success", "data": [{"patient_id": p[1], "name": p[2], "age": p[3], "diagnosis": p[5]} for p in patients], "count": len(patients)}
            return {"status": "success", "data": [], "count": 0}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def clinical_consultation(self, patient_id: str, clinical_question: str):
        try:
            patient_result = self.get_patient_info(patient_id)
            if patient_result["status"] == "error":
                return patient_result
            pd = patient_result["data"]
            enhanced_query = f"Patient: {pd['name']}, Age: {pd['age']}, Diagnosis: {pd['diagnosis']}, Medications: {pd['medications']}\n\nQuestion: {clinical_question}"
            guidance_result = self.get_medical_guidance(enhanced_query)
            if guidance_result["status"] == "error":
                return guidance_result
            return {"status": "success", "patient_info": pd, "clinical_question": clinical_question, "medical_guidance": guidance_result["guidance"], "timestamp": datetime.now().isoformat(), "consultation_type": "patient_specific"}
        except Exception as e:
            return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}

    def _extract_medical_question(self, question: str):
        if "Patient Context:" in question and "Patient Question:" in question:
            parts = question.split("Patient Question:")
            if len(parts) > 1:
                q = parts[1].strip()
                if "Please provide specific medical guidance" in q:
                    q = q.split("Please provide specific medical guidance")[0].strip()
                return q
        return question.strip()

    def general_medical_query(self, question: str):
        logger.info(f"Processing general medical query: {question[:80]}")
        actual_question = self._extract_medical_question(question)
        self._log_patient_interaction("general_query", actual_question)
        rag_result = self.get_medical_guidance(question)
        rag_response = ""
        rag_available = False
        if rag_result["status"] == "success":
            rag_response = rag_result["guidance"]
            rag_available = len(rag_response.strip()) >= 20
        needs_web_search = self.web_search.is_query_suitable_for_web_search(actual_question)
        if needs_web_search:
            web_result = self.web_search.search_medical_literature(actual_question)
            if rag_available and web_result.get("status") == "success":
                return {"status": "success", "question": question, "medical_guidance": f"REFERENCE MATERIALS:\n{rag_response}\n\nRECENT LITERATURE:\n{self.web_search.format_web_search_response(web_result, actual_question)}", "sources": ["Reference Materials", "Web Search"], "timestamp": datetime.now().isoformat(), "consultation_type": "comprehensive"}
            elif web_result.get("status") == "success":
                return {"status": "success", "question": question, "medical_guidance": self.web_search.format_web_search_response(web_result, actual_question), "sources": ["Web Search"], "timestamp": datetime.now().isoformat(), "consultation_type": "web_fallback"}
            elif rag_available:
                return {"status": "success", "question": question, "medical_guidance": f"REFERENCE MATERIALS:\n{rag_response}", "sources": ["Reference Materials"], "timestamp": datetime.now().isoformat(), "consultation_type": "reference_only"}
            return {"status": "error", "question": question, "medical_guidance": "Unable to provide guidance. Please consult a healthcare professional.", "sources": [], "timestamp": datetime.now().isoformat()}
        else:
            if rag_available:
                return {"status": "success", "question": question, "medical_guidance": f"REFERENCE MATERIALS (Comprehensive Clinical Nephrology):\n{rag_response}", "sources": ["Reference Materials"], "source_details": {"reference_materials": "Comprehensive Clinical Nephrology"}, "timestamp": datetime.now().isoformat(), "consultation_type": "reference_based"}
            return {"status": "error", "question": question, "medical_guidance": "Unable to access medical reference materials. Please consult a healthcare professional.", "sources": [], "timestamp": datetime.now().isoformat()}

    def _log_patient_interaction(self, interaction_type: str, query: str, patient_id: str = None):
        try:
            logger.info(f"Patient interaction: type={interaction_type}, query={query[:100]}")
        except Exception:
            pass

    def search_drug_information(self, drug_name: str):
        try:
            web_result = self.web_search.search_drug_information(drug_name)
            if web_result["status"] == "success":
                info = web_result["information"]
                return {"status": "success", "drug_name": drug_name, "information": f"Drug: {drug_name.title()}\nClass: {info['class']}\nIndication: {info['indication']}\nKidney Considerations: {info['kidney_considerations']}\nInteractions: {info['interactions']}", "source": "web_search", "timestamp": datetime.now().isoformat()}
            return web_result
        except Exception as e:
            return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}