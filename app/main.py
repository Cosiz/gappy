from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.core.config import get_settings
from app.core.database import create_db_and_tables, engine
from app.api.v1 import analyses, documents, findings
from app.models.finding import Finding

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
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

# === Web Portal ===
@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/upload", include_in_schema=False)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/run-analysis", include_in_schema=False)
async def run_analysis_page(request: Request):
    return templates.TemplateResponse("run_analysis.html", {"request": request})

@app.get("/report", include_in_schema=False)
async def gap_analysis_report(request: Request):
    with Session(engine) as session:
        findings_list = session.exec(select(Finding)).all()
    
    return templates.TemplateResponse(
        "report.html", 
        {"request": request, "findings": findings_list}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)