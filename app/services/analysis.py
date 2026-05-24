"""
Analysis Engine - Phase 2 Refactored Version

This module implements a more structured gap analysis pipeline.
"""

import os
import re
import json
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.models.document import Document
from app.models.finding import Finding, FindingLabel, FindingStatus
import litellm


# =============================================================================
# STAGE 1: Requirement Extraction
# =============================================================================

def extract_requirements_from_text(text: str, doc_prefix: str = "") -> List[Dict[str, Any]]:
    """
    Extract structured requirements from regulation text.
    Improved regex-based extraction with better section handling.
    """
    requirements = []
    
    # Match patterns like "1.2", "2.1.3", "TM-G-2 3.1", etc.
    pattern = re.compile(
        r'((?:[A-Z]-)?\d+(?:\.\d+)*(?:\.\d+)?)\s+([^\n]{50,1200}?)(?=\n(?:[A-Z]-)?\d+(?:\.\d+)*\s+|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in pattern.finditer(text):
        req_id = match.group(1).strip()
        content = match.group(2).strip().replace('\n', ' ')
        
        if len(content) < 50:
            continue
            
        obligation = "shall"
        if re.search(r'\bmay\b', content, re.I):
            obligation = "may"
        elif re.search(r'\bshould\b', content, re.I):
            obligation = "should"
            
        requirements.append({
            "requirement_id": f"{doc_prefix}{req_id}" if doc_prefix else req_id,
            "action": content[:500],
            "obligation_type": obligation,
            "verbatim": content[:800]
        })
    
    return requirements


# =============================================================================
# STAGE 2: SOP Content Loading
# =============================================================================

def load_sop_context(sop_doc_ids: List[str], session: Session, max_chars: int = 12000) -> str:
    """
    Load and concatenate relevant SOP content for analysis.
    """
    context_parts = []
    total_chars = 0
    
    for sop_id in sop_doc_ids:
        sop_doc = session.get(Document, sop_id)
        if not sop_doc or not sop_doc.file_path:
            continue
            
        try:
            import fitz
            doc = fitz.open(sop_doc.file_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            
            header = f"\n\n=== {sop_doc.title} ===\n"
            content = text[:3000]  # Limit per document
            
            if total_chars + len(header) + len(content) > max_chars:
                break
                
            context_parts.append(header + content)
            total_chars += len(header) + len(content)
            
        except Exception as e:
            print(f"Failed to read SOP {sop_id}: {e}")
            continue
    
    return "\n".join(context_parts) if context_parts else "No SOP content available."


# =============================================================================
# STAGE 2.5: Chunking & Retrieval (Phase 2 Enhancement)
# =============================================================================

def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    return [c for c in chunks if len(c) > 100]


def retrieve_relevant_chunks(requirement: Dict[str, Any], sop_context: str, top_k: int = 5) -> List[str]:
    """
    Simple retrieval: find chunks most relevant to the requirement.
    Currently uses keyword overlap. Can be upgraded to embeddings later.
    """
    chunks = chunk_text(sop_context)
    if not chunks:
        return []
    
    req_keywords = set(re.findall(r'\b\w{4,}\b', requirement['action'].lower()))
    
    scored_chunks = []
    for chunk in chunks:
        chunk_keywords = set(re.findall(r'\b\w{4,}\b', chunk.lower()))
        overlap = len(req_keywords & chunk_keywords)
        scored_chunks.append((overlap, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in scored_chunks[:top_k] if score > 0]



# =============================================================================
# STAGE 3: LLM Assessment
# =============================================================================

def assess_requirement(requirement: Dict[str, Any], sop_context: str) -> Dict[str, Any]:
    """
    Assess how well SOPs cover a single regulatory requirement using MiniMax.
    """
    prompt = f"""You are an expert HKMA compliance gap analyst.

REGULATORY REQUIREMENT:
ID: {requirement['requirement_id']}
Text: {requirement['action']}

RELEVANT SOP CONTENT:
{sop_context[:10000]}

TASK:
Determine how well the SOPs cover this requirement.

Return ONLY valid JSON:
{{
  "label": "COVERED" | "PARTIAL" | "MISSING",
  "confidence": 0.0-1.0,
  "rationale": "Explain with reference to specific SOPs",
  "missing_aspects": ["list", "of", "gaps"] or [],
  "evidence": ["key", "quotes", "from", "SOPs"]
}}

Rules:
- "COVERED": SOPs fully address the requirement with clear procedures.
- "PARTIAL": SOPs address some but not all aspects.
- "MISSING": Little or no relevant SOP content.
- Be specific. Reference SOP titles when possible.
"""

    minimax_api_key = os.getenv("MINIMAX_CN_API_KEY") or os.getenv("MINIMAX_API_KEY")
    model_name = "minimax/MiniMax-M2.7-highspeed"
    api_base = "https://api.minimax.chat/v1"

    last_error = None
    
    for attempt in range(2):
        try:
            response = litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1200,
                api_key=minimax_api_key,
                api_base=api_base,
                extra_body={"reasoning_reasoning": True}
            )
            
            raw = response.choices[0].message.content.strip()
            
            # Clean common MiniMax prefixes
            cleaned = raw
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].strip()
            if cleaned.startswith("```"):
                cleaned = cleaned[3:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            
            try:
                result = json.loads(cleaned)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON block
                match = re.search(r'(\{[\s\S]*\})', cleaned)
                if match:
                    result = json.loads(match.group(1))
                    return result
                    
        except Exception as e:
            last_error = str(e)
            print(f"Assessment failed for {requirement['requirement_id']} (attempt {attempt+1}): {e}")
            continue
    
    # Fallback
    return {
        "label": "MISSING",
        "confidence": 0.3,
        "rationale": f"LLM assessment failed: {last_error[:100] if last_error else 'Unknown error'}",
        "missing_aspects": ["Assessment error"],
        "evidence": []
    }


# =============================================================================
# STAGE 4: Finding Creation
# =============================================================================

def create_finding_from_assessment(
    analysis_id: str,
    requirement: Dict[str, Any],
    assessment: Dict[str, Any]
) -> Finding:
    """
    Create a Finding object from LLM assessment result.
    """
    label_map = {
        "COVERED": FindingLabel.COVERED,
        "PARTIAL": FindingLabel.PARTIAL,
        "MISSING": FindingLabel.MISSING
    }
    
    return Finding(
        analysis_id=analysis_id,
        requirement_id=requirement["requirement_id"],
        label=label_map.get(assessment.get("label", "MISSING"), FindingLabel.MISSING),
        confidence=float(assessment.get("confidence", 0.5)),
        rationale=assessment.get("rationale", "No rationale provided."),
        supporting_anchors=[],
        missing_aspects=assessment.get("missing_aspects", []),
        evidence=assessment.get("evidence", []),
        status=FindingStatus.PENDING_OFFICER
    )


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_gap_analysis(
    analysis_id: str,
    regulation_doc_ids: List[str],
    sop_doc_ids: List[str],
    session: Session
) -> List[Finding]:
    """
    Main gap analysis pipeline.
    
    Stages:
    1. Extract requirements from regulations
    2. Load relevant SOP content
    3. Assess each requirement
    4. Create structured Finding objects
    """
    findings = []
    
    # Stage 2: Load SOP context once
    sop_context = load_sop_context(sop_doc_ids, session)
    
    for reg_id in regulation_doc_ids:
        reg_doc = session.get(Document, reg_id)
        if not reg_doc or not reg_doc.file_path:
            continue
            
        # Extract text from regulation
        try:
            import fitz
            doc = fitz.open(reg_doc.file_path)
            full_text = "\n".join([page.get_text() for page in doc])
            doc.close()
        except Exception:
            continue
        
        # Stage 1: Extract requirements
        prefix = f"[{reg_doc.title[:12]}] " if len(regulation_doc_ids) > 1 else ""
        requirements = extract_requirements_from_text(full_text, prefix)
        
        # Stage 3 & 4: Assess and create findings
        for req in requirements[:30]:  # Reasonable limit
            relevant_chunks = retrieve_relevant_chunks(req, sop_context)
            chunk_context = "\n\n".join(relevant_chunks) if relevant_chunks else sop_context[:4000]
            assessment = assess_requirement(req, chunk_context)
            finding = create_finding_from_assessment(analysis_id, req, assessment)
            
            session.add(finding)
            findings.append(finding)
    
    # Fallback if nothing was generated
    if not findings:
        fallback = Finding(
            analysis_id=analysis_id,
            requirement_id="G-1",
            label=FindingLabel.MISSING,
            confidence=0.2,
            rationale="No structured requirements could be extracted or analyzed.",
            supporting_anchors=[],
            missing_aspects=["Pipeline execution issue"],
            status=FindingStatus.PENDING_OFFICER
        )
        session.add(fallback)
        findings.append(fallback)
    
    session.commit()
    return findings
