from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import openai
from dotenv import load_dotenv
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables (will work with or without .env file)
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
    print("   Please set OPENAI_API_KEY in Render environment variables")
    client = None
else:
    client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)  # Enable CORS for PyRevit requests

class DocumentMComplianceChecker:
    def __init__(self):
        """Initialize the Document M compliance checker with embeddings."""
        self.chunks = []
        self.embeddings = []
        self.diagrams = []
        self.diagram_embeddings = []
        
        # Load Document M chunks
        self._load_chunks()
        
        # Load diagram summaries
        self._load_diagrams()
        
        # Initialize FAISS index for semantic search
        self._build_search_index()
    
    def _load_chunks(self):
        """Load Document M text chunks and embeddings."""
        try:
            # Load chunks
            with open("chunks/docm_chunks.jsonl", "r") as f:
                for line in f:
                    self.chunks.append(json.loads(line))
            
            # Load embeddings
            with open("embeddings/docm_embeddings.jsonl", "r") as f:
                for line in f:
                    embedding_data = json.loads(line)
                    self.embeddings.append(embedding_data["embedding"])
            print(f"✅ Loaded {len(self.chunks)} chunks and {len(self.embeddings)} embeddings")
        except Exception as e:
            print(f"❌ Error loading chunks: {e}")
            # Use simplified mode if embeddings not available
            self.chunks = []
            self.embeddings = []
    
    def _load_diagrams(self):
        """Load diagram summaries and embeddings."""
        try:
            # Load diagram summaries
            with open("chunks/manual_diagrams.jsonl", "r") as f:
                for line in f:
                    self.diagrams.append(json.loads(line))
            
            # Load diagram embeddings
            with open("embeddings/manual_diagrams.jsonl", "r") as f:
                for line in f:
                    embedding_data = json.loads(line)
                    self.diagram_embeddings.append(embedding_data["embedding"])
            print(f"✅ Loaded {len(self.diagrams)} diagrams and {len(self.diagram_embeddings)} diagram embeddings")
        except Exception as e:
            print(f"❌ Error loading diagrams: {e}")
            self.diagrams = []
            self.diagram_embeddings = []
    
    def _build_search_index(self):
        """Build FAISS index for semantic search."""
        try:
            import faiss
            # Combine all embeddings
            all_embeddings = self.embeddings + self.diagram_embeddings
            if all_embeddings:
                all_embeddings = np.array(all_embeddings).astype('float32')
                
                # Create FAISS index
                dimension = all_embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
                self.index.add(all_embeddings)
                print(f"✅ Built FAISS index with {len(all_embeddings)} vectors")
            else:
                self.index = None
                print("⚠️  No embeddings available for search index")
        except Exception as e:
            print(f"❌ Error building search index: {e}")
            self.index = None
    
    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search on Document M content."""
        if not self.index:
            return []
        
        try:
            # Generate query embedding
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Search
            query_vector = np.array([query_embedding]).astype('float32')
            scores, indices = self.index.search(query_vector, top_k)
            
            # Return relevant chunks and diagrams
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.chunks):
                    results.append({
                        "type": "text",
                        "content": self.chunks[idx]["text"],
                        "id": self.chunks[idx]["id"],
                        "score": float(score)
                    })
                else:
                    diagram_idx = idx - len(self.chunks)
                    if diagram_idx < len(self.diagrams):
                        results.append({
                            "type": "diagram",
                            "content": self.diagrams[diagram_idx]["text"],
                            "id": self.diagrams[diagram_idx]["id"],
                            "score": float(score)
                        })
            
            return results
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []
    
    def check_compliance(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check geometry against Document M compliance requirements."""
        
        # Check if OpenAI client is available
        if not client:
            return {
                "compliance_status": "Error",
                "issues": ["OpenAI API key not configured"],
                "suggestions": ["Please set OPENAI_API_KEY environment variable in Render"],
                "full_report": "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in Render environment variables.",
                "geometry_summary": self._prepare_geometry_summary(geometry_data),
                "relevant_regulations": []
            }
        
        # Prepare geometry summary
        geometry_summary = self._prepare_geometry_summary(geometry_data)
        
        # Generate compliance queries
        queries = self._generate_compliance_queries(geometry_data)
        
        # Collect relevant regulations
        relevant_content = []
        for query in queries:
            results = self._semantic_search(query, top_k=3)
            relevant_content.extend(results)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_content = []
        for item in relevant_content:
            content_id = f"{item['type']}_{item['id']}"
            if content_id not in seen:
                seen.add(content_id)
                unique_content.append(item)
        
        # Generate compliance report using GPT-4 Turbo
        report = self._generate_compliance_report(geometry_summary, unique_content)
        
        return report
    
    def _prepare_geometry_summary(self, geometry_data: Dict[str, Any]) -> str:
        """Prepare a summary of the extracted geometry."""
        summary = "Extracted geometry:\n"
        
        if geometry_data.get("doors"):
            summary += f"- {len(geometry_data['doors'])} door(s)\n"
        
        if geometry_data.get("toilets"):
            summary += f"- {len(geometry_data['toilets'])} toilet(s)\n"
        
        if geometry_data.get("grab_rails"):
            summary += f"- {len(geometry_data['grab_rails'])} grab rail(s)\n"
        
        if geometry_data.get("turning_circles"):
            summary += f"- {len(geometry_data['turning_circles'])} turning circle(s)\n"
        
        if geometry_data.get("basins"):
            summary += f"- {len(geometry_data['basins'])} basin(s)\n"
        
        if geometry_data.get("dimensions"):
            dims = geometry_data["dimensions"]
            summary += f"- Room dimensions: {dims.get('width', 0):.1f}mm x {dims.get('length', 0):.1f}mm\n"
            summary += f"- Room area: {dims.get('area', 0):.1f}mm²\n"
        
        if geometry_data.get("section_heights_mm"):
            heights = geometry_data["section_heights_mm"]
            summary += "- Section heights:\n"
            for item, height in heights.items():
                summary += f"  - {item}: {height}mm\n"
        
        return summary
    
    def _generate_compliance_queries(self, geometry_data: Dict[str, Any]) -> List[str]:
        """Generate semantic search queries based on extracted geometry."""
        queries = [
            "wheelchair accessible unisex toilets Document M",
            "grab rail positioning Document M",
            "turning space requirements Document M",
            "door clearances Document M",
            "basin height toilet accommodation Document M",
            "toilet seat height Document M",
            "sanitary accommodation generally Document M",
            "wheelchair accessible toilet compartment Document M"
        ]
        
        # Add specific queries based on what geometry was found
        if geometry_data.get("toilets"):
            queries.append("toilet positioning clearances Document M")
        
        if geometry_data.get("grab_rails"):
            queries.append("grab rail specifications installation Document M")
        
        if geometry_data.get("turning_circles"):
            queries.append("wheelchair turning space requirements Document M")
        
        if geometry_data.get("doors"):
            queries.append("door clearances opening directions Document M")
        
        return queries
    
    def _generate_compliance_report(self, geometry_summary: str, relevant_content: List[Dict]) -> Dict[str, Any]:
        """Generate compliance report using GPT-4 Turbo."""
        
        # Prepare context for GPT
        context = "Relevant Document M regulations and diagrams:\n\n"
        for i, content in enumerate(relevant_content[:10]):  # Limit to top 10
            context += f"{content['type'].upper()} {content['id']}:\n{content['content']}\n\n"
        
        # Create prompt
        prompt = f"""
You are a Document M compliance expert. Evaluate the following geometry against UK Approved Document M (2024) accessibility standards.

IMPORTANT: You must ONLY reference the provided Document M regulations and diagrams. Do not use any external sources or general accessibility knowledge. Base your analysis solely on the specific Document M content provided.

{geometry_summary}

{context}

Please provide a comprehensive compliance report including:
1. Overall compliance status (Compliant/Non-compliant/Partially compliant)
2. Specific issues found with citations to Document M clauses and diagram numbers
3. Suggested fixes for non-compliant elements based on Document M requirements
4. Recommendations for improvement based on Document M guidance

When referencing diagrams, use the format "Diagram X" and explain how the diagram requirements apply to the specific geometry.

Format your response as a structured analysis with clear sections, citing specific Document M clauses and diagrams.
"""
        
        try:
            # Generate report using GPT-4 Turbo
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a Document M compliance expert. You must ONLY reference the provided Document M regulations and diagrams. Do not use any external sources, general accessibility knowledge, or other building regulations. Base your analysis solely on the specific Document M content provided. Always cite specific Document M clauses and diagram numbers when making recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            report_text = response.choices[0].message.content
            
            # Parse the report into structured format
            return {
                "compliance_status": self._extract_compliance_status(report_text),
                "issues": self._extract_issues(report_text),
                "suggestions": self._extract_suggestions(report_text),
                "full_report": report_text,
                "geometry_summary": geometry_summary,
                "relevant_regulations": [{"type": c["type"], "id": c["id"], "content": c["content"][:200] + "..."} for c in relevant_content[:5]]
            }
        except Exception as e:
            return {
                "compliance_status": "Error",
                "issues": [f"Error generating report: {str(e)}"],
                "suggestions": ["Please check your OpenAI API key and try again"],
                "full_report": f"Error: {str(e)}",
                "geometry_summary": geometry_summary,
                "relevant_regulations": []
            }
    
    def _extract_compliance_status(self, report_text: str) -> str:
        """Extract compliance status from report text."""
        if "compliant" in report_text.lower():
            if "non-compliant" in report_text.lower():
                return "Partially compliant"
            elif "not compliant" in report_text.lower():
                return "Non-compliant"
            else:
                return "Compliant"
        return "Unknown"
    
    def _extract_issues(self, report_text: str) -> List[str]:
        """Extract specific issues from report text."""
        issues = []
        lines = report_text.split('\n')
        in_issues_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if we're entering the issues section
            if any(keyword in line.lower() for keyword in ['specific issues found', 'issues found']):
                in_issues_section = True
                continue
                
            # Check if we're leaving the issues section
            if in_issues_section and any(keyword in line.lower() for keyword in ['suggested fixes', 'recommendations', 'conclusion']):
                break
                
            # Extract actual issues (not headers)
            if in_issues_section and line and not line.startswith('#'):
                if any(keyword in line.lower() for keyword in ['issue', 'problem', 'non-compliant', 'violation', 'deficiency']):
                    # Clean up the line
                    clean_line = line.replace('- **', '- ').replace('**', '').strip()
                    if clean_line and len(clean_line) > 10:  # Only add substantial content
                        issues.append(clean_line)
        
        return issues[:5]  # Limit to 5 issues
    
    def _extract_suggestions(self, report_text: str) -> List[str]:
        """Extract suggestions from report text."""
        suggestions = []
        lines = report_text.split('\n')
        in_suggestions_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if we're entering the suggestions section
            if any(keyword in line.lower() for keyword in ['suggested fixes', 'recommendations for improvement']):
                in_suggestions_section = True
                continue
                
            # Check if we're leaving the suggestions section
            if in_suggestions_section and any(keyword in line.lower() for keyword in ['conclusion', 'in conclusion']):
                break
                
            # Extract actual suggestions (not headers)
            if in_suggestions_section and line and not line.startswith('#'):
                if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'fix', 'improve', 'ensure', 'adjust']):
                    # Clean up the line
                    clean_line = line.replace('- **', '- ').replace('**', '').strip()
                    if clean_line and len(clean_line) > 10:  # Only add substantial content
                        suggestions.append(clean_line)
        
        return suggestions[:5]  # Limit to 5 suggestions

# Initialize the compliance checker
print("🚀 Initializing Document M Compliance Checker...")
checker = DocumentMComplianceChecker()
print("✅ Compliance checker initialized!")

@app.route('/')
def home():
    """Home page."""
    return jsonify({
        "message": "Document M Compliance Checker API",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "POST /api/compliance/check": "Check geometry compliance",
            "GET /api/health": "Health check"
        }
    })

@app.route('/api/compliance/check', methods=['POST'])
def check_compliance():
    """API endpoint for compliance checking."""
    try:
        # Get geometry data from request
        geometry_data = request.get_json()
        
        if not geometry_data:
            return jsonify({
                "error": "No geometry data provided",
                "details": "Please provide geometry data in the request body"
            }), 400
        
        # Check compliance
        result = checker.check_compliance(geometry_data)
        
        # Add metadata
        result["api_version"] = "1.0"
        result["timestamp"] = str(datetime.now())
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Document M Compliance Checker API",
        "version": "1.0",
        "openai_configured": client is not None
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000))) 