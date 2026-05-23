"""Seed sample data for comprehensive testing of Gappy"""
from sqlmodel import Session, select
from app.core.database import engine
from app.models.user import User, UserRole
from app.models.document import Document, DocumentType
from app.models.requirement import Requirement
from app.models.analysis import AnalysisRun
from datetime import datetime
import uuid

def seed_sample_data():
    with Session(engine) as session:
        # Check if already seeded
        existing_docs = session.exec(select(Document)).first()
        if existing_docs:
            print("Data already seeded. Skipping.")
            return

        print("Seeding sample data...")

        # 1. Create a sample user
        user = User(
            email="darren@cosie.com",
            full_name="Darren Tan",
            role=UserRole.COMPLIANCE_OFFICER,
            hashed_password="demo"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # 2. Create sample documents
        reg_doc = Document(
            title="HKMA AI Governance Guidelines v2.3",
            doc_type=DocumentType.REGULATION,
            version="2.3",
            file_path="uploads/seed_reg.pdf",
            uploaded_by=user.id
        )
        sop_doc = Document(
            title="Internal AI Risk Management SOP v1.4",
            doc_type=DocumentType.SOP,
            version="1.4",
            file_path="uploads/seed_sop.pdf",
            uploaded_by=user.id
        )
        session.add(reg_doc)
        session.add(sop_doc)
        session.commit()
        session.refresh(reg_doc)
        session.refresh(sop_doc)

        # 3. Create sample requirements (from the regulation)
        requirements = [
            Requirement(
                requirement_id="HKMA-AI-3.1",
                document_id=reg_doc.id,
                obligation_type="SHALL",
                subject="Board Oversight",
                action="The board of directors shall establish an AI governance committee with clear reporting lines.",
                verbatim="The board shall establish...",
                source_section="Section 3.1"
            ),
            Requirement(
                requirement_id="HKMA-AI-3.2",
                document_id=reg_doc.id,
                obligation_type="SHOULD",
                subject="Risk Management",
                action="Institutions should maintain a risk inventory covering all AI use cases.",
                verbatim="Institutions should maintain...",
                source_section="Section 3.2"
            ),
            Requirement(
                requirement_id="HKMA-AI-4.1",
                document_id=reg_doc.id,
                obligation_type="SHALL",
                subject="Model Validation",
                action="All AI models must undergo independent validation before deployment.",
                verbatim="All AI models must undergo...",
                source_section="Section 4.1"
            ),
        ]
        for req in requirements:
            session.add(req)
        session.commit()

        print(f"Seeded: 1 user, 2 documents, {len(requirements)} requirements")
        print("Sample data ready for testing.")

if __name__ == "__main__":
    seed_sample_data()