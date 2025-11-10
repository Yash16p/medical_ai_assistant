"""
LangGraph Workflow for Medical AI Assistant
Multi-agent orchestration with state management
"""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import operator
import os
import sys

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from patient_lookup import lookup_patient, get_discharge_report
from rag_tool import query_rag
from web_search import WebSearchTool
from logger import get_logger

logger = get_logger("langgraph_workflow")

# Define the state schema
class AgentState(TypedDict):
    """State schema for the medical assistant workflow"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    patient_name: str
    patient_id: str
    patient_data: dict
    current_agent: str
    conversation_stage: str
    medical_query: str
    rag_response: str
    web_search_response: str
    final_response: str


class MedicalWorkflow:
    """LangGraph workflow for medical AI assistant"""
    
    def __init__(self):
        """Initialize the workflow with LLM and tools"""
        logger.info("Initializing LangGraph Medical Workflow...")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize tools
        self.web_search = WebSearchTool()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("LangGraph Medical Workflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("receptionist", self.receptionist_node)
        workflow.add_node("patient_lookup", self.patient_lookup_node)
        workflow.add_node("clinical_agent", self.clinical_agent_node)
        workflow.add_node("rag_retrieval", self.rag_retrieval_node)
        workflow.add_node("web_search", self.web_search_node)
        workflow.add_node("response_formatter", self.response_formatter_node)
        
        # Set entry point
        workflow.set_entry_point("receptionist")
        
        # Add edges
        workflow.add_conditional_edges(
            "receptionist",
            self.route_from_receptionist,
            {
                "patient_lookup": "patient_lookup",
                "clinical_agent": "clinical_agent",
                "end": END
            }
        )
        
        workflow.add_edge("patient_lookup", "receptionist")
        
        workflow.add_conditional_edges(
            "clinical_agent",
            self.route_from_clinical,
            {
                "rag_retrieval": "rag_retrieval",
                "web_search": "web_search",
                "response_formatter": "response_formatter"
            }
        )
        
        workflow.add_edge("rag_retrieval", "response_formatter")
        workflow.add_edge("web_search", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        return workflow
    
    def receptionist_node(self, state: AgentState) -> AgentState:
        """Receptionist agent node - handles patient identification"""
        logger.info("Receptionist node processing...")
        
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        
        # Check if patient is already identified
        if state.get("patient_name") and state.get("patient_data"):
            # Patient identified, check if medical query
            medical_keywords = [
                "pain", "swelling", "worried", "concerned", "hurt", "ache",
                "problem", "issue", "symptoms", "feel", "sick", "nausea",
                "itching", "itch", "cramps", "cramping", "headache", "dizzy"
            ]
            
            is_medical = any(keyword in last_message.lower() for keyword in medical_keywords)
            
            if is_medical:
                state["conversation_stage"] = "medical_query"
                state["current_agent"] = "clinical"
                state["medical_query"] = last_message
                
                # Create handoff message
                handoff_msg = AIMessage(
                    content="This sounds like a medical concern. Let me connect you with our Clinical AI Agent."
                )
                state["messages"].append(handoff_msg)
                
                logger.info(f"Medical query detected, routing to clinical agent")
            else:
                # General follow-up
                state["conversation_stage"] = "general_followup"
                response = self._generate_followup_response(state)
                state["messages"].append(AIMessage(content=response))
                state["final_response"] = response
        else:
            # Try to identify patient
            state["conversation_stage"] = "patient_identification"
            state["current_agent"] = "receptionist"
        
        return state
    
    def patient_lookup_node(self, state: AgentState) -> AgentState:
        """Patient lookup node - retrieves patient data"""
        logger.info("Patient lookup node processing...")
        
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        
        # Attempt patient lookup
        patient_result = lookup_patient(last_message)
        
        if patient_result.get("status") == "success":
            patient_data = patient_result.get("data", {})
            state["patient_name"] = patient_data.get("name")
            state["patient_id"] = patient_data.get("patient_id")
            state["patient_data"] = patient_data
            
            # Generate greeting
            greeting = f"""Hi {patient_data.get('name')}! I found your discharge report from {patient_data.get('date_admitted')} for {patient_data.get('diagnosis')}. How are you feeling today? Are you following your medication schedule?"""
            
            state["messages"].append(AIMessage(content=greeting))
            state["final_response"] = greeting
            state["conversation_stage"] = "patient_identified"
            
            logger.info(f"Patient identified: {patient_data.get('name')}")
        
        elif patient_result.get("status") == "multiple_found":
            # Multiple patients found
            patients = patient_result.get("patients", [])
            response = f"Hello! I found multiple patients with the name '{last_message}'. Could you please provide your full name or patient ID?\n\n"
            for p in patients[:3]:
                response += f"- {p.get('name')} (ID: {p.get('patient_id')})\n"
            
            state["messages"].append(AIMessage(content=response))
            state["final_response"] = response
            state["conversation_stage"] = "disambiguation"
            
        else:
            # Patient not found
            response = f"Hello! I couldn't find your discharge report for '{last_message}'. Could you please verify your name spelling?"
            state["messages"].append(AIMessage(content=response))
            state["final_response"] = response
            state["conversation_stage"] = "patient_not_found"
        
        return state
    
    def clinical_agent_node(self, state: AgentState) -> AgentState:
        """Clinical agent node - determines query type"""
        logger.info("Clinical agent node processing...")
        
        medical_query = state.get("medical_query", "")
        
        # Determine if query needs web search or RAG
        temporal_keywords = ["latest", "recent", "new", "current", "2024", "2025"]
        historical_keywords = ["when did", "when was", "history of", "first case", "discovered"]
        
        needs_web_search = (
            any(keyword in medical_query.lower() for keyword in temporal_keywords) or
            any(keyword in medical_query.lower() for keyword in historical_keywords)
        )
        
        if needs_web_search:
            state["conversation_stage"] = "web_search_query"
            logger.info("Query requires web search")
        else:
            state["conversation_stage"] = "rag_query"
            logger.info("Query will use RAG")
        
        state["current_agent"] = "clinical"
        return state
    
    def rag_retrieval_node(self, state: AgentState) -> AgentState:
        """RAG retrieval node - queries medical literature"""
        logger.info("RAG retrieval node processing...")
        
        medical_query = state.get("medical_query", "")
        patient_data = state.get("patient_data", {})
        
        # Build enhanced query with patient context
        if patient_data:
            enhanced_query = f"""
