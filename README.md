# Medical AI Assistant - Multi-Agent System

A multi-agent medical AI assistant powered by Google Gemini, LangGraph, and LangChain for post-discharge nephrology care.

## Features

- Multi-agent architecture with LangGraph orchestration
- Receptionist Agent for patient identification
- Clinical Agent with RAG (Retrieval-Augmented Generation)
- Stateful conversation management with LangChain
- FAISS vector database for medical knowledge
- FastAPI backend with Streamlit frontend

## Setup

1. **Install dependencies:**
```bash
# Option 1: Automated (Recommended)
python install_dependencies.py

# Option 2: Manual
pip install -r backend/requirements.txt
```

2. **Configure your Gemini API key in `backend/.env`:**
```
GEMINI_API_KEY=your-gemini-api-key-here
```

3. **Generate patient database:**
```bash
python backend/scripts/generate_patients.py
```

4. **Run the application:**
```bash
# Full app (Frontend + Backend)
python run_app.py

# Backend only
python run_fastapi.py
```

## Troubleshooting

If you see errors like `'GenerationConfig' has no attribute 'Modality'`, see [QUICK_INSTALL.md](QUICK_INSTALL.md) for detailed installation instructions.

## Architecture

- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: LLM integration and RAG pipeline
- **Google Gemini**: LLM (gemini-1.5-flash) and embeddings
- **FAISS**: Vector database for medical literature
- **FastAPI**: REST API backend
- **Streamlit**: Chat interface frontend

## API Endpoints

- `POST /chat` - Main chat endpoint
- `POST /api/patient/greeting` - Patient identification
- `POST /api/medical/query` - Medical questions
- `GET /health` - Health check

## Project Structure

```
backend/
├── agents/          # AI agents (receptionist, clinical)
├── api/             # FastAPI backend
├── data/            # Patient database and FAISS index
├── tools/           # RAG, logging, database tools
├── workflow/        # LangGraph workflows
└── scripts/         # Utility scripts

frontend/
└── app.py          # Streamlit chat interface
```
