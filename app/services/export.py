"""
Export Service - Phase 4

Provides export functionality for gap analysis results:
- JSON
- CSV
- PDF (basic)
"""

import json
import csv
import io
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.models.finding import Finding
from app.models.analysis import AnalysisRun


def get_findings_for_export(analysis_id: str, session: Session) -> List[Dict[str, Any]]:
    """Fetch and serialize findings for export."""
    findings = session.exec(
        select(Finding).where(Finding.analysis_id == analysis_id)
    ).all()
    
    result = []
    for f in findings:
        result.append({
            "requirement_id": f.requirement_id,
            "label": f.label.value if hasattr(f.label, "value") else str(f.label),
            "confidence": round(f.confidence, 3) if f.confidence else 0.0,
            "rationale": f.rationale or "",
            "missing_aspects": f.missing_aspects if isinstance(f.missing_aspects, list) else [],
            "evidence": f.evidence if isinstance(f.evidence, list) else [],
            "status": f.status.value if hasattr(f.status, "value") else str(f.status),
            "supporting_anchors": getattr(f, "supporting_anchors", []) or [],
        })
    return result


def export_as_json(analysis_id: str, session: Session) -> str:
    """Export findings as JSON string."""
    findings = get_findings_for_export(analysis_id, session)
    return json.dumps({
        "analysis_id": analysis_id,
        "findings": findings,
        "count": len(findings)
    }, indent=2, ensure_ascii=False)


def export_as_csv(analysis_id: str, session: Session) -> str:
    """Export findings as CSV string."""
    findings = get_findings_for_export(analysis_id, session)
    
    if not findings:
        return "requirement_id,label,confidence,rationale,status
"
    
    output = io.StringIO()
    fieldnames = ["requirement_id", "label", "confidence", "rationale", "status", "missing_aspects", "evidence"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for f in findings:
        writer.writerow({
            "requirement_id": f["requirement_id"],
            "label": f["label"],
            "confidence": f["confidence"],
            "rationale": f["rationale"][:500] if f["rationale"] else "",  # truncate long text
            "status": f["status"],
            "missing_aspects": "; ".join(f["missing_aspects"]) if f["missing_aspects"] else "",
            "evidence": "; ".join(f["evidence"][:2]) if f["evidence"] else "",  # first 2 pieces
        })
    
    return output.getvalue()


def export_as_pdf(analysis_id: str, session: Session) -> bytes:
    """
    Basic PDF export.
    Uses reportlab if available, otherwise returns a simple message.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        # Fallback: return a minimal PDF saying "PDF export requires reportlab"
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj 4 0 obj<</Length 55>>stream\nBT /F1 24 Tf 100 700 Td (PDF Export) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"
    
    findings = get_findings_for_export(analysis_id, session)
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, f"Gap Analysis Report - {analysis_id[:8]}")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Total Findings: {len(findings)}")
    
    y = height - 100
    c.setFont("Helvetica-Bold", 11)
    
    for i, f in enumerate(findings[:30]):  # Limit to first 30 for PDF
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 11)
        
        label = f["label"]
        color = {"COVERED": "green", "PARTIAL": "orange", "MISSING": "red"}.get(label, "black")
        
        c.setFillColorRGB(0, 0, 0)
        c.drawString(50, y, f"{f['requirement_id']} [{label}] - Confidence: {f['confidence']}")
        y -= 14
        
        c.setFont("Helvetica", 9)
        rationale = f["rationale"][:120] + "..." if len(f["rationale"]) > 120 else f["rationale"]
        c.drawString(60, y, rationale)
        y -= 20
        c.setFont("Helvetica-Bold", 11)
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
