import re
from app.models.requirement import Requirement
from sqlmodel import Session

OBLIGATION_PATTERNS = [
    (re.compile(r'\bmust\b', re.I), 'SHALL'),
    (re.compile(r'\bshall\b', re.I), 'SHALL'),
    (re.compile(r'\bshould\b', re.I), 'SHOULD'),
    (re.compile(r'\bmay\b', re.I), 'MAY'),
]

def extract_requirements_from_text(text: str, document_id: str, session: Session) -> list[Requirement]:
    """Simple regex-based requirement extraction"""
    requirements = []
    
    # Split into sentences/sections
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for i, sentence in enumerate(sentences):
        if len(sentence) < 30:
            continue
            
        for pattern, obligation in OBLIGATION_PATTERNS:
            if pattern.search(sentence):
                req = Requirement(
                    requirement_id=f"REQ-{i+1}",
                    document_id=document_id,
                    obligation_type=obligation,
                    subject="General",
                    action=sentence[:200],
                    verbatim=sentence[:500],
                    source_section=f"Section {i+1}"
                )
                session.add(req)
                requirements.append(req)
                break
    
    session.commit()
    return requirements