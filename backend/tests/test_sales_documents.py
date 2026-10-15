import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import mysql, postgresql
from app.models import Membership, SalesDocument, User
from app.sales_document_files import MAX_DOCUMENT_SIZE

ORIGIN = {"Origin": "http://localhost:5173", "Content-Type": "application/octet-stream"}
PDF = b"%PDF-1.7\nTest sales document\n%%EOF"
PATH = "/api/units/101/sales-documents"


def login(client, username):
    response = client.post("/api/auth/login", json={"username": username, "password": "test-password-only-123"}, headers={"Origin": ORIGIN["Origin"]})
    assert response.status_code == 200


def make_admin(db):
    db.get(Membership, (101, 101)).role = "admin"
    db.commit()


def upload(client, **params):
    return client.post(PATH, params={"filename": "Ponuda Ž.pdf", **params}, content=PDF, headers=ORIGIN)


def test_admin_upload_is_downloadable_by_other_team_members_not_other_brands(client, db):
    assert client.get(PATH).status_code == 401
    assert upload(client).status_code == 401
    make_admin(db)
    login(client, "manager")
    response = upload(client, title="Nova ponuda")
    assert response.status_code == 201
    document = response.json()
    assert document["title"] == "Nova ponuda" and document["size_bytes"] == len(PDF)
    assert document["filename"] == "Ponuda Ž.pdf" and "data" not in document
    download = PATH + f'/{document["id"]}/download'
    client.post("/api/auth/logout", headers=ORIGIN)
    assert client.get(download).status_code == 401
    for username in ("sales", "other"):
        login(client, username)
        listed = client.get(PATH).json()
        assert listed["total"] == 1 and listed["items"][0]["id"] == document["id"]
        response = client.get(download)
        assert response.status_code == 200 and response.content == PDF
        assert response.headers["content-type"] == "application/octet-stream"
        assert response.headers["content-disposition"].startswith("attachment;")
        assert "filename*=UTF-8''Ponuda%20%C5%BD.pdf" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["cache-control"] == "no-store"
    login(client, "outsider")
    assert client.get(PATH).status_code == 403
    assert client.get(download).status_code == 403
    assert client.get(f'/api/units/102/sales-documents/{document["id"]}/download').status_code == 404
    assert client.get("/api/units/102/sales-documents").json()["total"] == 0
    db.get(Membership, (101, 101)).role = "manager"
    db.commit()
    login(client, "manager")
    assert client.get(download).content == PDF
    db.get(Membership, (101, 101)).enabled = False
    db.commit()
    assert client.get(download).status_code == 403
    login(client, "sales")
    db.get(User, 102).active = False
    db.commit()
    assert client.get(download).status_code == 401


def test_manager_and_sales_cannot_upload_even_if_ui_is_bypassed(client, db):
    for username in ("manager", "sales", "other"):
        login(client, username)
        assert upload(client).status_code == 403
    assert db.scalar(select(func.count()).select_from(SalesDocument).where(SalesDocument.business_unit_id == 101)) == 0
    # Platform admin still needs an enabled membership in the requested brand.
    db.get(User, 101).is_platform_admin = True
    db.commit()
    login(client, "manager")
    assert upload(client).status_code == 201
    db.get(Membership, (101, 101)).enabled = False
    db.commit()
    assert upload(client).status_code == 403
    assert client.get(PATH).status_code == 403


def test_origin_validation_and_file_validation_leave_no_partial_records(client, db):
    make_admin(db)
    login(client, "manager")
    assert client.post(PATH, params={"filename": "Offer.pdf"}, content=PDF).status_code == 403
    assert client.post(PATH, params={"filename": "Offer.pdf"}, content=PDF, headers={**ORIGIN, "Origin": "https://other.example"}).status_code == 403
    for filename, body, code in [("Offer.html", b"<html>", 422), ("Offer.pdf", b"", 422),
                                  ("Offer.pdf", b"fake", 422), ("a\r\nb.pdf", PDF, 422),
                                  ("a" * 256 + ".pdf", PDF, 422), ("Offer.pdf", b"%PDF-" + b"x" * MAX_DOCUMENT_SIZE, 413)]:
        response = client.post(PATH, params={"filename": filename}, content=body, headers=ORIGIN)
        assert response.status_code == code
    assert db.scalar(select(func.count()).select_from(SalesDocument).where(SalesDocument.business_unit_id == 101)) == 0
    # Ignore path components; preserve original Unicode base filename safely.
    assert upload(client, filename="../Ponuda Ž.pdf").json()["filename"] == "Ponuda Ž.pdf"


def test_search_pagination_and_blob_storage_do_not_expose_content_in_metadata(client, db):
    make_admin(db)
    login(client, "manager")
    for title in ("Ponuda A", "Cenovnik", "Ponuda B", "100% odobreno"):
        assert upload(client, title=title).status_code == 201
    first = client.get(PATH, params={"limit": 2}).json()
    second = client.get(PATH, params={"limit": 2, "offset": 2}).json()
    assert first["total"] == second["total"] == 4
    assert {r["id"] for r in first["items"]}.isdisjoint(r["id"] for r in second["items"])
    assert client.get(PATH, params={"search": "ponuda a"}).json()["total"] == 1
    assert client.get(PATH, params={"search": "%"}).json()["total"] == 1
    assert all("data" not in row for row in first["items"])
    assert SalesDocument.data.property.deferred
    assert str(SalesDocument.__table__.c.data.type.compile(dialect=mysql.dialect())) == "MEDIUMBLOB"
    assert str(SalesDocument.__table__.c.data.type.compile(dialect=postgresql.dialect())) == "BYTEA"


def test_file_larger_than_mysql_plain_blob_limit_is_not_truncated(client, db):
    make_admin(db)
    login(client, "manager")
    body = PDF + b"0" * (128 * 1024)
    response = client.post(PATH, params={"filename": "Big.pdf"}, content=body, headers=ORIGIN)
    assert response.status_code == 201 and response.json()["size_bytes"] == len(body)
    assert client.get(PATH + f'/{response.json()["id"]}/download').content == body


def test_streaming_upload_enforces_limit_without_content_length(client, db):
    make_admin(db)
    login(client, "manager")
    def chunks():
        yield b"%PDF-1.7\n"
        yield b"x" * MAX_DOCUMENT_SIZE
    response = client.post(PATH, params={"filename": "Offer.pdf"}, content=chunks(), headers=ORIGIN)
    assert response.status_code == 413
    assert db.scalar(select(func.count()).select_from(SalesDocument).where(SalesDocument.business_unit_id == 101)) == 0


@pytest.mark.parametrize("filename,body", [("Test.doc", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    ("Test.xls", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"), ("Test.docx", b"PK\x03\x04"),
    ("Test.xlsx", b"PK\x03\x04"), ("Test.png", b"\x89PNG\r\n\x1a\n"), ("Test.jpg", b"\xff\xd8\xff")])
def test_supported_file_types_roundtrip_as_downloads(client, db, filename, body):
    make_admin(db)
    login(client, "manager")
    response = client.post(PATH, params={"filename": filename}, content=body, headers=ORIGIN)
    assert response.status_code == 201
    assert client.get(PATH + f'/{response.json()["id"]}/download').content == body
