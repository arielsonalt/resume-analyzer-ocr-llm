from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.ocr.pdf_utils import extract_images_from_pdf
from app.ocr.tesseract_engine import TesseractOCREngine
from app.ocr.easyocr_engine import EasyOCREngine
from app.ocr.paddle_engine import PaddleOCREngine

from app.llm.summarizer import Summarizer
from app.llm.explainer import Explainer
from app.rank.matcher import rank_documents

from app.store.mongo import MongoLogStore
from app.store.models import LogEntry

app = FastAPI(
    title="TechMatch Analisador de Currículos (OCR + LLM)",
    version="1.0.0",
    description="Recebe múltiplos currículos (PDF/Imagem), gera sumários e responde queries de recrutamento com justificativas. Registra logs sem armazenar documentos."
)

def get_ocr_engine(name: str):
    name = (name or "tesseract").lower()
    if name == "tesseract":
        return TesseractOCREngine()
    if name == "easyocr":
        return EasyOCREngine()
    if name == "paddleocr":
        return PaddleOCREngine()
    raise HTTPException(status_code=422, detail="ocr_engine inválido. Use: tesseract|easyocr|paddleocr")


summarizer = Summarizer()
explainer = Explainer()
log_store = MongoLogStore() 


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_uuid(value: str) -> str:
    try:
        uuid.UUID(value)
        return value
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"request_id inválido (UUID esperado): {e}")

class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["request_id inválido (UUID esperado): badly formed hexadecimal UUID string"])

