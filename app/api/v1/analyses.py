from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.services.analysis import run_gap_analysis
from app.models.analysis import AnalysisRun

router = APIRouter(prefix="/analyses", tags=["analyses"])

@router.post("/run")
async def run_analysis(
    name: str,
    regulation_doc_id: str,
    sop_doc_ids: list[str],
    session: Session = Depends(get_session)
):
    run = AnalysisRun(
        name=name,
        regulation_doc_id=regulation_doc_id,
        sop_doc_ids=sop_doc_ids,
        status="RUNNING"
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    # Execute real analysis
    findings = run_gap_analysis(
        analysis_id=str(run.id),
        regulation_doc_id=regulation_doc_id,
        sop_doc_ids=sop_doc_ids,
        session=session
    )

    run.status = "COMPLETED"
    session.add(run)
    session.commit()

    return {
        "analysis_id": str(run.id),
        "status": "completed",
        "findings_created": len(findings)
    }