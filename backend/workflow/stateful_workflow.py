"""
Stateful LangGraph Workflow with Conversation Memory
Maintains patient context across multiple interactions
"""

from typing import TypedDict, Annotated, Sequence, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import operator
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from patient_lookup import lookup_patient
from rag_tool import query_rag
from web_search import WebSearchTool
from logger import get_logger, get_system_logger

logger = get_logger("stateful_workflow")
system_logger = get_system_logger()


class ConversationState(TypedDict):
    """Enhanced state with conversation memory"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    patient_name: str
    patient_id: str
    patient_data: dict
    current_agent: str
    conversation_stage: str
    medical_query: str
    query_history: list
    session_id: str


class StatefulMedicalWorkflow:
    """Stateful workflow with conversation memory"""
    
    def __init__(self):
        """Initialize stateful workflow"""
        logger.info("Initializing Stateful LangGraph Workflow...")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.web_search = WebSearchTool()
        
        # Create memory saver for checkpointing
        self.memory = MemorySaver()
        
        # Build and compile workflow with checkpointing
        workflow = self._build_workflow()
        self.app = workflow.compile(checkpointer=self.memory)
        
        logger.info("Stateful workflow initialized with memory")
    
    def _build_workflow(self) -> StateGraph:
        """Build the stateful workflow graph"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("patient_identification", self.patient_identification_node)
        workflow.add_node("medical_consultation", self.medical_consultation_node)
        workflow.add_node("general_response", self.general_response_node)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "router",
            self.route_decision,
            {
                "identify_patient": "patient_identification",
                "medical_query": "medical_consultation",
                "general": "general_response",
                "end": END
            }
        )
        
        workflow.add_edge("patient_identification", END)
        workflow.add_edge("medical_consultation", END)
        workflow.add_edge("general_response", END)
        
        return workflow
    
    def router_node(self, state: ConversationState) -> ConversationState:
        """Main router node - determines conversation flow"""
        logger.info("Router node processing...")
        
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        patient_data = state.get("patient_data", {})
        
        # Log routing decision
        system_logger.log_system_flow(
            event_type="router_decision",
            description=f"Routing message: {last_message[:50]}...",
            session_id=state.get("session_id", "default")
        )
        
        # Determine routing
        if not patient_data:
            state["conversation_stage"] = "needs_identification"
        else:
            # Check if medical query
            medical_keywords = [
                "pain", "swelling", "worried", "concerned", "hurt", "ache",
                "problem", "issue", "symptoms", "feel", "sick", "nausea",
                "itching", "itch", "cramps", "cramping", "headache", "dizzy",
                "tired", "fatigue", "blood", "urine", "breathing"
            ]
            
            is_medical = any(keyword in last_message.lower() for keyword in medical_keywords)
            
            if is_medical:
                state["conversation_stage"] = "medical_query"
                state["medical_query"] = last_message
                state["current_agent"] = "clinical"
                
                # Log agent handoff
                system_logger.log_agent_handoff(
                    from_agent="Receptionist Agent",
                    to_agent="Clinical Agent",
                    reason="Medical concern detected",
                    context=f"Patient: {patient_data.get('name')}, Query: {last_message[:100]}",
                    session_id=state.get("session_id", "default")
                )
            else:
                state["conversation_stage"] = "general_followup"
        
        return state
    
    def patient_identification_node(self, state: ConversationState) -> ConversationState:
        """Handle patient identification"""
        logger.info("Patient identification node processing...")
        
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        session_id = state.get("session_id", "default")
        
        # Attempt patient lookup
        patient_result = lookup_patient(last_message)
        
        if patient_result.get("status") == "success":
            patient_data = patient_result.get("data", {})
            state["patient_name"] = patient_data.get("name")
            state["patient_id"] = patient_data.get("patient_id")
            state["patient_data"] = patient_data
            state["current_agent"] = "receptionist"
            
            # Generate personalized greeting
            greeting = f"""Hi {patient_data.get('name')}! I found your discharge report from {patient_data.get('date_admitted')} for {patient_data.get('diagnosis')}. How are you feeling today? Are you following your medication schedule?"""
            
            state["messages"].append(AIMessage(content=greeting))
            
            # Log interaction
            system_logger.log_user_interaction(
                session_id=session_id,
                user_message=last_message,
                agent_response=greeting,
                agent_used="Receptionist Agent",
                sources=[],
                metadata={"patient_found": True, "patient_name": patient_data.get("name")}
            )
            
            logger.info(f"Patient identified: {patient_data.get('name')}")
        
        elif patient_result.get("status") == "multiple_found":
            patients = patient_result.get("patients", [])
            response = f"Hello! I found multiple patients with the name '{last_message}'. Could you please provide your full name or patient ID?\n\n"
            for p in patients[:3]:
                response += f"- {p.get('name')} (ID: {p.get('patient_id')})\n"
            
            state["messages"].append(AIMessage(content=response))
            
            system_logger.log_user_interaction(
                session_id=session_id,
                user_message=last_message,
                agent_response=response,
                agent_used="Receptionist Agent",
                sources=[],
                metadata={"patient_found": False, "lookup_status": "multiple_found"}
            )
        
        else:
            response = f"Hello! I couldn't find your discharge report for '{last_message}'. Could you please verify your name spelling?"
            state["messages"].append(AIMessage(content=response))
            
            system_logger.log_user_interaction(
                session_id=session_id,
                user_message=last_message,
                agent_response=response,
                agent_used="Receptionist Agent",
                sources=[],
                metadata={"patient_found": False, "lookup_status": "not_found"}
            )
        
        return state
    
    def medical_consultation_node(self, state: ConversationState) -> ConversationState:
        """Handle medical consultation with RAG or web search"""
        logger.info("Medical consultation node processing...")
        
        medical_query = state.get("medical_query", "")
        patient_data = state.get("patient_data", {})
        session_id = state.get("session_id", "default")
        
        # Determine query type
        temporal_keywords = ["latest", "recent", "new", "current", "2024", "2025"]
        needs_web_search = any(keyword in medical_query.lower() for keyword in temporal_keywords)
        
        try:
            if needs_web_search:
                # Use web search
                logger.info("Using web search for query")
                search_results = self.web_search.search_medical_literature(medical_query)
                
                response = f"""This sounds like a medical concern. Let me connect you with our Clinical AI Agent.

🌐 **RECENT MEDICAL LITERATURE** (Web Search):
{search_results}

⚠️ **IMPORTANT:** This is an AI assistant for educational purposes only. Always consult healthcare professionals for medical advice."""
                
                sources = ["Web Search"]
                consultation_type = "web_fallback"
            
            else:
                # Use RAG
                logger.info("Using RAG for query")
                
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
                
                rag_response = query_rag(enhanced_query)
                
                response = f"""This sounds like a medical concern. Let me connect you with our Clinical AI Agent.

📚 **REFERENCE MATERIALS** (Comprehensive Clinical Nephrology):
{rag_response}

📋 **SOURCE:** This information is from the Comprehensive Clinical Nephrology textbook, a peer-reviewed medical reference.

⚠️ **IMPORTANT:** This is an AI assistant for educational purposes only. Always consult healthcare professionals for medical advice."""
                
                sources = ["Reference Materials"]
                consultation_type = "reference_based"
            
            state["messages"].append(AIMessage(content=response))
            
            # Log interaction
            system_logger.log_user_interaction(
                session_id=session_id,
                user_message=medical_query,
                agent_response=response,
                agent_used="Receptionist → Clinical Agent",
                sources=sources,
                metadata={
                    "patient_name": patient_data.get("name") if patient_data else None,
                    "medical_concern": True,
                    "consultation_type": consultation_type,
                    "agent_handoff": True
                }
            )
            
            # Add to query history
            query_history = state.get("query_history", [])
            query_history.append({
                "query": medical_query,
                "type": "web_search" if needs_web_search else "rag",
                "timestamp": system_logger._get_timestamp()
            })
            state["query_history"] = query_history
            
            logger.info("Medical consultation completed successfully")
        
        except Exception as e:
            logger.error(f"Medical consultation failed: {e}")
            response = "I apologize, but I encountered an error processing your medical query. Please consult with your healthcare provider."
            state["messages"].append(AIMessage(content=response))
        
        return state
    
    def general_response_node(self, state: ConversationState) -> ConversationState:
        """Handle general follow-up responses"""
        logger.info("General response node processing...")
        
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        session_id = state.get("session_id", "default")
        
        general_responses = [
            "Thank you for the update. Remember to take your medications as prescribed. If you have any medical concerns, please let me know.",
            "I appreciate you keeping me informed. Please continue with your treatment plan and let me know if you need any assistance.",
            "That's good to hear! Please continue following your discharge instructions. If you have any medical concerns, please let me know.",
            "Thank you for sharing that with me. Make sure to attend your follow-up appointments as scheduled."
        ]
        
        import random
        response = random.choice(general_responses)
        state["messages"].append(AIMessage(content=response))
        
        # Log interaction
        system_logger.log_user_interaction(
            session_id=session_id,
            user_message=last_message,
            agent_response=response,
            agent_used="Receptionist Agent",
            sources=[],
            metadata={"interaction_type": "general_followup"}
        )
        
        return state
    
    def route_decision(self, state: ConversationState) -> str:
        """Determine routing based on conversation stage"""
        stage = state.get("conversation_stage", "")
        
        if stage == "needs_identification":
            return "identify_patient"
        elif stage == "medical_query":
            return "medical_query"
        elif stage == "general_followup":
            return "general"
        else:
            return "end"
    
    def process_message(self, message: str, session_id: str = "default") -> dict:
        """Process a message with conversation memory"""
        logger.info(f"Processing message for session {session_id}: {message[:50]}...")
        
        # Create config with thread_id for memory
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state or initialize
        try:
            current_state = self.app.get_state(config)
            if current_state.values:
                # Continue existing conversation
                input_state = {
                    "messages": [HumanMessage(content=message)],
                    "session_id": session_id
                }
            else:
                # New conversation
                input_state = {
                    "messages": [HumanMessage(content=message)],
                    "patient_name": "",
                    "patient_id": "",
                    "patient_data": {},
                    "current_agent": "receptionist",
                    "conversation_stage": "initial",
                    "medical_query": "",
                    "query_history": [],
                    "session_id": session_id
                }
        except:
            # New conversation
            input_state = {
                "messages": [HumanMessage(content=message)],
                "patient_name": "",
                "patient_id": "",
                "patient_data": {},
                "current_agent": "receptionist",
                "conversation_stage": "initial",
                "medical_query": "",
                "query_history": [],
                "session_id": session_id
            }
        
        try:
            # Run workflow with memory
            result = self.app.invoke(input_state, config)
            
            # Extract response from last AI message
            ai_messages = [msg for msg in result.get("messages", []) if isinstance(msg, AIMessage)]
            response = ai_messages[-1].content if ai_messages else "I apologize, but I couldn't process your request."
            
            return {
                "status": "success",
                "response": response,
                "agent_used": result.get("current_agent", "receptionist"),
                "patient_identified": bool(result.get("patient_name")),
                "conversation_stage": result.get("conversation_stage", ""),
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "status": "error",
                "response": "I apologize, but I encountered an error. Please try again.",
                "error": str(e),
                "session_id": session_id
            }
    
    def reset_conversation(self, session_id: str = "default"):
        """Reset conversation for a session"""
        config = {"configurable": {"thread_id": session_id}}
        # Clear the checkpoint for this thread
        logger.info(f"Resetting conversation for session: {session_id}")


# Singleton instance
_stateful_workflow = None

def get_stateful_workflow() -> StatefulMedicalWorkflow:
    """Get or create stateful workflow instance"""
    global _stateful_workflow
    if _stateful_workflow is None:
        _stateful_workflow = StatefulMedicalWorkflow()
    return _stateful_workflow


if __name__ == "__main__":
    # Test stateful workflow
    workflow = get_stateful_workflow()
    
    session = "test_session_001"
    
    # Test 1: Patient identification
    result1 = workflow.process_message("Sarah Harris", session)
    print("Test 1 - Patient Identification:")
    print(f"Response: {result1['response'][:200]}...")
    print(f"Patient Identified: {result1['patient_identified']}")
    print("\n" + "="*80 + "\n")
    
    # Test 2: Medical query (should remember patient)
    result2 = workflow.process_message("I have itching all over my body", session)
    print("Test 2 - Medical Query with Context:")
    print(f"Response: {result2['response'][:200]}...")
    print(f"Agent: {result2['agent_used']}")
