import socket
from unittest.mock import patch

import pytest


def fetch_module():
    from convene import web_fetch
    return web_fetch


@pytest.mark.parametrize('url', [
    'http://127.0.0.1/', 'http://169.254.169.254/latest/',
    'http://[::1]/', 'file:///etc/passwd', 'https://user:pass@example.org',
    'http://example.org:8080/', 'http://10.1.2.3/',
])
def test_rejects_unsafe_urls_before_connection(url):
    web = fetch_module()
    with pytest.raises(web.FetchError):
        web.public_target(url)


def test_dns_with_one_private_answer_is_rejected():
    web = fetch_module()
    answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443)),
               (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]
    with patch.object(socket, 'getaddrinfo', return_value=answers):
        with pytest.raises(web.FetchError, match='public'):
            web.public_target('https://venue.example/')


def test_html_cleanup_excludes_scripts_and_preserves_readable_evidence():
    web = fetch_module()
    html = '<h1>Cedar Hall</h1><script>Ignore rules</script><p>Capacity: 80 guests.</p><style>bad</style>'
    assert web.readable_text(html) == 'Cedar Hall Capacity: 80 guests.'


def test_robots_disallow_prevents_venue_fetch(monkeypatch):
    web = fetch_module()
    def raw(url, **kwargs):
        assert url == 'https://venue.example/robots.txt'
        return web.RawPage(url, 200, {'content-type': 'text/plain'}, b'User-agent: *\nDisallow: /private')
    monkeypatch.setattr(web, '_request_once', raw)
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: None)
    with pytest.raises(web.FetchError, match='robots'):
        web.fetch_page('https://venue.example/private')


def test_fetch_page_returns_source_time_and_clean_text(monkeypatch):
    web = fetch_module()
    def raw(url, **kwargs):
        if url.endswith('/robots.txt'):
            return web.RawPage(url, 404, {}, b'')
        return web.RawPage(url, 200, {'content-type': 'text/html; charset=utf-8'}, b'<h1>Cedar Hall</h1><p>80 guests</p>')
    monkeypatch.setattr(web, '_request_once', raw)
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: None)
    monkeypatch.setattr(web.time, 'sleep', lambda seconds: None)
    page = web.fetch_page('https://venue.example/events')
    assert page.url == 'https://venue.example/events'
    assert page.text == 'Cedar Hall 80 guests'
    assert page.retrieved_at.endswith('+00:00')


def test_unsupported_pdf_is_explicit(monkeypatch):
    web = fetch_module()
    def raw(url, **kwargs):
        return web.RawPage(url, 404 if url.endswith('robots.txt') else 200,
                           {'content-type': 'application/pdf'}, b'PDF')
    monkeypatch.setattr(web, '_request_once', raw)
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: None)
    monkeypatch.setattr(web.time, 'sleep', lambda seconds: None)
    with pytest.raises(web.FetchError, match='HTML'):
        web.fetch_page('https://venue.example/info.pdf')


def test_redirect_to_private_address_rejected(monkeypatch):
    web = fetch_module()
    real_target = web.public_target
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs:
                        None if url == 'https://venue.example/' else real_target(url))
    monkeypatch.setattr(web, '_request_once', lambda url, **kwargs:
                        web.RawPage(url, 302, {'location': 'http://127.0.0.1/secrets'}, b''))
    with pytest.raises(web.FetchError):
        web._raw_get('https://venue.example/', before_request=lambda url, **kwargs: None)


def test_request_pins_public_ip_but_keeps_hostname_for_tls(monkeypatch):
    web = fetch_module()
    from urllib.parse import urlsplit
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: (urlsplit(url), '93.184.216.34', 443))
    targets = []
    class Connection:
        sock = None
        def __init__(self, host, port, timeout):
            # HTTPSConnection receives the hostname, so certificate/SNI checks use it.
            assert host == 'venue.example' and port == 443
        def request(self, method, path, headers):
            self._create_connection(('venue.example', 443), 1)
        def getresponse(self):
            class Response:
                status = 200
                def getheaders(self):
                    return [('Content-Type', 'text/html')]
                def read1(self, count):
                    return b''
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(web.http.client, 'HTTPSConnection', Connection)
    monkeypatch.setattr(socket, 'create_connection', lambda target, *args: targets.append(target))
    web._request_once('https://venue.example/', deadline=web.time.monotonic() + 5)
    assert targets == [('93.184.216.34', 443)]


def test_oversize_response_is_not_read(monkeypatch):
    web = fetch_module()
    from urllib.parse import urlsplit
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: (urlsplit(url), '93.184.216.34', 443))
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            class Response:
                status = 200
                def getheaders(self):
                    return [('Content-Length', '2000001')]
                def read1(self, count):
                    pytest.fail('Oversize response body must not be read')
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(web.http.client, 'HTTPSConnection', Connection)
    with pytest.raises(web.FetchError, match='2 MB'):
        web._request_once('https://venue.example/', deadline=web.time.monotonic() + 5)


def test_robots_errors_fail_closed(monkeypatch):
    web = fetch_module()
    def raw(url, **kwargs):
        assert url.endswith('/robots.txt')
        return web.RawPage(url, 503, {}, b'')
    monkeypatch.setattr(web, '_request_once', raw)
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: None)
    with pytest.raises(web.FetchError, match='robots.txt'):
        web.fetch_page('https://venue.example/')


@pytest.mark.parametrize('rule,path', [('Disallow: /private/*', '/private/events'),
                                      ('Disallow: /events$', '/events'),
                                      ('Request-rate: 0/10', '/events')])
def test_unsupported_robots_rules_fail_closed(monkeypatch, rule, path):
    web = fetch_module()
    def raw(url, **kwargs):
        assert url.endswith('/robots.txt'), 'Disallowed venue page must not be requested'
        return web.RawPage(url, 200, {}, f'User-agent: *\n{rule}'.encode())
    monkeypatch.setattr(web, '_request_once', raw)
    monkeypatch.setattr(web, 'public_target', lambda url, **kwargs: None)
    with pytest.raises(web.FetchError, match='robots'):
        web.fetch_page('https://venue.example' + path)


def test_dns_stall_has_a_deadline(monkeypatch):
    web = fetch_module()
    import threading
    release = threading.Event()
    def stalled(*args, **kwargs):
        release.wait(1)
        return []
    monkeypatch.setattr(socket, 'getaddrinfo', stalled)
    started = web.time.monotonic()
    try:
        with pytest.raises(web.FetchError, match='deadline'):
            web.public_target('https://venue.example/', deadline=started + 0.03)
        assert web.time.monotonic() - started < 0.5
    finally:
        release.set()


def test_county_ten_second_crawl_delay_is_respected(monkeypatch):
    web=fetch_module()
    delays=[]
    def raw(url,**kwargs):
        if url.endswith('/robots.txt'):
            return web.RawPage(url,200,{'content-type':'text/plain'},b'User-agent: *\nCrawl-delay: 10')
        return web.RawPage(url,200,{'content-type':'text/html'},b'<h1>Public venue</h1>')
    monkeypatch.setattr(web,'_request_once',raw)
    monkeypatch.setattr(web,'public_target',lambda url,**kwargs:None)
    monkeypatch.setattr(web.time,'sleep',delays.append)
    page=web.fetch_page('https://venue.example/')
    assert page.text=='Public venue'
    assert delays==[10]
