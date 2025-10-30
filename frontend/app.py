import streamlit as st
import requests
import json
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Post-Discharge Care Assistant",
    page_icon="🏥",
    layout="centered"
)

# Main title
st.title("🏥 Post-Discharge Care Assistant")

# Backend API URL
API_BASE_URL = "http://localhost:8000"

def make_api_request(endpoint, data):
    """Make API request with error handling"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.conversation_started = False

# Display chat history using Streamlit's native chat components
for message in st.session_state.messages:
    if message["type"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    elif message["type"] == "agent":
        with st.chat_message("assistant"):
            st.write(message["content"])
    elif message["type"] == "error":
        with st.chat_message("assistant"):
            st.error(message["content"])

# Initial greeting
if not st.session_state.conversation_started:
    greeting = "Hello! I'm your post-discharge care assistant. What's your name?"
    with st.chat_message("assistant"):
        st.write(greeting)
    st.session_state.messages.append({"type": "agent", "content": greeting})
    st.session_state.conversation_started = True

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"type": "user", "content": user_input})
    
    # Make API request
    with st.spinner("Processing your message..."):
        response = make_api_request("/chat", {"message": user_input})
        
        if response and "response" in response:
            # Display agent response
            with st.chat_message("assistant"):
                st.write(response["response"])
            st.session_state.messages.append({"type": "agent", "content": response["response"]})
            
            # Show additional info if available
            if "agent_used" in response:
                st.info(f"🤖 Agent: {response['agent_used']}")
            
            # Enhanced source display
            if "sources" in response and response["sources"]:
                with st.expander("📚 Information Sources", expanded=True):
                    # Show consultation type if available
                    if "consultation_type" in response:
                        consultation_types = {
                            "comprehensive": "🔍 Comprehensive (Reference + Recent Literature)",
                            "reference_based": "📚 Reference Materials Only",
                            "reference_only": "📚 Reference Materials (Web Search Unavailable)",
                            "web_only": "🌐 Web Search Only (Reference Unavailable)",
                            "unknown": "❓ Standard Consultation"
                        }
                        st.write(f"**Consultation Type:** {consultation_types.get(response['consultation_type'], response['consultation_type'])}")
                    
                    # Show sources with detailed information
                    for source in response["sources"]:
                        if source == "Reference Materials":
                            st.success("📚 **Reference Materials**: Comprehensive Clinical Nephrology (peer-reviewed textbook)")
                        elif source == "Web Search":
                            st.info("🌐 **Web Search**: Recent medical literature and research findings")
                        elif source == "Web Search (Fallback)":
                            st.warning("🌐 **Web Search (Fallback)**: Recent medical literature (reference materials unavailable)")
                        else:
                            st.write(f"• {source}")
                    
                    # Show detailed source information if available
                    if "source_details" in response and response["source_details"]:
                        st.write("**Detailed Source Information:**")
                        for source_type, details in response["source_details"].items():
                            st.write(f"• **{source_type.replace('_', ' ').title()}**: {details}")
                    
                    # Add disclaimer
                    st.caption("ℹ️ Information sources are clearly identified to distinguish between established medical knowledge and recent research findings.")
        else:
            error_msg = "Sorry, I'm having trouble connecting to the system. Please try again."
            with st.chat_message("assistant"):
                st.error(error_msg)
            st.session_state.messages.append({"type": "error", "content": error_msg})
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("⚠️ *This system is for educational purposes. Always consult with qualified healthcare professionals for medical advice.*")