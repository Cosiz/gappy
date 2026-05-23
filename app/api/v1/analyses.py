from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import List, Any
from app.core.database import get_session
from app.services.analysis import run_gap_analysis
from app.models.analysis import AnalysisRun
from app.models.finding import Finding
from app.models.document import Document

router = APIRouter(prefix="/analyses", tags=["analyses"])

templates = Jinja2Templates(directory="app/templates")


def _safe(val: Any) -> Any:
    """Convert potentially unhashable types to safe primitives for Jinja."""
    if isinstance(val, (dict, list)):
        return val
    if hasattr(val, "value"):  # Enum
        return val.value
    return val


@router.get("/report", response_class=HTMLResponse)
async def view_report(request: Request, session: Session = Depends(get_session)):
    """View Reports page - safe rendering."""
    latest_run = session.exec(
        select(AnalysisRun).order_by(AnalysisRun.created_at.desc())
    ).first()

    if not latest_run:
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Gap Analysis Report - Project Gappy</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
<div class="max-w-5xl mx-auto px-8 py-12">
    <div class="flex items-center justify-between mb-10">
        <div class="flex items-center gap-x-3">
            <div class="w-8 h-8 bg-black rounded-full flex items-center justify-center">
                <span class="text-white text-sm font-semibold">G</span>
            </div>
            <span class="text-2xl font-semibold tracking-tighter">Project Gappy</span>
        </div>
        <div class="flex items-center gap-x-4 text-sm">
            <div class="text-slate-500">Darren Tan</div>
            <div class="px-3 py-1 bg-slate-100 rounded-full text-xs font-medium">Compliance Officer</div>
        </div>
    </div>

    <div class="flex items-end justify-between mb-8">
        <div>
            <div class="text-3xl font-semibold tracking-tighter">Gap Analysis Report</div>
            <div class="text-slate-500 mt-1">0 findings found</div>
        </div>
    </div>

    <div class="minimal-card rounded-3xl p-16 text-center mt-8 border border-slate-200">
        <div class="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-6">
            <span class="text-3xl">📋</span>
        </div>
        <div class="text-2xl font-semibold tracking-tighter mb-3">No gap analysis reports yet</div>
        <div class="text-slate-500 max-w-md mx-auto mb-8">
            Upload your regulatory documents and SOPs, then run a gap analysis to generate compliance findings.
        </div>
        <div class="flex justify-center gap-4">
            <a href="/documents" class="px-6 py-3 rounded-2xl border border-slate-300 text-sm font-medium hover:bg-slate-50">Document Library</a>
            <a href="/run-analysis" class="px-6 py-3 rounded-2xl bg-black text-white text-sm font-medium">Run New Analysis →</a>
        </div>
    </div>
</div>
</body>
</html>
"""
        return HTMLResponse(content=html)

    # Convert findings to plain dicts
    raw_findings = session.exec(
        select(Finding).where(Finding.analysis_id == latest_run.id)
    ).all()

    findings = []
    for f in raw_findings:
        findings.append({
            "id": str(f.id),
            "requirement_id": f.requirement_id,
            "label": _safe(f.label),
            "confidence": f.confidence,
            "rationale": f.rationale or "",
            "missing_aspects": f.missing_aspects if isinstance(f.missing_aspects, list) else [],
            "supporting_sop_anchors": f.supporting_anchors if isinstance(f.supporting_anchors, list) else [],
            "status": _safe(f.status),
        })

    # Convert analysis run to plain dict (avoid passing SQLModel with JSON fields)
    analysis = {
        "id": str(latest_run.id),
        "name": latest_run.name,
        "created_at": latest_run.created_at,
    }

    documents = []
    
    # Load all Regulation documents (new multi-reg support)
    reg_ids = getattr(latest_run, 'regulation_doc_ids', None) or []
    if not reg_ids and latest_run.regulation_doc_id:
        reg_ids = [latest_run.regulation_doc_id]  # fallback for legacy runs
    
    for reg_id in reg_ids:
        reg_doc = session.get(Document, reg_id)
        if reg_doc:
            documents.append({
                "id": str(reg_doc.id),
                "title": reg_doc.title,
                "type": "REGULATION"
            })
    
    # Load SOP documents
    for sop_id in (latest_run.sop_doc_ids or []):
        sop_doc = session.get(Document, sop_id)
        if sop_doc:
            documents.append({
                "id": str(sop_doc.id),
                "title": sop_doc.title,
                "type": "SOP"
            })

    # Use direct render to avoid TemplateResponse caching issues
    template = templates.env.get_template("report.html")
    html = template.render(
        request=request,
        findings=findings,
        documents=documents,
        analysis=analysis
    )
    return HTMLResponse(content=html)


@router.post("/run")
async def run_analysis(
    name: str = Form(...),
    regulation_doc_ids: List[str] = Form(default=[]),
    sop_doc_ids: List[str] = Form(default=[]),
    session: Session = Depends(get_session)
):
    if not regulation_doc_ids:
        return RedirectResponse(url="/run-analysis?error=no_regulation", status_code=303)
    if not sop_doc_ids:
        return RedirectResponse(url="/run-analysis?error=no_sop", status_code=303)

    sop_ids_list = sop_doc_ids

    run = AnalysisRun(
        name=name,
        regulation_doc_ids=regulation_doc_ids,     # store all selected regulations
        sop_doc_ids=sop_ids_list,
        status="RUNNING"
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    findings = run_gap_analysis(
        analysis_id=run.id,
        regulation_doc_ids=regulation_doc_ids,
        sop_doc_ids=sop_ids_list,
        session=session
    )

    run.status = "COMPLETED"
    session.add(run)
    session.commit()

    return RedirectResponse(
        url=f"/analyses/report?analysis_success=1&findings={len(findings)}",
        status_code=303
    )
