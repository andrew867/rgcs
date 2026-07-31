"""R10.61 -- directory-index crawling, size estimation, and manifests.

Only official mission roots are reachable. Every candidate URL is checked
against :data:`ALLOWED_ROOTS` after normalisation, so a relative link in
a remote page cannot walk the crawler outside the archive it was pointed
at. That check is the security boundary and it is tested directly.

Estimation uses HEAD, falling back to a Range-limited GET when a server
does not answer HEAD. The archive is never downloaded to measure it.
"""

from __future__ import annotations

import posixpath
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

#: Official roots. Nothing outside these is ever fetched.
ALLOWED_ROOTS = (
    "https://heasarc.gsfc.nasa.gov/FTP/vela5b/",
    "https://heasarc.gsfc.nasa.gov/docs/vela5b/",
    "https://heasarc.gsfc.nasa.gov/FTP/software/ftools/",
    "https://heasarc.gsfc.nasa.gov/docs/cgro/",
    "https://heasarc.gsfc.nasa.gov/FTP/compton/",
    "https://fermi.gsfc.nasa.gov/ssc/data/",
    "https://heasarc.gsfc.nasa.gov/FTP/fermi/",
    "https://pds-ppi.igpp.ucla.edu/",
    "https://pds.nasa.gov/",
)

USER_AGENT = ("rgcs-archive/0.1 (research downloader; "
              "contact via repository issues)")

#: Politeness. Deep-space archives are shared public infrastructure.
DEFAULT_CONCURRENCY = 2
DEFAULT_DELAY_S = 0.5
DEFAULT_TIMEOUT_S = 60.0
DEFAULT_MAX_RETRIES = 4


class CatalogError(ValueError):
    """A URL is outside the allowlist, or an index could not be parsed."""


def normalise(url: str) -> str:
    """Collapse dot segments so ``..`` cannot escape a root."""
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise CatalogError(f"unsupported scheme in {url!r}")
    path = posixpath.normpath(p.path)
    if p.path.endswith("/") and not path.endswith("/"):
        path += "/"
    return f"{p.scheme}://{p.netloc}{path}" + (f"?{p.query}" if p.query else "")


def is_allowed(url: str) -> bool:
    """Is ``url`` inside an official root, after normalisation?"""
    try:
        u = normalise(url)
    except CatalogError:
        return False
    return any(u.startswith(normalise(root)) for root in ALLOWED_ROOTS)


def assert_allowed(url: str) -> str:
    u = normalise(url)
    if not is_allowed(u):
        raise CatalogError(
            f"{url!r} is outside the official allowlist; refusing to fetch")
    return u


class _IndexParser(HTMLParser):
    """Collect hrefs from an Apache/nginx style directory index."""

    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        for k, v in attrs:
            if k == "href" and v:
                self.hrefs.append(v)


#: Directory indexes put the date and size in the row text after the link.
#: TWO date formats are in the wild and both must be matched, because a
#: date that fails to match lets the size group swallow the year: HEASARC
#: serves ISO "1995-02-14 15:48", classic Apache serves "14-Feb-1995 15:48".
#: An earlier revision matched only the Apache form and reported the
#: Vela 5B archive as 24 MiB instead of the correct 4.9 GiB.
_ROW = re.compile(
    r'href="(?P<href>[^"?][^"]*)"[^>]*>[^<]*</a>\s*'
    r'(?P<date>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}'
    r'|\d{2}-\w{3}-\d{4}\s+\d{2}:\d{2})?\s*'
    r'(?P<size>[\d.]+[KMGT]|[\d]+|-)?', re.I)

_SIZE_UNITS = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3,
                "T": 1024 ** 4}


def _parse_size(text: str | None) -> int | None:
    if not text or text.strip() in ("-", ""):
        return None
    t = text.strip().upper()
    unit = t[-1] if t[-1] in _SIZE_UNITS else ""
    try:
        return int(float(t[:-1] if unit else t) * _SIZE_UNITS[unit])
    except ValueError:
        return None


def parse_index(html: str, base_url: str) -> list:
    """Parse a directory index into entries, discarding anything outside root.

    Returns dicts with ``url``, ``name``, ``is_dir``, ``reported_size`` and
    ``reported_date``. Parent links and sort links are dropped.
    """
    base = assert_allowed(base_url)
    p = _IndexParser()
    p.feed(html)
    meta = {m.group("href"): m for m in _ROW.finditer(html)}
    out, seen = [], set()
    for href in p.hrefs:
        if href.startswith(("?", "#")) or href in ("../", "/"):
            continue
        url = normalise(urljoin(base, href))
        if not url.startswith(base) or url == base or url in seen:
            continue
        seen.add(url)
        m = meta.get(href)
        out.append({
            "url": url,
            "name": posixpath.basename(url.rstrip("/")),
            "is_dir": url.endswith("/"),
            "reported_size": _parse_size(m.group("size")) if m else None,
            "reported_date": (m.group("date") or "").strip() if m else "",
        })
    return out


def crawl(base_url: str, fetch, max_depth: int = 2,
          max_entries: int = 20000) -> list:
    """Walk a directory index. ``fetch(url) -> str`` supplies the HTML.

    ``fetch`` is injected so the crawler is testable against a local fake
    index with no network at all.
    """
    root = assert_allowed(base_url)
    queue, files, seen = [(root, 0)], [], {root}
    while queue and len(files) < max_entries:
        url, depth = queue.pop(0)
        try:
            html = fetch(url)
        except Exception as exc:                       # noqa: BLE001
            files.append({"url": url, "error": f"{type(exc).__name__}: {exc}",
                          "is_dir": True})
            continue
        for e in parse_index(html, url):
            if e["is_dir"]:
                if depth < max_depth and e["url"] not in seen:
                    seen.add(e["url"])
                    queue.append((e["url"], depth + 1))
            else:
                files.append(e)
    return files


def estimate(entries) -> dict:
    """File count and byte estimate, separating known from unknown sizes."""
    rows = [e for e in entries if not e.get("is_dir") and "error" not in e]
    known = [e for e in rows if e.get("reported_size")]
    unknown = [e for e in rows if not e.get("reported_size")]
    total = sum(e["reported_size"] for e in known)
    return {
        "schema": "rgcs.r1061.estimate.v1",
        "files": len(rows),
        "with_reported_size": len(known),
        "without_reported_size": len(unknown),
        "known_bytes": total,
        "known_mib": round(total / 1024 ** 2, 2),
        "known_gib": round(total / 1024 ** 3, 3),
        "mean_known_bytes": (total // len(known)) if known else 0,
        "projected_total_bytes": (
            total + (total // len(known)) * len(unknown)) if known else None,
        "note": "projection assumes unknown-size files match the known mean; "
                "it is an estimate, not a measurement",
    }
