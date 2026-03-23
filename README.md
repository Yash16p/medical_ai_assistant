# 🏥 Medical AI Assistant - Post-Discharge Care System

An intelligent AI-powered healthcare assistant that provides 24/7 post-discharge care support using LangGraph, LangChain, and RAG (Retrieval-Augmented Generation).

## 🎯 Problem Statement

### Healthcare Challenges Addressed:
- **Post-Discharge Care Gap**: Patients have questions after hospital discharge but can't reach doctors 24/7
- **Information Overload**: Medical textbooks contain thousands of pages - doctors can't remember everything
- **Patient Anxiety**: Patients unsure when symptoms require immediate attention vs routine follow-up
- **Medication Confusion**: Patients forget medication instructions and potential side effects

### Our Solution:
A multi-agent AI system that:
-  Identifies patients by name and retrieves discharge information
-  Answers medical questions using a comprehensive medical textbook (RAG)
-  Provides web search for general knowledge and historical queries
-  Maintains conversation context across multiple interactions
-  Offers 24/7 support with intelligent routing

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│                    (Streamlit Frontend)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP POST /chat
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│                    (API Layer - main.py)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   LANGGRAPH WORKFLOW                         │
│              (Stateful Multi-Agent System)                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ROUTER NODE                              │  │
│  │  • Analyzes message                                   │  │
│  │  • Checks patient state                               │  │
│  │  • Decides next action                                │  │
│  └───────┬──────────────┬──────────────┬─────────────────┘  │
│          │              │              │                    │
│          ↓              ↓              ↓                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │   Patient    │ │   Medical    │ │   General    │       │
│  │Identification│ │ Consultation │ │   Response   │       │
│  └──────┬───────┘ └──────┬───────┘ └──────────────┘       │
│         │                │                                  │
│         ↓                ↓                                  │
│  ┌──────────────┐ ┌──────────────────────────────┐        │
│  │  Patient DB  │ │  RAG or Web Search?          │        │
│  │   Lookup     │ │  • Check query keywords      │        │
│  └──────────────┘ │  • Route accordingly         │        │
│                   └──────┬───────────────┬────────┘        │
│                          │               │                 │
│                          ↓               ↓                 │
│                   ┌──────────────┐ ┌──────────────┐       │
│                   │  RAG System  │ │ Web Search   │       │
│                   │  (ChromaDB)  │ │   Tool       │       │
│                   └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

### **Core Technologies**
- **LangGraph** - Multi-agent workflow orchestration with state management
- **LangChain** - LLM integration, RAG pipeline, and document processing
- **Google Gemini 2.5 Flash** - Large Language Model for text generation
- **ChromaDB** - Vector database for semantic search
- **HuggingFace Transformers** - Local embeddings (sentence-transformers/all-MiniLM-L6-v2)

### **Backend**
- **FastAPI** - Modern Python web framework for REST API
- **SQLite** - Patient database
- **Python 3.11** - Core programming language

### **Frontend**
- **Streamlit** - Interactive web UI for chat interface

### **Document Processing**
- **PyPDF** - PDF text extraction
- **LangChain Text Splitters** - Intelligent document chunking

---

##  Data Flow

### Example: Patient with Back Pain

```
1. User Input: "John Clark"
   ↓
2. Router → No patient data → Patient Identification Node
   ↓
3. Patient DB Lookup → Found: NEP0003
   ↓
4. Response: "Hi John Clark! I found your discharge report..."
   ↓
5. User Input: "I have back pain"
   ↓
6. Router → Has patient data + "pain" keyword → Medical Consultation
   ↓
7. Check: needs_web_search? → No (no temporal keywords)
   ↓
8. RAG Pipeline:
   - Convert query to embedding (384 dimensions)
   - Search ChromaDB (10,225 medical chunks)
   - Retrieve top 4 relevant chunks
   - Build prompt with patient context + retrieved context
   - Call Gemini 2.5 Flash
   ↓
9. Response: Medical guidance from textbook with patient-specific context
```

---

## 🧠 Key Components

### **1. LangGraph Workflow (stateful_workflow.py)**
- **State Management**: Maintains patient data, conversation history, and context
- **Router Node**: Intelligent routing based on message content and state
- **Conditional Edges**: Dynamic flow control between agents
- **Memory**: Persistent conversation state using MemorySaver

### **2. RAG System (rag_tool.py)**
- **Document Source**: Comprehensive Clinical Nephrology (1,547 pages)
- **Chunking**: 10,225 chunks (1000 chars each, 200 char overlap)
- **Embeddings**: Local HuggingFace model (no API costs!)
- **Vector Store**: ChromaDB with persistent storage
- **Retrieval**: Top-4 semantic search with patient context enhancement

