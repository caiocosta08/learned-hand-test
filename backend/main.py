from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.presentation.rate_limit import SimpleRateLimitMiddleware
from app.schemas.report import VerificationReport
from app.services.analyzer import AnalyzerService
from app.services.document_loader import DocumentLoader

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "https://learned-hand-front.acutistecnologia.com",
        "https://learned-hand-back.acutistecnologia.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SimpleRateLimitMiddleware, max_requests=20, window_seconds=60)

DOCUMENTS_DIR = Path(__file__).parent / "documents"
document_loader = DocumentLoader(DOCUMENTS_DIR)
analyzer_service = AnalyzerService()

MAX_DOC_LENGTH = 60_000
MAX_TOTAL_LENGTH = 180_000


class AnalyzeRequest(BaseModel):
    use_local_documents: bool = True
    documents_override: dict[str, str] | None = None


def _validate_overrides(overrides: dict[str, str]) -> None:
    total = 0
    for name, content in overrides.items():
        if not name or not isinstance(name, str):
            raise HTTPException(status_code=422, detail="Invalid document name.")
        if not isinstance(content, str):
            raise HTTPException(status_code=422, detail="Invalid document payload.")
        if len(content) > MAX_DOC_LENGTH:
            raise HTTPException(status_code=413, detail="Document too large.")
        total += len(content)
    if total > MAX_TOTAL_LENGTH:
        raise HTTPException(status_code=413, detail="Combined payload too large.")


@app.post("/analyze")
async def analyze(payload: AnalyzeRequest = Body(default_factory=AnalyzeRequest)) -> dict[str, VerificationReport]:
    documents = document_loader.load_documents()
    if payload.documents_override:
        _validate_overrides(payload.documents_override)
        documents.update(payload.documents_override)
    if not payload.use_local_documents and not payload.documents_override:
        raise HTTPException(status_code=422, detail="No documents available for analysis.")
    if not payload.use_local_documents and payload.documents_override:
        documents = payload.documents_override
    report = analyzer_service.analyze(documents)
    return {"report": report}
