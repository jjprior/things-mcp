"""Read the Things database through a cached snapshot, not the protected container.

Why: since macOS 27, the Things database (in Things' group container) is behind
the "Data shared by Things and affiliated apps" privacy gate, and the grant is
attributed to the executable that started the process chain. For this server
that is the Claude Code binary, which lives at a new versioned path after every
update, so every update produced a fresh permission pop-up and a dead TCC row.

Fix: `automation/things-server` (launchd, port 8091, the one process that is
granted access) serves a consistent read-only copy of the live DB at
/things-db.sqlite with an ETag that changes whenever Things writes. We pull
that copy into ~/Library/Caches/things-mcp with a conditional GET (304 when
nothing changed, ~5 MB otherwise) and point things.py at it via the THINGSDB
environment variable, which things.py honours natively. Writes are unaffected:
they go through the Things URL scheme, never the DB.

Set THINGS_SNAPSHOT_URL to an empty string to disable and read the DB directly
(useful on a machine without things-server).
"""
import logging
import os
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

SNAPSHOT_URL = os.environ.get("THINGS_SNAPSHOT_URL", "http://localhost:8091/things-db.sqlite")
CACHE_DIR = Path(os.environ.get("THINGS_SNAPSHOT_CACHE") or "~/Library/Caches/things-mcp").expanduser()
CACHE_FILE = CACHE_DIR / "main.sqlite"
ETAG_FILE = CACHE_DIR / "main.sqlite.etag"
TIMEOUT = 5.0

_lock = threading.Lock()
_warned_stale = False


def enabled() -> bool:
    return bool(SNAPSHOT_URL)


def _read_etag():
    try:
        return ETAG_FILE.read_text().strip() or None
    except OSError:
        return None


def _store(body: bytes, etag):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".sqlite.part")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(body)
        os.replace(tmp, CACHE_FILE)  # atomic: a reader never sees a half-written DB
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    ETAG_FILE.write_text(etag or "")


def refresh() -> bool:
    """Bring the cached snapshot up to date and point things.py at it.

    Returns True when things.py will read the snapshot, False when it will fall
    back to the live database (snapshot disabled, or server down with no cache).
    Never raises: a read tool should still get an answer if the server hiccups.
    """
    global _warned_stale
    if not enabled():
        return False
    with _lock:
        etag = _read_etag() if CACHE_FILE.exists() else None
        headers = {"If-None-Match": etag} if etag else {}
        try:
            req = urllib.request.Request(SNAPSHOT_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                _store(resp.read(), resp.headers.get("ETag"))
            _warned_stale = False
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                _warned_stale = False
            else:
                return _fallback(f"HTTP {exc.code} from {SNAPSHOT_URL}")
        except (urllib.error.URLError, OSError) as exc:
            return _fallback(str(exc))
        os.environ["THINGSDB"] = str(CACHE_FILE)
        return True


def _fallback(reason: str) -> bool:
    """Server unreachable: keep a stale cache if there is one, else read live."""
    global _warned_stale
    if CACHE_FILE.exists():
        if not _warned_stale:
            logger.warning("things-server unreachable (%s); using stale snapshot %s", reason, CACHE_FILE)
            _warned_stale = True
        os.environ["THINGSDB"] = str(CACHE_FILE)
        return True
    logger.warning("things-server unreachable (%s) and no cached snapshot; reading the live Things DB", reason)
    os.environ.pop("THINGSDB", None)
    return False
