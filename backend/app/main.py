"""FastAPI entrypoint for Bionic Reader Pro."""
from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .exporters import SUPPORTED_EXPORTS, get_exporter
from .models import ExportRequest
from .parsers import SUPPORTED_EXTENSIONS, parse_bytes

logger = logging.getLogger("bionic_reader")
logging.basicConfig(level=logging.INFO)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

app = FastAPI(
    title="Bionic Reader Pro API",
    version="0.1.0",
    description="Convert PDF/DOCX/TXT/EPUB/HTML/MD/RTF into ADHD-friendly bionic reading format.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "supported_extensions": SUPPORTED_EXTENSIONS}


@app.get("/api/formats")
def formats() -> dict[str, list[str]]:
    return {
        "input": SUPPORTED_EXTENSIONS,
        "output": SUPPORTED_EXPORTS,
    }


@app.post("/api/parse")
async def parse(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large; max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    try:
        document = parse_bytes(file.filename or "untitled.txt", data)
    except Exception as exc:
        logger.exception("parse failed")
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {exc}") from exc
    return document


@app.post("/api/export")
def export(req: ExportRequest):
    fmt = req.format
    if fmt not in SUPPORTED_EXPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {fmt}")
    exporter = get_exporter(fmt)
    try:
        body, media_type, filename = exporter(req.document, req.settings, req.title)
    except Exception as exc:
        logger.exception("export failed")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}") from exc
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
