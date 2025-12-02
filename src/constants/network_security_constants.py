
from typing import Final, FrozenSet

ALLOWED_METHODS: Final[FrozenSet[str]] = frozenset({"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"})
REQUIRED_HEADERS: Final[FrozenSet[str]] = frozenset({
    "X-Request-ID",
    "Authorization", 
    "Content-Type"
})

SUSPICIOUS_HEADERS: Final[FrozenSet[str]] = frozenset({
    "X-Requested-With", "X-HTTP-Method-Override", "X-Real-IP", "X-Rewrite-URL", "X-Custom-Header", "X-Another-Header"})