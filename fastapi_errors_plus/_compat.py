"""Compatibility shims with no internal package dependencies."""

from __future__ import annotations

from fastapi import status

# Starlette (via FastAPI) prefers HTTP_422_UNPROCESSABLE_CONTENT over ENTITY.
# Older pins may lack CONTENT (import crash); avoid nested getattr(, default=)
# touching ENTITY when CONTENT exists (DeprecationWarning).
_http_422_attr = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", None)
if _http_422_attr is None:
    HTTP_422 = int(getattr(status, "HTTP_422_UNPROCESSABLE_ENTITY", 422))
else:
    HTTP_422 = int(_http_422_attr)
