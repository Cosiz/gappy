from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.core.config import get_settings
from app.core.database import create_db_and_tables, engine
from app.api.v1 import analyses, documents, findings
from app.models.finding import Finding
from app.models.document import Document

# Import all models so SQLAlchemy registers them before create_all()
from app.models import user, document, requirement, analysis, finding

import os

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Regulatory Gap Analysis System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = "app/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(analyses.router)
app.include_router(documents.router)
app.include_router(findings.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "Project Gappy API", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request):
    with Session(engine) as session:
        documents_list = session.exec(select(Document)).all()
        findings_list = session.exec(select(Finding)).all()
    
    pending_officer = len([f for f in findings_list if f.status.value == "PENDING_OFFICER"])
    pending_supervisor = len([f for f in findings_list if f.status.value == "PENDING_SUPERVISOR"])
    
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html",
        context={
            "total_documents": len(documents_list),
            "pending_officer": pending_officer,
            "pending_supervisor": pending_supervisor,
            "total_findings": len(findings_list)
        }
    )

@app.get("/upload", include_in_schema=False)
async def upload_page(request: Request):
    success = request.query_params.get("success") == "1"
    doc_title = request.query_params.get("doc")
    return templates.TemplateResponse(
        request=request, 
        name="upload.html", 
        context={"success": {"title": doc_title} if success else None}
    )

@app.get("/documents", include_in_schema=False)
async def documents_page(request: Request):
    with Session(engine) as session:
        documents_list = session.exec(select(Document)).all()
    return templates.TemplateResponse(
        request=request,
        name="documents.html",
        context={"documents": documents_list}
    )

@app.get("/run-analysis", include_in_schema=False)
async def run_analysis_page(request: Request):
    with Session(engine) as session:
        all_docs = session.exec(select(Document).order_by(Document.created_at.desc())).all()
    
    regulations = [d for d in all_docs if d.doc_type.value == "REGULATION"]
    sops = [d for d in all_docs if d.doc_type.value == "SOP"]
    
    return templates.TemplateResponse(
        request=request, 
        name="run_analysis.html",
        context={
            "regulations": regulations,
            "sops": sops
        }
    )



@app.get("/report", include_in_schema=False)
async def redirect_report(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/analyses/report" + ("?" + str(request.url.query) if request.url.query else ""), status_code=307)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)