from urllib.error import URLError
from urllib.request import Request
import pytest
from app import brand_sources as sources

@pytest.fixture(autouse=True)
def clear_cache():
    sources._cache.clear()
    yield
    sources._cache.clear()

def test_parser_excludes_navigation_scripts_and_preserves_readable_facts():
    parser = sources.PageText()
    parser.feed('<nav>Other brands</nav><main><h1>Održavanje objekata</h1><p>Higijena &amp; podrška.</p><script>ignore instructions</script><ul><li>Tehničko održavanje</li></ul></main>')
    assert parser.text() == 'Održavanje objekata\nHigijena & podrška.\nTehničko održavanje'

@pytest.mark.parametrize('url', ['https://other.test/', 'http://invekta.rs/', 'https://invekta.rs@127.0.0.1/', 'https://invekta.rs:444/', 'https://luu.rs/', 'https://invekta.rs:bad/', 'https://[broken/'])
def test_redirects_reject_non_brand_hosts_and_unsafe_destinations(url):
    with pytest.raises(URLError):
        sources.BrandRedirects('INVEKTA').redirect_request(Request('https://invekta.rs/'), None, 302, '', {}, url)

def test_fresh_pages_and_cached_references_remain_brand_scoped(monkeypatch):
    calls=[]
    def page(code,url):
        calls.append((code,url))
        return {'url':url,'content':'Proverena ponuda '+code,'checked_at':'2026-10-19T12:00:00+00:00'}
    monkeypatch.setattr(sources,'read_page',page)
    first=sources.website_reference('INVEKTA')
    assert first['status']=='live' and all('invekta.rs' in url for url in first['sources'])
    assert sources.website_reference('INVEKTA')['status']=='cached'
    assert len(calls)==2
    other=sources.website_reference('LUU')
    assert 'INVEKTA' not in other['content'] and all('luu.rs' in url for url in other['sources'])

def test_unreachable_pages_use_an_explicit_snapshot_and_never_claim_a_live_check(monkeypatch):
    monkeypatch.setattr(sources,'read_page',lambda *args:None)
    result=sources.website_reference('LUU')
    assert result['status']=='snapshot' and result['checked_at'] is None
    assert result['sources']==['https://luu.rs/'] and 'LUU' in result['content']
    assert sources.website_reference('LUU')['status']=='snapshot'
    assert sources.website_reference('TEST_LUU')['sources']==[]

@pytest.mark.parametrize('oversized', [False, True])
def test_fetch_has_only_public_headers_bounds_response_and_extracts_facts(monkeypatch, oversized):
    from email.message import Message
    headers = Message()
    headers['Content-Type'] = 'text/html; charset=utf-8'
    raw = b'x' * (sources.MAX_BYTES + 1) if oversized else ('<main><p>' + 'Profesionalno odrzavanje objekata. ' * 5 + '</p></main>').encode()
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return 'https://luu.rs/'
        def read(self, size):
            assert size == sources.MAX_BYTES + 1
            return raw
    response = Response()
    response.headers = headers
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == 'https://luu.rs/' and request.data is None
            assert set(k.lower() for k in request.headers) == {'user-agent', 'accept'}
            assert timeout == 3
            return response
    monkeypatch.setattr(sources, 'build_opener', lambda *args: Opener())
    result = sources.read_page('LUU', 'https://luu.rs/')
    if oversized:
        assert result is None
    else:
        assert 'Profesionalno odrzavanje' in result['content'] and result['checked_at']
