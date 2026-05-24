from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.finding import Finding, Decision, FindingStatus
from app.services.workflow import submit_officer_decision, submit_supervisor_decision
from app.core.security import require_officer, require_supervisor

router = APIRouter(prefix="/findings", tags=["findings"])

@router.get("/{finding_id}")
def get_finding(finding_id: str, session: Session = Depends(get_session)):
    finding = session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    return finding

@router.post("/{finding_id}/review/officer")
def officer_review(
    finding_id: str,
    decision: Decision = Form(...),
    comment: str | None = Form(None),
    session: Session = Depends(get_session),
    role: str = Depends(require_officer)
):
    finding = session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    
    try:
        updated = submit_officer_decision(finding, decision, comment, session)
        # Redirect back to report with success message
        return RedirectResponse(
            url="/report?review_success=1&role=officer",
            status_code=303
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/{finding_id}/review/supervisor")
def supervisor_review(
    finding_id: str,
    decision: Decision = Form(...),
    comment: str | None = Form(None),
    session: Session = Depends(get_session),
    role: str = Depends(require_supervisor)
):
    finding = session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    
    try:
        updated = submit_supervisor_decision(finding, decision, comment, session)
        return RedirectResponse(
            url="/report?review_success=1&role=supervisor",
            status_code=303
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/{finding_id}/undo")
def undo_finding(finding_id: str, session: Session = Depends(get_session)):
    from app.services.workflow import undo_officer_decision, can_undo
    finding = session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    
    if not can_undo(finding):
        raise HTTPException(400, "Undo window has expired")
    
    try:
        updated = undo_officer_decision(finding, session)
        return RedirectResponse(
            url="/report?undo_success=1",
            status_code=303
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{finding_id}/clarify")
def request_clarification_endpoint(
    finding_id: str,
    comment: str = Form(...),
    session: Session = Depends(get_session)
):
    from app.services.workflow import request_clarification
    finding = session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")
    
    try:
        updated = request_clarification(finding, comment, session)
        return RedirectResponse(
            url="/report?clarification_requested=1",
            status_code=303
        )
    except ValueError as e:
        raise HTTPException(400, str(e))