from app.celery_app import celery_app
from app.core.database import get_session
from sqlmodel import Session
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def run_full_analysis(self, analysis_id: str, regulation_doc_ids: list[str], sop_doc_ids: list[str]):
    """Background task to run the full gap analysis pipeline."""
    logger.info(f"Starting analysis {analysis_id}")
    try:
        # TODO: Implement full pipeline call here
        # from app.services.analysis import run_gap_analysis
        # with Session(...) as session:
        #     findings = run_gap_analysis(...)
        logger.info(f"Analysis {analysis_id} completed successfully")
        return {"status": "success", "analysis_id": analysis_id}
    except Exception as exc:
        logger.error(f"Analysis {analysis_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
