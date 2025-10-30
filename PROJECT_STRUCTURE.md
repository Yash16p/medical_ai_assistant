# 🏥 Post-Discharge Care Assistant - Project Structure

## 📁 **Core Files**

### **Frontend**
- `frontend/app.py` - Streamlit chat interface

### **Backend API**
- `backend/api/main.py` - FastAPI server with conversation flow
- `backend/main.py` - Alternative FastAPI entry point

### **AI Agents**
- `backend/agents/receptionist.py` - Patient lookup and routing
- `backend/agents/clinical.py` - Medical guidance with RAG

### **Tools & Services**
- `backend/tools/patient_db.py` - SQLite database operations
- `backend/tools/rag_tool.py` - Medical knowledge retrieval
- `backend/tools/web_search.py` - Recent medical literature search
- `backend/tools/patient_lookup.py` - Patient search functionality
- `backend/tools/logger.py` - Logging utilities
- `backend/tools/setup_db.py` - Database initialization

### **Data**
- `backend/data/patients.db` - SQLite database with patient records
- `backend/data/faiss_index/` - Vector database for medical knowledge
- `backend/data/comprehensive-clinical-nephrology.pdf` - Medical textbook

### **Scripts**
- `backend/scripts/generate_patients.py` - Generate sample patient data
- `backend/scripts/view_patients.py` - View database contents

### **Configuration**
- `backend/.env` - Environment variables
- `backend/requirements.txt` - Python dependencies
- `run_app.py` - Start both frontend and backend
- `run_fastapi.py` - Start backend only

## 🚀 **How to Run**

1. **Install dependencies**: `pip install -r backend/requirements.txt`
2. **Start the system**: `python run_app.py`
3. **Access the app**: http://localhost:8501

## 🏗️ **Architecture**

```
Streamlit Frontend (Port 8501)
    ↓
FastAPI Backend (Port 8000)
    ↓
Conversation Flow Manager
    ↓
┌─────────────────┬─────────────────┐
│ Receptionist    │ Clinical Agent  │
│ Agent           │                 │
│ - Patient lookup│ - RAG System    │
│ - Routing       │ - Web Search    │
└─────────────────┴─────────────────┘
    ↓                    ↓
SQLite Database     FAISS Vector DB
(Patient Records)   (Medical Knowledge)
```

## 💬 **Conversation Flow**

1. **Initial**: Receptionist greets and finds patient
2. **Patient Found**: Receptionist asks "How are you feeling?"
3. **Medical Routing**: Routes medical concerns to Clinical Agent
4. **Clinical Response**: Clinical Agent provides medical guidance

## 🎯 **Key Features**

- ✅ Patient discharge report lookup
- ✅ Medical symptom detection and routing
- ✅ RAG-based medical knowledge retrieval
- ✅ Web search for recent medical research
- ✅ Patient-specific medical guidance
- ✅ Source citations for medical advice