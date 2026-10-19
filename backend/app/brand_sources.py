"""Read-only official brand pages. No client URLs, CRM content, credentials or cross-brand redirects."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import socket

from .brand_knowledge import defaults

BRAND_URLS = {
    "LUU": ("https://luu.rs/",),
    "INVEKTA": ("https://invekta.rs/cesta-pitanja/", "https://invekta.rs/upit-za-ponudu/"),
    "CENOBOTS": ("https://cenobots.rs/", "https://cenobots.rs/pametna-maloprodaja-i-trzni-centri/"),
}
CACHE_SECONDS = 900
MAX_BYTES = 300_000
_cache: dict[str, tuple[float, dict]] = {}
_lock = Lock()


class PageText(HTMLParser):
    ignored = {"script", "style", "noscript", "svg", "template", "nav", "footer", "header", "form"}
    blocks = {"p", "div", "section", "article", "main", "li", "h1", "h2", "h3", "h4", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden: list[str] = []
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored and tag not in {"br", "input", "img"}:
            self.hidden.append(tag)
        if not self.hidden and tag in self.blocks:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in self.blocks:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = [" ".join(line.split()) for line in " ".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line)[:7000]


def allowed_url(url: str, code: str) -> bool:
    try:
        parsed = urlsplit(url)
        hosts = {urlsplit(u).hostname for u in BRAND_URLS.get(code, ())}
        hosts |= {"www." + host for host in tuple(hosts) if host}
        return (parsed.scheme == "https" and parsed.hostname in hosts and parsed.port in (None, 443)
                and parsed.username is None and parsed.password is None)
    except ValueError:
        return False


class BrandRedirects(HTTPRedirectHandler):
    def __init__(self, code):
        self.code = code
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl, self.code):
            raise URLError("Unapproved website redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_page(code: str, url: str) -> dict | None:
    if url not in BRAND_URLS.get(code, ()):
        return None
    request = Request(url, headers={"User-Agent": "InvektaCRM/0.4 (public brand reference)", "Accept": "text/html"})
    try:
        with build_opener(BrandRedirects(code)).open(request, timeout=3) as response:
            if not allowed_url(response.geturl(), code) or "text/html" not in response.headers.get("Content-Type", ""):
                return None
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return None
            encoding = response.headers.get_content_charset() or "utf-8"
        parser = PageText()
        parser.feed(raw.decode(encoding, errors="replace"))
        text = parser.text()
        if len(text) < 80 or any(marker in text.lower() for marker in ("checking your browser", "just a moment", "verify you are human")):
            return None
        return {"url": url, "content": text, "checked_at": datetime.now(timezone.utc).isoformat()}
    except (HTTPError, URLError, TimeoutError, socket.timeout, ValueError, LookupError, OSError):
        return None


def website_reference(code: str) -> dict:
    code = code.upper()
    urls = BRAND_URLS.get(code, ())
    if not urls:
        return {"status": "unavailable", "sources": [], "content": "", "checked_at": None}
    now = monotonic()
    with _lock:
        cached = _cache.get(code)
        if cached and now - cached[0] < CACHE_SECONDS:
            result = cached[1]
            return {**result, "status": "cached" if result["status"] == "live" else result["status"]}
    with ThreadPoolExecutor(max_workers=2) as pool:
        pages = [page for page in pool.map(lambda url: read_page(code, url), urls) if page]
    result = {
        "status": "live" if pages else "snapshot",
        "sources": [page["url"] for page in pages] if pages else list(urls),
        "content": "\n\n".join(f"Izvor: {page['url']}\n{page['content']}" for page in pages) if pages else defaults().get(code, ""),
        "checked_at": min(page["checked_at"] for page in pages) if pages else None,
    }
    with _lock:
        _cache[code] = (now, result)
    return result
