"""Conservative URL identity: preserve case-sensitive paths and query values."""
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
TRACKING_PARAMS = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content','fbclid','gclid','ref','source','mc_cid','mc_eid'}
def normalize_url(url):
    p = urlsplit(url.strip())
    query = [(k,v) for k,v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', urlencode(query), ''))