@app.post(
    "/v1/cv/analyze",
    summary="Analisa múltiplos currículos e retorna o ranking por query",
    response_class=JSONResponse,
    responses={
        200: {
            "description": "Resultado do ranking",
            "content": {
                "application/json": {
                    "examples": {
                        "summary_mode": {
                            "summary": "Sem query: sumário por currículo",
                            "value": {
                                "request_id": "3b6f6b84-0c4b-4e2a-8f9f-7b6f3a6a0b9a",
                                "user_id": "fabio",
                                "timestamp": "2026-01-19T12:34:56.789Z",
                                "mode": "summaries",
                                "documents": [
                                    {
                                        "document_id": "doc_1",
                                        "filename": "cv-joao.pdf",
                                        "summary": "Engenheiro de software com 5 anos..."
                                    }
                                ]
                            }
                        },
                        "ranking_mode": {
                            "summary": "Com query: ranking + justificativas",
                            "value": {
                                "request_id": "3b6f6b84-0c4b-4e2a-8f9f-7b6f3a6a0b9a",
                                "user_id": "fabio",
                                "timestamp": "2026-01-19T12:34:56.789Z",
                                "mode": "ranking",
                                "query": "Engenheiro de Software com Python, FastAPI, Docker, AWS",
                                "top_k": 2,
                                "results": [
                                    {
                                        "document_id": "doc_1",
                                        "filename": "cv-joao.pdf",
                                        "score": 0.82,
                                        "short_summary": "Python/FastAPI, AWS, CI/CD...",
                                        "justification": [
                                            {"evidence": "Experiência com FastAPI e Docker", "why": "cobre backend + container"},
                                            {"evidence": "Projetos em AWS (EC2/S3)", "why": "alinha com cloud"}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }
)
async def analyze(
    request_id: str = Form(..., description="UUID da requisição"),
    user_id: str = Form(..., description="Identificador do solicitante"),
    query: Optional[str] = Form(None, description="Pergunta de recrutamento (opcional)"),
    top_k: int = Form(3, description="Quantidade de resultados no ranking (quando houver query)"),
    ocr_engine: str = Form("tesseract", description="tesseract|easyocr|paddleocr"),
    files: List[UploadFile] = File(..., description="Lista de PDFs ou imagens (JPG/PNG)")
):  
    # Perguntar se request_id pode ser automático str(uuid.uuid1()) 
    request_id = _ensure_uuid(request_id) 
    

    allowed = {"tesseract", "easyocr", "paddleocr"}
    if ocr_engine not in allowed:
        raise HTTPException(status_code=422, detail="ocr_engine inválido. Use: tesseract|easyocr|paddleocr")
    
    engine = get_ocr_engine(ocr_engine)

    documents = []
    for idx, f in enumerate(files, start=1):
        content_type = (f.content_type or "").lower()
        filename = f.filename or f"file_{idx}"
        data = await f.read()

        doc_id = f"doc_{idx}"

        if filename.lower().endswith(".pdf") or "pdf" in content_type:
            images = extract_images_from_pdf(data)
            text_parts = [engine.image_to_text(img) for img in images]
            full_text = "\n".join(t for t in text_parts if t.strip())
        else:
            full_text = engine.bytes_to_text(data)

        documents.append(
            {
                "document_id": doc_id,
                "filename": filename,
                "text": full_text.strip()
            }
        )

    for d in documents:
        if len(d["text"]) < 50:
            d["text_warning"] = "Texto muito curto/ruim. Possível OCR fraco ou arquivo com baixa qualidade."

    timestamp = _now_iso()

    if not query or not query.strip():
        out_docs = []
        for d in documents:
            summary = summarizer.summarize(d["text"])
            out_docs.append(
                {
                    "document_id": d["document_id"],
                    "filename": d["filename"],
                    "summary": summary,
                    **({"warning": d["text_warning"]} if "text_warning" in d else {})
                }
            )

        response = {
            "request_id": request_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "mode": "summaries",
            "documents": out_docs
        }

        log_store.insert(
            LogEntry(
                request_id=request_id,
                user_id=user_id,
                timestamp=timestamp,
                query=None,
                result=response
            )
        )
        return JSONResponse(response)

    ranked = rank_documents(query=query, documents=documents, top_k=top_k)

    results = []
    for item in ranked:
        just = explainer.build_justification(query=query, evidence_snippets=item["evidence_snippets"])
        results.append(
            {
                "document_id": item["document_id"],
                "filename": item["filename"],
                "score": round(float(item["score"]), 4),
                "short_summary": summarizer.short_summary(item["text"]),
                "justification": just,
                **({"warning": item["warning"]} if item.get("warning") else {})
            }
        )

    response = {
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": timestamp,
        "mode": "ranking",
        "query": query,
        "top_k": top_k,
        "results": results
    }

    log_store.insert(
        LogEntry(
            request_id=request_id,
            user_id=user_id,
            timestamp=timestamp,
            query=query,
            result=response
        )
    )

    return JSONResponse(response)
@app.get(
    "/v1/logs",
    summary="Lista logs salvos no Mongo",
    description="Retorna os registros de uso salvos no banco para auditoria",
    responses={
        200: {
            "description": "OK. Lista logs.",
            "content": {
                "application/json": {
                    "examples": {
                        "logs_ok": {
                            "value": {
                                "count": 1,
                                "logs": [
                                    {
                                        "_id": "65a1c2f0a3b1c2d3e4f56789",
                                        "request_id": "3b6f6b84-0c4b-4e2a-8f9f-7b6f3a6a0b9a",
                                        "user_id": "fabio",
                                        "timestamp": "2026-01-19T12:34:56.789Z",
                                        "query": "Engenheiro de Software com Python, FastAPI, Docker, AWS",
                                        "result": {"mode": "ranking"}
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
         400: {
            "description": "Requisição inválida (ex.: arquivo vazio, payload malformado).",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "bad_request": {"value": {"detail": "Arquivo inválido ou vazio."}}
                    }
                }
            }
        },
        422: {
            "description": "Erro de validação (ex.: request_id não é UUID, ocr_engine inválido, campos obrigatórios ausentes).",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_uuid": {
                            "value": {
                                "detail": "request_id inválido (UUID esperado): badly formed hexadecimal UUID string"
                            }
                        },
                        "invalid_ocr_engine": {
                            "value": {"detail": "ocr_engine inválido. Use: tesseract|easyocr|paddleocr"}
                        }
                    }
                }
            }
        },
        500: {
            "description": "Erro interno (ex.: OCR/LLM falhou, erro de persistência no Mongo).",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "internal_error": {"value": {"detail": "Erro interno ao processar a requisição."}}
                    }
                }
            }
        }
    }
)
def get_logs(user_id: str | None = None, limit: int = 50):
    """
    • Se user_id for informado → filtra por usuário  
    • limit controla quantos registros retorna
    """
    if user_id:
        logs = log_store.find_by_user(user_id, limit)
    else:
        logs = log_store.find_all(limit)

    return {"count": len(logs), "logs": logs}
