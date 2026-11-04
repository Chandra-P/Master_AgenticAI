"""Bounded public website reads. Connections pin validated DNS answers."""
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import time
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from convene.deadlines import DeadlineError, bounded_call, remaining

USER_AGENT = 'CONVENE-Research/0.1'
MAX_BYTES = 2_000_000
MAX_TEXT = 24_000
TIMEOUT = 12


class FetchError(ValueError):
    pass


@dataclass
class RawPage:
    url: str
    status: int
    headers: dict
    body: bytes


@dataclass
class Page:
    url: str
    text: str
    retrieved_at: str


def normalize_url(url: str) -> str:
    try:
        parts = urlsplit(url.strip())
        if (parts.scheme not in ('http', 'https') or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.port not in (None, 80 if parts.scheme == 'http' else 443)
                or any(ord(c) < 33 for c in url) or '\\' in url):
            raise ValueError
        host = parts.hostname.encode('idna').decode('ascii').lower()
        host = f'[{host}]' if ':' in host else host
        return urlunsplit((parts.scheme, host, parts.path or '/', parts.query, ''))
    except (ValueError, UnicodeError):
        raise FetchError('Use a public HTTP(S) URL on its standard port, without credentials.') from None


def public_target(url: str, *, deadline=None):
    parts = urlsplit(normalize_url(url))
    host = parts.hostname
    port = 443 if parts.scheme == 'https' else 80
    try:
        answers = bounded_call(lambda: socket.getaddrinfo(host, port, type=socket.SOCK_STREAM),
                               deadline=min(deadline or time.monotonic() + 5, time.monotonic() + 5))
        addresses = [answer[4][0] for answer in answers]
        if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
            raise FetchError('Only public internet destinations are allowed.')
    except DeadlineError as error:
        raise FetchError(str(error)) from None
    except (OSError, ValueError) as error:
        if isinstance(error, FetchError):
            raise
        raise FetchError('Could not resolve a public internet destination.') from None
    return parts, addresses[0], port


def _request_once(url: str, *, deadline: float) -> RawPage:
    parts, address, port = public_target(url, deadline=deadline)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise FetchError('Website read deadline exceeded.')
    connection_type = http.client.HTTPSConnection if parts.scheme == 'https' else http.client.HTTPConnection
    connection = connection_type(parts.hostname, port, timeout=min(TIMEOUT, remaining))
    # HTTPSConnection still uses the original hostname for TLS certificate checks/SNI.
    # The socket connects directly to the already validated IP, preventing DNS rebinding.
    connection._create_connection = lambda target, timeout, source_address=None: socket.create_connection(
        (address, port), timeout, source_address)
    try:
        path = urlunsplit(('', '', parts.path or '/', parts.query, ''))
        connection.request('GET', path, headers={
            'User-Agent': USER_AGENT, 'Accept': 'text/html,text/plain', 'Accept-Encoding': 'identity'})
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        if headers.get('content-encoding', 'identity').lower() != 'identity':
            raise FetchError('Compressed responses are not supported.')
        if int(headers.get('content-length', '0')) > MAX_BYTES:
            raise FetchError('Page exceeds the 2 MB read limit.')
        chunks, size = [], 0
        if response.status in (301, 302, 303, 307, 308):
            return RawPage(url, response.status, headers, b'')
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FetchError('Website read deadline exceeded.')
            if connection.sock:
                connection.sock.settimeout(min(TIMEOUT, remaining))
            chunk = response.read1(min(65536, MAX_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_BYTES:
                raise FetchError('Page exceeds the 2 MB read limit.')
        return RawPage(url, response.status, headers, b''.join(chunks))
    except (OSError, http.client.HTTPException, ValueError) as error:
        if isinstance(error, FetchError):
            raise
        raise FetchError('Website request failed or timed out.') from None
    finally:
        connection.close()


def _raw_get(url: str, *, before_request=None, deadline=None) -> RawPage:
    deadline = deadline or time.monotonic() + TIMEOUT
    url = normalize_url(url)
    for _ in range(4):
        # This preflight also protects redirect targets before robots checks.
        public_target(url, deadline=deadline)
        if before_request:
            before_request(url)
        page = _request_once(url, deadline=deadline)
        if page.status not in (301, 302, 303, 307, 308):
            return page
        location = page.headers.get('location')
        if not location:
            raise FetchError('Redirect has no destination.')
        url = normalize_url(urljoin(url, location))
    raise FetchError('Too many website redirects.')


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg', 'template'):
            self.hidden.append(tag)

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def readable_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return ' '.join(' '.join(parser.text).split())[:MAX_TEXT]


def fetch_page(url: str, *, deadline=None) -> Page:
    deadline = min(deadline or time.monotonic() + 30, time.monotonic() + 30)
    robots_by_origin = {}

    def check_robots(target):
        parts = urlsplit(target)
        origin = urlunsplit((parts.scheme, parts.netloc, '', '', ''))
        if origin not in robots_by_origin:
            robots = _raw_get(origin + '/robots.txt', deadline=deadline)
            if robots.status == 404:
                rules = ['User-agent: *', 'Allow: /']
            elif robots.status == 200:
                rules = robots.body.decode('utf-8', errors='replace').splitlines()
            else:
                raise FetchError('Could not verify robots.txt permissions.')
            # stdlib's parser does not implement wildcard/end-anchor matching.
            # Fail closed rather than silently bypass restrictions on these sites.
            for line in rules:
                directive, _, value = line.split('#', 1)[0].partition(':')
                if directive.strip().lower() in ('allow', 'disallow') and any(c in value for c in '*$'):
                    raise FetchError('Complex robots.txt wildcard rules are unsupported; use another public venue URL.')
            parser = RobotFileParser()
            parser.parse(rules)
            delay = parser.crawl_delay(USER_AGENT) or 1
            rate = parser.request_rate(USER_AGENT)
            if rate:
                if rate.requests <= 0 or rate.seconds <= 0:
                    raise FetchError('Invalid robots.txt request rate; cannot safely fetch this page.')
                delay = max(delay, rate.seconds / rate.requests)
            if delay > 20:
                raise FetchError('robots.txt requests a longer crawl interval than supported.')
            robots_by_origin[origin] = parser, delay
        parser, delay = robots_by_origin[origin]
        if not parser.can_fetch(USER_AGENT, target):
            raise FetchError('Fetching this page is disallowed by robots.txt.')
        try:
            if remaining(deadline) <= delay:
                raise DeadlineError('Research deadline exceeded before permitted crawl interval.')
        except DeadlineError as error:
            raise FetchError(str(error)) from None
        time.sleep(delay)

    page = _raw_get(url, before_request=check_robots, deadline=deadline)
    if page.status != 200:
        raise FetchError(f'Website returned HTTP {page.status}; use a public venue details page.')
    content_type = page.headers.get('content-type', '').lower()
    if not any(kind in content_type for kind in ('text/html', 'text/plain', 'application/xhtml+xml')):
        raise FetchError('Only HTML and plain text are supported; PDF and JavaScript-only pages are unsupported.')
    encoding = re.search(r'charset=["\']?([\w-]+)', content_type)
    try:
        raw_text = page.body.decode(encoding.group(1) if encoding else 'utf-8', errors='replace')
    except LookupError:
        raw_text = page.body.decode('utf-8', errors='replace')
    text = readable_text(raw_text) if 'html' in content_type else ' '.join(raw_text.split())[:MAX_TEXT]
    if not text:
        raise FetchError('No readable page text; JavaScript-only pages are unsupported.')
    return Page(page.url, text, datetime.now(timezone.utc).isoformat())
