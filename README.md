# Medical AI Assistant

A comprehensive post-discharge nephrology care assistant with multi-agent system architecture. This system provides personalized medical guidance using RAG (Retrieval-Augmented Generation) and web search capabilities.

## 🏥 Features

### Multi-Agent Architecture
- **Receptionist Agent**: Handles patient identification and initial greetings
- **Clinical Agent**: Provides medical guidance with source attribution
- **Intelligent Routing**: Seamless handoff between agents based on conversation context

### Advanced Capabilities
- **Patient Context Management**: Personalized responses based on discharge reports
- **Source Attribution**: Clear distinction between reference materials (📚) and web search results (🌐)
- **Comprehensive Logging**: Audit trail for interactions, agent handoffs, and database access
- **RAG-First Approach**: Prioritizes established medical knowledge over web search
- **Conversation State Management**: Maintains context across interactions

### Medical Knowledge Sources
- Comprehensive Clinical Nephrology textbook
- Real-time medical literature search
- Patient-specific discharge information
- Evidence-based treatment guidelines

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medical_ai_assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OpenAI API key
   ```

4. **Initialize the database**
   ```bash
   python backend/tools/setup_db.py
   python backend/scripts/generate_patients.py
   ```

5. **Start the application**
   ```bash
   python run_app.py
   ```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## 📁 Project Structure

```
medical_ai_assistant/
├── backend/
│   ├── agents/
│   │   ├── clinical.py          # Clinical AI Agent
│   │   └── receptionist.py      # Receptionist Agent
│   ├── api/
│   │   └── main.py             # FastAPI backend
│   ├── data/
│   │   ├── comprehensive-clinical-nephrology.pdf
│   │   └── vector_db/          # Vector database storage
│   ├── tools/
│   │   ├── patient_db.py       # Patient database management
│   │   ├── patient_lookup.py   # Enhanced patient retrieval
│   │   ├── rag_tool.py         # RAG implementation
│   │   ├── web_search.py       # Medical literature search
│   │   ├── logger.py           # Comprehensive logging system
│   │   └── log_viewer.py       # System monitoring
│   ├── scripts/
│   │   ├── generate_patients.py # Sample patient data
│   │   └── view_patients.py     # Database viewer
│   └── requirements.txt
├── frontend/
│   └── app.py                  # Streamlit frontend
├── run_app.py                  # Application launcher
└── README.md
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Database Setup
The system uses SQLite for patient data storage. Initialize with:
```bash
python backend/tools/setup_db.py
python backend/scripts/generate_patients.py
```

## 🎯 Usage Examples

### 1. Patient Identification Flow
```
User: "What is kidney disease?"
System: "Hello! I'm your post-discharge care assistant. What's your name?"

User: "John Smith"
System: "Hi John Smith! I found your discharge report from 2025-09-15 for Chronic Kidney Disease Stage 3..."
```

### 2. Medical Consultation
```
User: "I have swelling in my legs"
System: "This sounds like a medical concern. Let me connect you with our Clinical Agent."
[Provides detailed medical guidance with patient context]
```

### 3. General Medical Questions
```
User: "What causes chronic kidney disease?"
System: [Provides evidence-based information with source attribution]
```

## 🔍 API Endpoints

### Patient Management
- `POST /api/patient/greeting` - Initial patient greeting
- `POST /api/patient/discharge-report` - Retrieve discharge report
- `POST /api/patient/search` - Search patients

### Medical Consultation
- `POST /api/medical/query` - General medical questions
- `POST /api/medical/consultation` - Patient-specific consultation

### Chat Interface
- `POST /chat` - Main chat endpoint with conversation flow

### System Monitoring
- `GET /health` - Health check
- `GET /api/stats` - System statistics
- `GET /debug/conversation` - Conversation state debug

## 📊 Logging and Monitoring

The system includes comprehensive logging:

- **User Interactions**: All user messages and agent responses
- **Agent Handoffs**: Transitions between agents with context
- **Database Access**: Patient data retrieval and modifications
- **Information Retrieval**: RAG queries and web searches
- **System Flow**: Application state changes and routing decisions

View logs using:
```bash
python backend/tools/log_viewer.py
```

## 🧪 Testing

### Test Patient Data
The system includes sample patients:
- John Smith (CKD Stage 3)
- Jane Doe (Acute Kidney Injury)
- Bob Johnson (Diabetic Nephropathy)

### API Testing
```bash
# Test patient greeting
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "John Smith"}'

# Test medical query
curl -X POST "http://localhost:8000/api/medical/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is chronic kidney disease?"}'
```

## 🔒 Security Considerations

- API keys are stored in environment variables only
- Patient data is handled according to healthcare privacy standards
- Comprehensive audit logging for compliance
- Input validation and sanitization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the logs using `python backend/tools/log_viewer.py`
2. Review the API documentation at http://localhost:8000/docs
3. Open an issue on GitHub

## 🔄 Recent Updates

### Enhanced Source Citation System
- Clear distinction between reference materials (📚) and web search results (🌐)
- Detailed source attribution with consultation types
- Comprehensive vs reference-only consultation modes

### Improved Conversation Flow
- Fixed medical keyword detection to prevent bypassing receptionist
- Enhanced patient context isolation between sessions
- Intelligent question classification for appropriate routing

### Comprehensive Logging
- Multi-layered logging system with separate log types
- Patient interaction tracking and agent handoff monitoring
- Database access logging and system analytics

---

**Note**: This system is designed for educational and demonstration purposes. Always consult with qualified healthcare professionals for medical advice.