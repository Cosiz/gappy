from sqlmodel import SQLModel, create_engine, Session
from app.core.config import get_settings

# Import models directly
from app.models.user import User
from app.models.document import Document
from app.models.requirement import Requirement
from app.models.analysis import AnalysisRun
from app.models.finding import Finding

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)