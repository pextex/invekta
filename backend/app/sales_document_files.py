"""Limits and file metadata for download-only sales documents."""

from pathlib import PurePosixPath
from fastapi import HTTPException, Request

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
FILE_TYPES = {
    ".pdf": ("application/pdf", (b"%PDF-",)),
    ".doc": ("application/msword", (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)),
    ".xls": ("application/vnd.ms-excel", (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", (b"PK\x03\x04",)),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", (b"PK\x03\x04",)),
    ".png": ("image/png", (b"\x89PNG\r\n\x1a\n",)),
    ".jpg": ("image/jpeg", (b"\xff\xd8\xff",)),
    ".jpeg": ("image/jpeg", (b"\xff\xd8\xff",)),
}


def file_metadata(filename: str):
    if any(ord(char) < 32 or ord(char) == 127 for char in filename):
        raise HTTPException(422, "Naziv fajla sadrži nedozvoljene znakove.")
    name = PurePosixPath(filename.replace("\\", "/")).name.strip()
    extension = PurePosixPath(name).suffix.lower()
    if not name or extension not in FILE_TYPES:
        raise HTTPException(422, "Dozvoljeni su PDF, Word, Excel, PNG i JPG fajlovi.")
    return name, FILE_TYPES[extension]


async def read_document(request: Request):
    length = request.headers.get("content-length")
    if length is not None:
        try:
            size = int(length)
        except ValueError:
            raise HTTPException(400, "Neispravna veličina fajla.") from None
        if size < 0:
            raise HTTPException(400, "Neispravna veličina fajla.")
        if size > MAX_DOCUMENT_SIZE:
            raise HTTPException(413, "Fajl može imati najviše 10 MB.")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_DOCUMENT_SIZE:
            raise HTTPException(413, "Fajl može imati najviše 10 MB.")
        data.extend(chunk)
    if not data:
        raise HTTPException(422, "Izabrani fajl je prazan.")
    return bytes(data)
