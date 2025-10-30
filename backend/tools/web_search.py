import os
import requests
from datetime import datetime
import json
from logger import get_logger

logger = get_logger("web_search")

class WebSearchTool:
    def __init__(self):
        """Initialize the Web Search Tool."""
        logger.info("Initializing Web Search Tool...")
        
        # For this demo, we'll use a simple search simulation
        # In production, you would integrate with Google Search API, Bing API, etc.
        self.search_enabled = True
        
        logger.info("Web Search Tool initialized successfully")
    
    def search_medical_literature(self, query: str, max_results: int = 3):
        """
        Search for medical literature and recent research.
        For demo purposes, this simulates web search results.
        """
        logger.info(f"Searching medical literature for: {query}")
        
        try:
            # Simulate web search results for medical queries
            # In production, this would call actual search APIs
            simulated_results = self._simulate_medical_search(query)
            
            search_result = {
                "status": "success",
                "query": query,
                "results": simulated_results,
                "source": "web_search",
                "timestamp": datetime.now().isoformat(),
                "disclaimer": "Information from web search - verify with healthcare professionals"
            }
            
            logger.info(f"Web search completed for query: {query}")
            return search_result
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _simulate_medical_search(self, query: str):
        """
        Simulate medical search results based on query keywords.
        In production, replace with actual search API calls.
        """
        query_lower = query.lower()
        
        # Simulated search results based on common medical queries
        if "sglt2" in query_lower or "inhibitor" in query_lower:
            return [
                {
                    "title": "SGLT2 Inhibitors in Chronic Kidney Disease: Recent Clinical Trials",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/example1",
                    "snippet": "Recent studies show SGLT2 inhibitors like empagliflozin and dapagliflozin significantly reduce kidney disease progression in CKD patients, with cardiovascular benefits.",
                    "source": "PubMed",
                    "date": "2024-01-15"
                },
                {
                    "title": "Latest Guidelines on SGLT2 Inhibitors for Nephrology",
                    "url": "https://kidney.org/guidelines/sglt2",
                    "snippet": "Updated 2024 guidelines recommend SGLT2 inhibitors as first-line therapy for diabetic kidney disease with eGFR >20 mL/min/1.73m².",
                    "source": "National Kidney Foundation",
                    "date": "2024-02-01"
                }
            ]
        
        elif "cardiac arrest" in query_lower and ("first" in query_lower or "history" in query_lower or "when" in query_lower):
            return [
                {
                    "title": "History of Cardiac Arrest: First Documented Cases and Medical Understanding",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/cardiac-arrest-history",
                    "snippet": "The first documented cases of cardiac arrest date back to ancient medical texts around 3000 BCE, but modern understanding began with William Harvey's work on circulation in 1628. The first successful resuscitation was documented by Dr. Claude Beck in 1947.",
                    "source": "Journal of Medical History",
                    "date": "2023-11-15"
                },
                {
                    "title": "Evolution of Cardiac Arrest Treatment: From Ancient Times to Modern CPR",
                    "url": "https://cardiology.org/history-cardiac-arrest",
                    "snippet": "Ancient Egyptian and Greek physicians described sudden death, but systematic study began in the 18th century. Modern CPR was developed by Kouwenhoven, Jude, and Knickerbocker in 1960.",
                    "source": "American Heart Association",
                    "date": "2024-01-20"
                },
                {
                    "title": "Timeline of Cardiac Arrest Research and Treatment Milestones",
                    "url": "https://medical-timeline.org/cardiac-arrest",
                    "snippet": "Key milestones: 1628 - Harvey describes circulation, 1775 - First electrical defibrillation attempts, 1947 - First successful cardiac surgery resuscitation, 1960 - Modern CPR developed, 1965 - First portable defibrillator.",
                    "source": "Medical History Database",
                    "date": "2023-12-10"
                }
            ]
        
        elif "hypertension" in query_lower or "blood pressure" in query_lower:
            return [
                {
                    "title": "New Hypertension Guidelines for CKD Patients 2024",
                    "url": "https://hypertension.org/guidelines2024",
                    "snippet": "Updated blood pressure targets for CKD patients: <130/80 mmHg for most patients, with individualized approaches for elderly patients.",
                    "source": "American Heart Association",
                    "date": "2024-03-01"
                },
                {
                    "title": "ACE Inhibitors vs ARBs in Kidney Disease: Meta-Analysis",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/example2",
                    "snippet": "Large meta-analysis shows similar efficacy between ACE inhibitors and ARBs for kidney protection, with ARBs having slightly better tolerability.",
                    "source": "Journal of Nephrology",
                    "date": "2024-01-20"
                }
            ]
        
        elif "dialysis" in query_lower:
            return [
                {
                    "title": "Home Dialysis Options: 2024 Patient Outcomes Study",
                    "url": "https://dialysis.org/home-options-2024",
                    "snippet": "Recent data shows improved quality of life and comparable outcomes with home hemodialysis and peritoneal dialysis compared to in-center treatment.",
                    "source": "American Society of Nephrology",
                    "date": "2024-02-15"
                }
            ]
        
        elif "transplant" in query_lower or "kidney transplant" in query_lower:
            return [
                {
                    "title": "Kidney Transplant Outcomes 2024: National Registry Data",
                    "url": "https://transplant.org/outcomes2024",
                    "snippet": "Five-year graft survival rates continue to improve, now at 87% for deceased donor and 94% for living donor kidney transplants.",
                    "source": "UNOS Transplant Registry",
                    "date": "2024-01-30"
                }
            ]
        
        elif "sleep" in query_lower and ("problem" in query_lower or "insomnia" in query_lower):
            return [
                {
                    "title": "Sleep Disorders in Chronic Kidney Disease: Recent Clinical Insights",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/sleep-ckd-2024",
                    "snippet": "Sleep disturbances affect 60-80% of CKD patients. Common causes include restless leg syndrome, sleep apnea, and uremic toxins. Treatment includes sleep hygiene, addressing underlying causes, and careful medication selection.",
                    "source": "Journal of Sleep Medicine",
                    "date": "2024-01-15"
                },
                {
                    "title": "Managing Sleep Problems in Diabetic Nephropathy Patients",
                    "url": "https://diabetes.org/sleep-nephropathy-2024",
                    "snippet": "Diabetic nephropathy patients often experience sleep disruption due to nocturia, pain, and metabolic changes. Recommendations include glucose control, fluid management, and sleep disorder screening.",
                    "source": "American Diabetes Association",
                    "date": "2024-02-10"
                }
            ]
        
        elif "headache" in query_lower:
            return [
                {
                    "title": "Headaches in Chronic Kidney Disease: Causes and Management",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/headache-ckd-2024",
                    "snippet": "Headaches in CKD patients may result from hypertension, fluid retention, electrolyte imbalances, or medication side effects. Evaluation should include blood pressure monitoring and electrolyte assessment.",
                    "source": "Nephrology Clinical Practice",
                    "date": "2024-01-20"
                },
                {
                    "title": "Hypertensive Headaches in Diabetic Nephropathy: 2024 Guidelines",
                    "url": "https://hypertension.org/diabetic-nephropathy-headache",
                    "snippet": "Headaches in diabetic nephropathy often indicate poor blood pressure control. Target BP <130/80 mmHg. Consider medication adjustment and lifestyle modifications.",
                    "source": "American Heart Association",
                    "date": "2024-03-05"
                }
            ]
        
        elif ("sleep" in query_lower and "headache" in query_lower) or ("sleep problem" in query_lower and "headache" in query_lower):
            return [
                {
                    "title": "Sleep Disturbances and Headaches in CKD: Interconnected Symptoms",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/sleep-headache-ckd-2024",
                    "snippet": "Sleep problems and headaches often co-occur in CKD patients. Poor sleep can worsen hypertension leading to headaches. Management includes sleep hygiene, blood pressure control, and addressing underlying kidney disease.",
                    "source": "Clinical Nephrology Journal",
                    "date": "2024-02-15"
                },
                {
                    "title": "Comprehensive Management of Sleep and Headache in Diabetic Nephropathy",
                    "url": "https://endocrinology.org/sleep-headache-management-2024",
                    "snippet": "Integrated approach recommended: optimize glucose control, manage blood pressure, improve sleep hygiene, and consider sleep study if symptoms persist. Avoid nephrotoxic pain medications.",
                    "source": "American Association of Clinical Endocrinologists",
                    "date": "2024-01-30"
                }
            ]
        
        else:
            # Generic medical search results
            return [
                {
                    "title": f"Recent Research on {query.title()}",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/search",
                    "snippet": f"Current medical literature and research findings related to {query}. Multiple studies available in peer-reviewed journals.",
                    "source": "PubMed Database",
                    "date": "2024-01-01"
                },
                {
                    "title": f"Clinical Guidelines: {query.title()}",
                    "url": "https://guidelines.org/search",
                    "snippet": f"Evidence-based clinical practice guidelines and recommendations for {query} from major medical organizations.",
                    "source": "Medical Guidelines Database",
                    "date": "2024-02-01"
                }
            ]
    
    def search_drug_information(self, drug_name: str):
        """Search for drug information and interactions."""
        logger.info(f"Searching drug information for: {drug_name}")
        
        try:
            # Simulate drug information search
            drug_info = self._simulate_drug_search(drug_name)
            
            return {
                "status": "success",
                "drug_name": drug_name,
                "information": drug_info,
                "source": "web_search_drug_database",
                "timestamp": datetime.now().isoformat(),
                "disclaimer": "Drug information from web search - consult pharmacist or physician"
            }
            
        except Exception as e:
            logger.error(f"Drug search failed: {e}")
            return {
                "status": "error",
                "drug_name": drug_name,
                "error": str(e)
            }
    
    def _simulate_drug_search(self, drug_name: str):
        """Simulate drug information search results."""
        drug_lower = drug_name.lower()
        
        # Common nephrology medications
        drug_database = {
            "lisinopril": {
                "class": "ACE Inhibitor",
                "indication": "Hypertension, heart failure, diabetic nephropathy",
                "kidney_considerations": "Reduce dose if eGFR <30. Monitor potassium and creatinine.",
                "interactions": "NSAIDs, potassium supplements, diuretics"
            },
            "furosemide": {
                "class": "Loop Diuretic",
                "indication": "Edema, heart failure, hypertension",
                "kidney_considerations": "Effective even with reduced kidney function. Monitor electrolytes.",
                "interactions": "Lithium, digoxin, aminoglycosides"
            },
            "metformin": {
                "class": "Biguanide",
                "indication": "Type 2 diabetes",
                "kidney_considerations": "Contraindicated if eGFR <30. Use caution if eGFR 30-45.",
                "interactions": "Contrast agents, alcohol"
            }
        }
        
        # Find matching drug
        for drug, info in drug_database.items():
            if drug in drug_lower:
                return info
        
        # Generic response for unknown drugs
        return {
            "class": "Information not available in local database",
            "indication": f"Please consult drug reference for {drug_name}",
            "kidney_considerations": "Check dosing adjustments for kidney function",
            "interactions": "Verify drug interactions with clinical pharmacist"
        }
    
    def is_query_suitable_for_web_search(self, query: str):
        """
        Determine if a query should use web search vs local knowledge base.
        """
        web_search_keywords = [
            # Time-related keywords
            "latest", "recent", "new", "current", "updated", "when", "last time",
            "when was", "when did", "how recent", "most recent", "recently",
            
            # Research-related keywords  
            "research", "study", "trial", "conducted", "published", "findings",
            "breakthrough", "discovery", "investigation", "clinical trial",
            
            # Historical/attribution keywords
            "history", "who", "who first", "first recorded", "first case", "origin",
            "discovered", "invented", "developed", "earliest", "timeline", "recorded",
            
            # Date-related keywords
            "2024", "2023", "2022", "this year", "last year", 
            
            # Regulatory and guideline keywords
            "guidelines", "recommendation", "approval", "fda", "updated guidelines",
            "new guidelines", "revised", "amended"
        ]
        
        query_lower = query.lower()
        
        # Check if query contains keywords that suggest need for recent information
        for keyword in web_search_keywords:
            if keyword in query_lower:
                logger.info(f"Query suitable for web search due to keyword: {keyword}")
                return True
        
        # Check for specific patterns that indicate temporal queries
        temporal_patterns = [
            "when was the last",
            "when did the last",
            "what is the latest",
            "what are the latest", 
            "how recent is",
            "most recent research",
            "latest research",
            "recent studies",
            "current research",
            # Historical phrasing
            "who has the first",
            "who first",
            "first recorded",
            "history of",
            "earliest recorded",
            "who discovered",
            "who invented",
            "who developed"
        ]
        
        for pattern in temporal_patterns:
            if pattern in query_lower:
                logger.info(f"Query suitable for web search due to temporal pattern: {pattern}")
                return True
        
        return False
    
    def format_web_search_response(self, search_results: dict, original_query: str):
        """Format web search results for clinical agent response."""
        if search_results["status"] != "success":
            return f"I encountered an error while searching for recent information about '{original_query}'. Please consult current medical literature or your healthcare provider."
        
        response = f"Based on recent web search results for '{original_query}':\n\n"
        
        for i, result in enumerate(search_results["results"], 1):
            response += f"{i}. **{result['title']}**\n"
            response += f"   {result['snippet']}\n"
            response += f"   Source: {result['source']} ({result.get('date', 'Date not available')})\n\n"
        
        response += "⚠️ **Important**: This information comes from web search results. Please verify with current medical literature and consult healthcare professionals for clinical decisions.\n"
        
        return response