### **3. Patient Database (patient_db.py)**
- **Storage**: SQLite database
- **Features**: Patient lookup by name/ID, fuzzy search
- **Data**: Demographics, diagnosis, medications, discharge info

### **4. Web Search Tool (web_search.py)**
- **Trigger Keywords**: "when", "history", "latest", "recent", "invented"
- **Use Cases**: Historical queries, current research, general knowledge
- **Fallback**: Simulated results (can integrate real APIs)

### **5. Logging System (logger.py)**
- **Interaction Logs**: All user conversations
- **Agent Handoffs**: Transitions between agents
- **Database Access**: Query tracking
- **System Flow**: Workflow execution traces

---

##  RAG Pipeline Details

### **Indexing Process (One-Time Setup)**

```python
# 1. Load PDF (1,547 pages)
documents = PyPDFLoader("comprehensive-clinical-nephrology.pdf").load()

# 2. Split into chunks (10,225 chunks)
chunks = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
).split_documents(documents)

# 3. Generate embeddings (local, no API costs)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 4. Build ChromaDB index
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="backend/data/chroma_db"
)
```

### **Query Process (Runtime)**

```python
# 1. Enhance query with patient context
enhanced_query = f"""
Patient: {patient_name}
Diagnosis: {diagnosis}
Medications: {medications}
Question: {user_question}
"""

# 2. Semantic search (ChromaDB)
relevant_chunks = retriever.invoke(enhanced_query)  # Top 4 chunks

# 3. Build prompt with context
prompt = f"Context: {chunks}\nQuestion: {enhanced_query}"

# 4. Generate response (Gemini)
response = llm.invoke(prompt)
```

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.11+
- Google Gemini API Key

### **1. Clone Repository**
```bash
git clone <repository-url>
cd medical_ai_assistant
```

### **2. Install Dependencies**
```bash
pip install -r backend/requirements.txt
```

### **3. Configure Environment**
```bash
# Create .env file
cp backend/.env.example backend/.env

# Add your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > backend/.env
```

### **4. Build Vector Database (One-Time)**
```bash
# This indexes the medical textbook (takes ~2 minutes)
python backend/tools/setup_db.py
```

### **5. Start Backend**
```bash
python run_fastapi.py
# API runs on http://localhost:8000
```

### **6. Start Frontend**
```bash
python run_app.py
# UI runs on http://localhost:8501
```

---

## 💡 Usage Examples

### **Example 1: Patient Identification**
```
User: John Clark
AI: Hi John Clark! I found your discharge report from 2025-10-20 
    for Diabetic Nephropathy. How are you feeling today?
```

### **Example 2: Medical Query (RAG)**
```
User: I have back pain
AI: 📚 REFERENCE MATERIALS (Comprehensive Clinical Nephrology):
    
    Back pain in patients with Diabetic Nephropathy can have several causes:
    1. Musculoskeletal: Common due to reduced physical activity
    2. Kidney-related: Though less common, kidney issues can cause flank pain
    3. Medication side effects: Some blood pressure medications may cause muscle aches
    
    Recommendations:
    - Monitor pain intensity and location
    - Ensure proper hydration
    - Gentle stretching exercises
    - If severe or persistent, contact your doctor
    
     IMPORTANT: Consult healthcare professionals for medical advice.
```

### **Example 3: General Knowledge (Web Search)**
```
User: when was cricket invented
AI: 🌐 WEB SEARCH RESULTS:
    
    1. History of Cricket: Origins and Evolution
       Cricket's origins date back to the 16th century in England...
       Source: Sports History Database (2024-01-15)
    
    2. Timeline of Cricket Development
       The modern form was established in the 18th century...
       Source: Cricket Historical Society (2024-02-01)
```

---

##  Project Structure

```
medical_ai_assistant/
├── backend/
│   ├── agents/
│   │   ├── clinical.py          # Clinical agent with RAG
│   │   └── receptionist.py      # Patient identification agent
│   ├── api/
│   │   └── main.py              # FastAPI endpoints
│   ├── data/
│   │   ├── comprehensive-clinical-nephrology.pdf
│   │   ├── chroma_db/           # Vector database
│   │   └── patients.db          # Patient records
│   ├── logs/                    # System logs
│   ├── tools/
│   │   ├── logger.py            # Logging system
│   │   ├── patient_db.py        # Database operations
│   │   ├── patient_lookup.py    # Patient search
│   │   ├── rag_tool.py          # RAG pipeline
│   │   ├── setup_db.py          # Vector DB indexing
│   │   └── web_search.py        # Web search tool
│   ├── workflow/
│   │   └── stateful_workflow.py # LangGraph workflow
│   ├── .env                     # API keys (not in git)
│   └── requirements.txt         # Python dependencies
├── frontend/
│   └── app.py                   # Streamlit UI
├── run_fastapi.py               # Backend launcher
├── run_app.py                   # Frontend launcher
├── .gitignore
└── README.md
```