Patient Context:
- Name: {patient_data.get('name')}
- Diagnosis: {patient_data.get('diagnosis')}
- Medications: {patient_data.get('medications')}
- Discharge Date: {patient_data.get('date_admitted')}

Patient Question: {medical_query}

Please provide specific medical guidance considering this patient's discharge information.
"""
        else:
            enhanced_query = medical_query
        
        try:
            # Query RAG system
            rag_response = query_rag(enhanced_query)
            state["rag_response"] = rag_response
            state["conversation_stage"] = "rag_retrieved"
            logger.info("RAG retrieval successful")
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            state["rag_response"] = ""
            state["conversation_stage"] = "rag_failed"
        
        return state
    
    def web_search_node(self, state: AgentState) -> AgentState:
        """Web search node - searches medical literature"""
        logger.info("Web search node processing...")
        
        medical_query = state.get("medical_query", "")
        
        try:
            # Perform web search
            search_results = self.web_search.search_medical_literature(medical_query)
            state["web_search_response"] = search_results
            state["conversation_stage"] = "web_search_completed"
            logger.info("Web search completed")
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            state["web_search_response"] = ""
            state["conversation_stage"] = "web_search_failed"
        
        return state
    
    def response_formatter_node(self, state: AgentState) -> AgentState:
        """Response formatter node - formats final response"""
        logger.info("Response formatter node processing...")
        
        conversation_stage = state.get("conversation_stage", "")
        
        if conversation_stage == "rag_retrieved":
            rag_response = state.get("rag_response", "")
            formatted_response = f"""📚 **REFERENCE MATERIALS** (Comprehensive Clinical Nephrology):
{rag_response}

