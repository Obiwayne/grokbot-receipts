"""Which site a URL belongs to, so two links from the same publisher count once."""

from urllib.parse import urlparse

# Second-level suffixes where the site name is the third label from the right.
_TWO_LEVEL = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk", "ltd.uk", "plc.uk",
    "com.au", "net.au", "org.au", "gov.au", "edu.au",
    "co.nz", "org.nz", "govt.nz",
    "co.jp", "or.jp", "ne.jp", "go.jp",
    "com.br", "gov.br", "co.in", "gov.in", "co.za", "gov.za",
    "com.mx", "com.ar", "com.tr", "com.cn", "com.hk", "com.sg",
}

# Hosts that are the same site under another name.
_ALIASES = {
    "twitter.com": "x.com",
    "t.co": "x.com",
    "youtu.be": "youtube.com",
    "redd.it": "reddit.com",
}


def site_of(url: str) -> str:
    """The registrable domain of a URL, e.g. https://www.bbc.co.uk/news -> bbc.co.uk."""
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return ""
    if host.replace(".", "").isdigit() or host == "localhost":
        # Local and IP hosts: keep the port so test servers on different ports stay distinct.
        port = urlparse(url).port
        return f"{host}:{port}" if port else host
    labels = host.split(".")
    tail = ".".join(labels[-2:])
    site = ".".join(labels[-3:]) if tail in _TWO_LEVEL and len(labels) >= 3 else tail
    return _ALIASES.get(site, site)