---

## 🔐 Security & Privacy

### **Current Implementation**
-  API keys stored in `.env` (not committed to Git)
-  Patient data in local SQLite database
-  No external data transmission
-  Comprehensive logging with PII truncation

### **Production Recommendations**
- 🔒 Encrypt patient database
- 🔒 Use HTTPS for API communication
- 🔒 Implement JWT authentication
- 🔒 HIPAA compliance measures
- 🔒 Audit logs for access control
- 🔒 Data retention policies

---

## Performance Metrics

### **Current Performance**
- **Patient Lookup**: ~50ms (SQLite)
- **RAG Query**: ~2-3 seconds
  - Embedding: ~100ms (local)
  - ChromaDB search: ~50ms
  - Gemini generation: ~2 seconds
- **Web Search**: ~200ms (simulated)

### **Scalability**
- **Concurrent Users**: 10-20 (single instance)
- **Database**: Handles 1000s of patients
- **Vector DB**: 10,225 chunks, scalable to millions
- **Memory**: Persistent conversation state per session

---

## 🎯 Key Features

### **1. Multi-Agent System**
- Receptionist Agent: Patient identification
- Clinical Agent: Medical consultation
- Web Search Agent: General knowledge
- Coordinated via LangGraph workflow

### **2. Stateful Conversations**
- Remembers patient across messages
- No need to re-enter information
- Context-aware responses

### **3. Hybrid Information Retrieval**
- RAG for medical queries (textbook)
- Web search for general/historical queries
- Intelligent routing based on keywords

### **4. Local Embeddings**
- No API costs for embeddings
- Fast processing on CPU
- Offline-capable after initial setup

### **5. Comprehensive Logging**
- All interactions logged
- Agent handoff tracking
- Database access monitoring
- System flow traces

---

##  Future Enhancements

### **High Priority**
1. **Hybrid Search** - Combine semantic + keyword search for better accuracy
2. **Medication Interaction Checker** - Safety feature for drug interactions
3. **Symptom Severity Triage** - Classify urgency (ER vs routine)
4. **Real Web Search Integration** - Google/PubMed API integration
5. **Evaluation Metrics** - Track RAG accuracy and user satisfaction

### **Medium Priority**
6. **Streaming Responses** - Real-time response generation
7. **Caching Layer** - Redis for common queries
8. **Multi-modal Support** - Upload lab reports, X-rays
9. **Appointment Scheduling** - Book follow-up appointments
10. **Better Patient Matching** - Fuzzy search with typo tolerance

### **Nice to Have**
11. **Multi-language Support** - Serve non-English patients
12. **Voice Interface** - Speech-to-text and text-to-speech
13. **Analytics Dashboard** - Usage metrics and insights
14. **Conversation Summarization** - Handle long conversations

---



## 📚 API Documentation

### **Endpoints**

#### **POST /chat**
Send a message to the AI assistant

**Request:**
```json
{
  "message": "John Clark",
  "session_id": "user_123"
}
```

**Response:**
```json
{
  "response": "Hi John Clark! I found your discharge report...",
  "session_id": "user_123",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### **GET /health**
Check API health status

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🧪 Testing

### **Run Tests**
```bash
# Test RAG pipeline
python backend/tools/rag_tool.py

# Test patient lookup
python backend/tools/patient_lookup.py

# Test web search
python backend/tools/web_search.py
```

### **View Logs**
```bash
# Interaction logs
cat backend/logs/interactions.log

# Agent handoffs
cat backend/logs/agent_handoffs.log

# System flow
cat backend/logs/system_flow.log
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---


## 🙏 Acknowledgments

- **Comprehensive Clinical Nephrology** - Medical textbook source
- **LangChain** - RAG framework
- **LangGraph** - Workflow orchestration
- **Google Gemini** - LLM provider
- **HuggingFace** - Embedding models
- **ChromaDB** - Vector database

---

##  Support

For questions or issues:
- Open an issue on GitHub
- Check logs in `backend/logs/`
- Review API docs at `http://localhost:8000/docs`

---

**Built with ❤️ using LangGraph, LangChain, and Google Gemini**
