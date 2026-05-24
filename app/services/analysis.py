import os
import re
import json
from sqlmodel import Session, select
from app.models.document import Document
from app.models.finding import Finding, FindingLabel, FindingStatus
import litellm
from app.core.config import get_settings

settings = get_settings()

def extract_requirements_from_text(text: str, doc_prefix: str = "") -> list[dict]:
    """Improved requirement extraction."""
    requirements = []
    
    # Better pattern for regulatory sections
    pattern = re.compile(
        r'((?:[A-Z]-)?\d+(?:\.\d+)*(?:\.\d+)?)\s+([^\n]{40,800}?)(?=\n(?:[A-Z]-)?\d+(?:\.\d+)*\s+|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    for match in pattern.finditer(text):
        req_id = match.group(1).strip()
        content = match.group(2).strip().replace('\n', ' ')
        
        if len(content) < 40:
            continue
            
        obligation = "shall"
        if re.search(r'\bmay\b', content, re.I):
            obligation = "may"
        elif re.search(r'\bshould\b', content, re.I):
            obligation = "should"
            
        requirements.append({
            "requirement_id": f"{doc_prefix}{req_id}" if doc_prefix else req_id,
            "action": content[:400],
            "obligation_type": obligation,
            "verbatim": content[:600]
        })
    
    return requirements


def _call_llm_for_assessment(requirement: dict, sop_context: str) -> dict:
    """Call MiniMax M2.7 Highspeed to assess coverage of one requirement against SOPs."""
    prompt = f"""You are an expert HKMA compliance gap analyst.

REGULATORY REQUIREMENT:
ID: {requirement['requirement_id']}
Text: {requirement['action']}

RELEVANT SOP CONTENT (excerpts from internal procedures):
{sop_context[:8000]}

TASK:
Analyze how well the SOPs cover this regulatory requirement.

Respond ONLY with valid JSON in this exact format:
{{
  "label": "COVERED" | "PARTIAL" | "MISSING",
  "confidence": 0.0-1.0,
  "rationale": "2-3 sentence explanation with specific references to SOPs",
  "missing_aspects": ["list", "of", "specific", "gaps"] or []
}}

Rules:
- Use "COVERED" only if SOPs fully address the requirement with clear procedures.
- Use "PARTIAL" if SOPs address some but not all aspects.
- Use "MISSING" if there is little or no relevant SOP content.
- Be specific in the rationale. Mention SOP numbers/titles when possible.
"""

    # MiniMax M2.7 Highspeed - hardcoded configuration
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
                max_tokens=1500,
                api_key=minimax_api_key,
                api_base=api_base,
                extra_body={"reasoning_reasoning": True}
            )
            raw = response.choices[0].message.content.strip()
            
            # Verbose logging for debugging
            print(f"[MiniMax Raw Response for {requirement['requirement_id']}] Length={len(raw)} | Preview: {raw[:180]}...")
            
            # Strip common prefixes (json, ```json, ```)
            cleaned = raw.strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].strip()
            if cleaned.startswith("```"):
                cleaned = cleaned[3:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
            
            # Robust JSON extraction
            result = None
            
            # Try 1: Direct JSON
            try:
                result = json.loads(cleaned)
            except json.JSONDecodeError:
                pass
            
            # Try 2: Extract from markdown code block
            if result is None:
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError:
                        pass
            
            # Try 3: Find first { ... } block
            if result is None:
                json_match = re.search(r'(\{[\s\S]*\})', raw)
                if json_match:
                    candidate = json_match.group(1)
                    candidate = re.sub(r'\n', ' ', candidate)
                    candidate = re.sub(r'\s+', ' ', candidate)
                    try:
                        result = json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
            
            if result is None:
                raise ValueError(f"Could not parse JSON: {raw[:150]}")
            
            return result
            
        except Exception as e:
            last_error = str(e)
            print(f"LLM assessment failed for {requirement['requirement_id']} (attempt {attempt+1}/2): {e}")
            continue
    
    # All attempts failed
    return {
        "label": "MISSING",
        "confidence": 0.3,
        "rationale": f"LLM assessment failed after 3 attempts: {last_error[:120] if last_error else 'Unknown error'}",
        "missing_aspects": ["LLM parsing error"]
    }
def run_gap_analysis(analysis_id: str, regulation_doc_ids: list[str], sop_doc_ids: list[str], session: Session) -> list[Finding]:
    """
    Improved gap analysis using LLM-based semantic matching against actual SOP content.
    """
    findings = []
    
    # Load all SOP content
    sop_context = ""
    for sop_id in sop_doc_ids:
        sop_doc = session.get(Document, sop_id)
        if not sop_doc or not sop_doc.file_path:
            continue
        try:
            import fitz
            doc = fitz.open(sop_doc.file_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            sop_context += f"\n\n=== {sop_doc.title} ===\n{text[:3000]}\n"
        except Exception as e:
            print(f"Failed to read SOP {sop_id}: {e}")
            continue
    
    if not sop_context:
        sop_context = "No SOP documents were successfully loaded for comparison."
    
    for reg_id in regulation_doc_ids:
        reg_doc = session.get(Document, reg_id)
        if not reg_doc or not reg_doc.file_path:
            continue
            
        try:
            import fitz
            doc = fitz.open(reg_doc.file_path)
            full_text = "\n".join([page.get_text() for page in doc])
            doc.close()
        except Exception:
            continue
        
        prefix = f"[{reg_doc.title[:12]}] " if len(regulation_doc_ids) > 1 else ""
        requirements = extract_requirements_from_text(full_text, prefix)
        
        for req in requirements[:25]:  # Reasonable limit
            assessment = _call_llm_for_assessment(req, sop_context)
            
            label_map = {
                "COVERED": FindingLabel.COVERED,
                "PARTIAL": FindingLabel.PARTIAL,
                "MISSING": FindingLabel.MISSING
            }
            
            finding = Finding(
                analysis_id=analysis_id,
                requirement_id=req["requirement_id"],
                label=label_map.get(assessment.get("label", "MISSING"), FindingLabel.MISSING),
                confidence=float(assessment.get("confidence", 0.5)),
                rationale=assessment.get("rationale", "No assessment available."),
                supporting_anchors=[],
                missing_aspects=assessment.get("missing_aspects", []),
                status=FindingStatus.PENDING_OFFICER
            )
            session.add(finding)
            findings.append(finding)
    
    if not findings:
        # Fallback
        finding = Finding(
            analysis_id=analysis_id,
            requirement_id="G-1",
            label=FindingLabel.MISSING,
            confidence=0.3,
            rationale="No structured requirements could be extracted or analyzed.",
            supporting_anchors=[],
            missing_aspects=["Requirement extraction or SOP loading failed"],
            status=FindingStatus.PENDING_OFFICER
        )
        session.add(finding)
        findings.append(finding)
    
    session.commit()
    return findings
