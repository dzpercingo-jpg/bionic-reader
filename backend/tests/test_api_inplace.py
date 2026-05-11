"""Integration tests for the /api/export-inplace endpoint."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"
SETTINGS = {"enabled": True, "fixation_ratio": 0.5, "min_word_length": 4}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_formats_lists_inplace(client: TestClient) -> None:
    r = client.get("/api/formats")
    assert r.status_code == 200
    payload = r.json()
    assert set(payload["inplace"]) == {"docx", "pdf", "pptx", "xlsx"}


@pytest.mark.parametrize(
    "fixture_name, expected_prefix, mime",
    [
        ("with_image_and_table.docx", b"PK", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("with_image_and_table.pdf", b"%PDF", "application/pdf"),
        ("with_image_and_table.pptx", b"PK", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("with_formula_and_image.xlsx", b"PK", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ],
)
def test_inplace_endpoint_returns_valid_file(
    client: TestClient, fixture_name: str, expected_prefix: bytes, mime: str
) -> None:
    path = FIXTURES / fixture_name
    with path.open("rb") as f:
        r = client.post(
            "/api/export-inplace",
            files={"file": (path.name, f, mime)},
            data={"settings": json.dumps(SETTINGS)},
        )
    assert r.status_code == 200, r.text
    assert r.content[: len(expected_prefix)] == expected_prefix
    assert "attachment" in r.headers["content-disposition"]
    assert ".bionic." in r.headers["content-disposition"]


def test_inplace_endpoint_rejects_unsupported(client: TestClient) -> None:
    r = client.post(
        "/api/export-inplace",
        files={"file": ("note.txt", b"hello", "text/plain")},
        data={"settings": json.dumps(SETTINGS)},
    )
    assert r.status_code == 400
    assert "not supported" in r.json()["detail"]


def test_inplace_endpoint_rejects_empty_file(client: TestClient) -> None:
    r = client.post(
        "/api/export-inplace",
        files={"file": ("doc.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"settings": json.dumps(SETTINGS)},
    )
    assert r.status_code == 400


def test_inplace_endpoint_rejects_bad_settings(client: TestClient) -> None:
    path = FIXTURES / "with_image_and_table.docx"
    with path.open("rb") as f:
        r = client.post(
            "/api/export-inplace",
            files={"file": (path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"settings": "not-json"},
        )
    assert r.status_code == 400
