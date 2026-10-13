"""
One identity per document URL.

The same page can be pasted as `HTTPS://Help.Example.com:443/a/#top` or
`https://help.example.com/a`. normalize_url() maps both to one string, so a
document is stored, looked up and de-duplicated under one key.

Only the parts that never change which page is served are touched. The path
keeps its case and the query string is kept: on some help centres both pick
the article.

Only http(s) URLs are rewritten. Other schemes are names, not addresses:
`local://Yotpo` labels pasted text, and its case is part of the name.
"""

from urllib.parse import urlsplit, urlunsplit

_DEFAULT_PORTS = {'http': 80, 'https': 443}


def normalize_url(url: str) -> str:
    """Strip whitespace; for http(s), also drop the #fragment, lowercase
    scheme and host, drop the default port, and drop a trailing slash except
    on the root path."""
    url = (url or '').strip()
    if not url:
        return url
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        return url

    host = (parts.hostname or '')  # urlsplit lowercases the host
    if ':' in host:
        host = f'[{host}]'  # IPv6 literal
    try:
        port = parts.port
    except ValueError:
        port = None  # not a number: leave the netloc as it was
        netloc = parts.netloc.lower()
    else:
        netloc = host
        if port is not None and port != _DEFAULT_PORTS.get(scheme):
            netloc = f'{host}:{port}'
        userinfo = parts.netloc.rpartition('@')[0] if '@' in parts.netloc else ''
        if userinfo:
            netloc = f'{userinfo}@{netloc}'

    path = parts.path
    if len(path) > 1 and path.endswith('/'):
        path = path.rstrip('/') or '/'

    return urlunsplit((scheme, netloc, path, parts.query, ''))
