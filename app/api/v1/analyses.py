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
async def view_report(request: Request, analysis_id: str = None, session: Session = Depends(get_session)):
    """View gap analysis reports. Supports selecting different historical runs via analysis_id."""
    from fastapi.responses import HTMLResponse

    # Fetch all analysis runs
    all_runs = session.exec(
        select(AnalysisRun).order_by(AnalysisRun.created_at.desc())
    ).all()

    if not all_runs:
        return HTMLResponse(content="""
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>No Reports</title>
        <script src="https://cdn.tailwindcss.com"></script></head>
        <body class="bg-[#fafafa]"><div class="max-w-5xl mx-auto px-8 py-12">
        <div class="text-3xl font-semibold tracking-tighter mb-4">No gap analysis reports yet</div>
        <a href="/run-analysis" class="px-5 py-2.5 rounded-2xl bg-black text-white text-sm">Run New Analysis →</a>
        </div></body></html>
        """)

    # Select the run to display
    selected_run = None
    if analysis_id:
        selected_run = next((r for r in all_runs if str(r.id) == analysis_id), None)
    if not selected_run:
        selected_run = all_runs[0]

    # Load findings
    raw_findings = session.exec(select(Finding).where(Finding.analysis_id == selected_run.id)).all()

    findings = []
    for f in raw_findings:
        findings.append({
            "id": str(f.id),
            "requirement_id": f.requirement_id,
            "label": _safe(f.label),
            "confidence": f.confidence,
            "rationale": f.rationale or "",
            "missing_aspects": f.missing_aspects if isinstance(f.missing_aspects, list) else [],
            "supporting_sop_anchors": getattr(f, 'supporting_anchors', []) or [],
            "status": _safe(f.status),
        })

    analysis = {
        "id": str(selected_run.id),
        "name": selected_run.name or "Gap Analysis",
        "created_at": selected_run.created_at,
    }

    # Build list for dropdown
    analyses_list = [{"id": str(r.id), "name": r.name or f"Analysis {str(r.id)[:8]}", "created_at": r.created_at} for r in all_runs]

    # Load documents
    documents = []
    reg_ids = getattr(selected_run, 'regulation_doc_ids', None) or []
    if not reg_ids and getattr(selected_run, 'regulation_doc_id', None):
        reg_ids = [selected_run.regulation_doc_id]
    for rid in reg_ids:
        d = session.get(Document, rid)
        if d: documents.append({"id": str(d.id), "title": d.title, "type": "REGULATION"})
    for sid in (getattr(selected_run, 'sop_doc_ids', None) or []):
        d = session.get(Document, sid)
        if d: documents.append({"id": str(d.id), "title": d.title, "type": "SOP"})

    template = templates.env.get_template("report.html")
    html = template.render(request=request, findings=findings, documents=documents, analysis=analysis, analyses=analyses_list)
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