def main():
    """Test the Web Search Tool."""
    print("🔍 TESTING WEB SEARCH TOOL")
    print("="*40)
    
    search_tool = WebSearchTool()
    
    # Test medical literature search
    print("\n1. Testing medical literature search...")
    result = search_tool.search_medical_literature("SGLT2 inhibitors kidney disease")
    if result["status"] == "success":
        print(f"✅ Found {len(result['results'])} results")
        for i, res in enumerate(result['results'], 1):
            print(f"   {i}. {res['title']}")
    
    # Test drug information search
    print("\n2. Testing drug information search...")
    drug_result = search_tool.search_drug_information("lisinopril")
    if drug_result["status"] == "success":
        info = drug_result["information"]
        print(f"✅ Drug info for lisinopril:")
        print(f"   Class: {info['class']}")
        print(f"   Kidney considerations: {info['kidney_considerations']}")
    
    # Test query suitability
    print("\n3. Testing query suitability...")
    queries = [
        "What are the latest SGLT2 inhibitor trials?",
        "What is chronic kidney disease?"
    ]
    
    for query in queries:
        suitable = search_tool.is_query_suitable_for_web_search(query)
        print(f"   '{query}' -> Web search: {'Yes' if suitable else 'No'}")
    
    print("\n✅ Web Search Tool testing completed!")

if __name__ == "__main__":
    main()