📋 **SOURCE:** This information is from the Comprehensive Clinical Nephrology textbook, a peer-reviewed medical reference.

⚠️ **IMPORTANT:** This is an AI assistant for educational purposes only. Always consult healthcare professionals for medical advice."""
            
        elif conversation_stage == "web_search_completed":
            web_response = state.get("web_search_response", "")
            formatted_response = f"""🌐 **RECENT MEDICAL LITERATURE** (Web Search):
{web_response}

⚠️ **IMPORTANT:** This is an AI assistant for educational purposes only. Always consult healthcare professionals for medical advice."""
        
        else:
            # Fallback response
            formatted_response = "I apologize, but I'm unable to provide specific medical guidance at this time. Please consult with your healthcare provider."
        
        state["final_response"] = formatted_response
        state["messages"].append(AIMessage(content=formatted_response))
        
        logger.info("Response formatted successfully")
        return state
    
    def route_from_receptionist(self, state: AgentState) -> str:
        """Route from receptionist based on conversation stage"""
        stage = state.get("conversation_stage", "")
        
        if stage == "patient_identification":
            return "patient_lookup"
        elif stage == "medical_query":
            return "clinical_agent"
        else:
            return "end"
    
    def route_from_clinical(self, state: AgentState) -> str:
        """Route from clinical agent based on query type"""
        stage = state.get("conversation_stage", "")
        
        if stage == "rag_query":
            return "rag_retrieval"
        elif stage == "web_search_query":
            return "web_search"
        else:
            return "response_formatter"
    
    def _generate_followup_response(self, state: AgentState) -> str:
        """Generate a follow-up response for general queries"""
        general_responses = [
            "Thank you for the update. Remember to take your medications as prescribed. If you have any medical concerns, please let me know.",
            "I appreciate you keeping me informed. Please continue with your treatment plan and let me know if you need any assistance.",
            "That's good to hear! Please continue following your discharge instructions. If you have any medical concerns, please let me know.",
            "Thank you for sharing that with me. Make sure to attend your follow-up appointments as scheduled."
        ]
        import random
        return random.choice(general_responses)
    
    def process_message(self, message: str, session_id: str = "default") -> dict:
        """Process a message through the workflow"""
        logger.info(f"Processing message: {message[:50]}...")
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "patient_name": "",
            "patient_id": "",
            "patient_data": {},
            "current_agent": "receptionist",
            "conversation_stage": "initial",
            "medical_query": "",
            "rag_response": "",
            "web_search_response": "",
            "final_response": ""
        }
        
        try:
            # Run the workflow
            result = self.app.invoke(initial_state)
            
            return {
                "status": "success",
                "response": result.get("final_response", ""),
                "agent_used": result.get("current_agent", "receptionist"),
                "patient_identified": bool(result.get("patient_name")),
                "conversation_stage": result.get("conversation_stage", "")
            }
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "status": "error",
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "error": str(e)
            }


# Singleton instance
_workflow_instance = None

def get_workflow() -> MedicalWorkflow:
    """Get or create workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = MedicalWorkflow()
    return _workflow_instance


if __name__ == "__main__":
    # Test the workflow
    workflow = get_workflow()
    
    # Test patient identification
    result1 = workflow.process_message("Sarah Harris")
    print("Test 1 - Patient Identification:")
    print(result1)
    print("\n" + "="*80 + "\n")
    
    # Test medical query
    result2 = workflow.process_message("I have itching all over my body")
    print("Test 2 - Medical Query:")
    print(result2)
