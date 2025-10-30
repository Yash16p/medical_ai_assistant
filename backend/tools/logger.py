import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

class SystemLogger:
    """Enhanced logging system for comprehensive system flow tracking."""
    
    def __init__(self):
        self.interaction_log_file = os.path.join(LOG_DIR, "interactions.log")
        self.agent_handoff_log_file = os.path.join(LOG_DIR, "agent_handoffs.log")
        self.database_access_log_file = os.path.join(LOG_DIR, "database_access.log")
        self.information_retrieval_log_file = os.path.join(LOG_DIR, "information_retrieval.log")
    
    def log_user_interaction(self, session_id: str, user_message: str, agent_response: str, 
                           agent_used: str, sources: list = None, metadata: Dict[Any, Any] = None):
        """Log complete user interaction with system response."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "interaction_type": "user_interaction",
            "user_message": user_message,
            "agent_response": agent_response[:500] + "..." if len(agent_response) > 500 else agent_response,
            "agent_used": agent_used,
            "sources": sources or [],
            "metadata": metadata or {}
        }
        
        self._write_log(self.interaction_log_file, log_entry)
    
    def log_agent_handoff(self, from_agent: str, to_agent: str, reason: str, 
                         context: str, session_id: str = None):
        """Log agent handoffs and decision processes."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "interaction_type": "agent_handoff",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "handoff_reason": reason,
            "context": context,
            "decision_process": f"Agent {from_agent} determined that {reason}, routing to {to_agent}"
        }
        
        self._write_log(self.agent_handoff_log_file, log_entry)
    
    def log_database_access(self, operation: str, table: str, query_params: Dict[Any, Any], 
                          result_count: int, success: bool, error: str = None):
        """Log all database access attempts."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "interaction_type": "database_access",
            "operation": operation,
            "table": table,
            "query_params": query_params,
            "result_count": result_count,
            "success": success,
            "error": error,
            "execution_time_ms": None  # Could be enhanced with timing
        }
        
        self._write_log(self.database_access_log_file, log_entry)
    
    def log_information_retrieval(self, source_type: str, query: str, success: bool, 
                                result_summary: str, response_length: int, 
                                retrieval_time_ms: float = None):
        """Log information retrieval attempts and results."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "interaction_type": "information_retrieval",
            "source_type": source_type,  # "RAG", "web_search", "database"
            "query": query,
            "success": success,
            "result_summary": result_summary,
            "response_length": response_length,
            "retrieval_time_ms": retrieval_time_ms
        }
        
        self._write_log(self.information_retrieval_log_file, log_entry)
    
    def log_system_flow(self, flow_step: str, details: str, session_id: str = None):
        """Log complete system flow for debugging and analysis."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "interaction_type": "system_flow",
            "flow_step": flow_step,
            "details": details
        }
        
        # Write to main system log
        self._write_log(os.path.join(LOG_DIR, "system_flow.log"), log_entry)
    
    def _write_log(self, log_file: str, log_entry: Dict[Any, Any]):
        """Write log entry to specified file."""
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            # Fallback to standard logging if file write fails
            logging.error(f"Failed to write to log file {log_file}: {e}")

# Global system logger instance
system_logger = SystemLogger()

def get_logger(name="main"):
    """Get standard logger for backward compatibility."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, "system.log"), encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_system_logger():
    """Get enhanced system logger for comprehensive logging."""
    return system_logger