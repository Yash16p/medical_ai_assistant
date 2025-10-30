#!/usr/bin/env python3
"""
Log Viewer Tool for monitoring system interactions and flows.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class LogViewer:
    """Tool for viewing and analyzing system logs."""
    
    def __init__(self):
        self.log_dir = "backend/logs"
        self.log_files = {
            "interactions": os.path.join(self.log_dir, "interactions.log"),
            "agent_handoffs": os.path.join(self.log_dir, "agent_handoffs.log"),
            "database_access": os.path.join(self.log_dir, "database_access.log"),
            "information_retrieval": os.path.join(self.log_dir, "information_retrieval.log"),
            "system_flow": os.path.join(self.log_dir, "system_flow.log")
        }
    
    def get_recent_interactions(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent user interactions."""
        return self._read_recent_logs("interactions", hours, limit)
    
    def get_agent_handoffs(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent agent handoffs."""
        return self._read_recent_logs("agent_handoffs", hours, limit)
    
    def get_database_access_logs(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent database access attempts."""
        return self._read_recent_logs("database_access", hours, limit)
    
    def get_information_retrieval_logs(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent information retrieval attempts."""
        return self._read_recent_logs("information_retrieval", hours, limit)
    
    def get_system_flow_logs(self, hours: int = 24, limit: int = 200) -> List[Dict[str, Any]]:
        """Get recent system flow logs."""
        return self._read_recent_logs("system_flow", hours, limit)
    
    def get_session_logs(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all logs for a specific session."""
        session_logs = {
            "interactions": [],
            "agent_handoffs": [],
            "database_access": [],
            "information_retrieval": [],
            "system_flow": []
        }
        
        for log_type, log_file in self.log_files.items():
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line.strip())
                                if log_entry.get("session_id") == session_id:
                                    session_logs[log_type].append(log_entry)
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"Error reading {log_file}: {e}")
        
        return session_logs
    
    def get_system_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system usage statistics."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        stats = {
            "total_interactions": 0,
            "successful_patient_lookups": 0,
            "failed_patient_lookups": 0,
            "agent_handoffs": 0,
            "database_queries": 0,
            "rag_queries": 0,
            "web_searches": 0,
            "unique_sessions": set(),
            "most_common_diagnoses": {},
            "average_response_time": 0
        }
        
        # Analyze interactions
        interactions = self.get_recent_interactions(hours, 1000)
        stats["total_interactions"] = len(interactions)
        
        for interaction in interactions:
            if interaction.get("session_id"):
                stats["unique_sessions"].add(interaction["session_id"])
            
            metadata = interaction.get("metadata", {})
            if metadata.get("patient_found"):
                stats["successful_patient_lookups"] += 1
            elif metadata.get("patient_found") is False:
                stats["failed_patient_lookups"] += 1
        
        # Analyze agent handoffs
        handoffs = self.get_agent_handoffs(hours, 1000)
        stats["agent_handoffs"] = len(handoffs)
        
        # Analyze database access
        db_logs = self.get_database_access_logs(hours, 1000)
        stats["database_queries"] = len(db_logs)
        
        # Analyze information retrieval
        retrieval_logs = self.get_information_retrieval_logs(hours, 1000)
        for log in retrieval_logs:
            if log.get("source_type") == "RAG":
                stats["rag_queries"] += 1
            elif log.get("source_type") == "web_search":
                stats["web_searches"] += 1
        
        stats["unique_sessions"] = len(stats["unique_sessions"])
        
        return stats
    
    def _read_recent_logs(self, log_type: str, hours: int, limit: int) -> List[Dict[str, Any]]:
        """Read recent logs from specified log file."""
        log_file = self.log_files.get(log_type)
        if not log_file or not os.path.exists(log_file):
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_logs = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_time = datetime.fromisoformat(log_entry.get("timestamp", ""))
                        
                        if log_time >= cutoff_time:
                            recent_logs.append(log_entry)
                            
                        if len(recent_logs) >= limit:
                            break
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
        
        return recent_logs[-limit:]  # Return most recent entries
    
    def print_system_summary(self, hours: int = 24):
        """Print a summary of system activity."""
        stats = self.get_system_statistics(hours)
        
        print(f"\n📊 SYSTEM ACTIVITY SUMMARY (Last {hours} hours)")
        print("=" * 60)
        print(f"Total Interactions: {stats['total_interactions']}")
        print(f"Unique Sessions: {stats['unique_sessions']}")
        print(f"Successful Patient Lookups: {stats['successful_patient_lookups']}")
        print(f"Failed Patient Lookups: {stats['failed_patient_lookups']}")
        print(f"Agent Handoffs: {stats['agent_handoffs']}")
        print(f"Database Queries: {stats['database_queries']}")
        print(f"RAG Queries: {stats['rag_queries']}")
        print(f"Web Searches: {stats['web_searches']}")
        
        # Recent interactions
        recent_interactions = self.get_recent_interactions(hours=1, limit=5)
        if recent_interactions:
            print(f"\n🕐 RECENT INTERACTIONS (Last hour):")
            for interaction in recent_interactions[-5:]:
                timestamp = interaction.get("timestamp", "")[:19]
                user_msg = interaction.get("user_message", "")[:50]
                agent = interaction.get("agent_used", "Unknown")
                print(f"  {timestamp} | {agent} | {user_msg}...")
        
        # Recent handoffs
        recent_handoffs = self.get_agent_handoffs(hours=1, limit=3)
        if recent_handoffs:
            print(f"\n🔄 RECENT AGENT HANDOFFS:")
            for handoff in recent_handoffs[-3:]:
                timestamp = handoff.get("timestamp", "")[:19]
                from_agent = handoff.get("from_agent", "")
                to_agent = handoff.get("to_agent", "")
                reason = handoff.get("handoff_reason", "")
                print(f"  {timestamp} | {from_agent} → {to_agent} | {reason}")

def main():
    """Main function for command-line usage."""
    viewer = LogViewer()
    viewer.print_system_summary()

if __name__ == "__main__":
    main()