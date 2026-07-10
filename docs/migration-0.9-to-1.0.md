# Migration Guide: 0.9.x → 1.0

Guide for upgrading from **0.9.x** to **1.0.0+**. See also [CHANGELOG.md](../CHANGELOG.md) § 1.0.0.

## Breaking changes (summary)

| Area | 0.9.x | 1.0 |
|------|-------|-----|
| `unauthorized`, `forbidden`, `validation_error`, `internal_server_error` | Deprecated, still accepted | **`TypeError`** — use `*_401` / `*_403` / `*_422` / `*_500` |
| `Errors()` without 422 kwargs | Adds 422 + `DeprecationWarning` | **No 422** (empty mapping if no other errors) |
| `validation_error_422=None` (default) | Implicit 422 + warning | **`False` behaviour** — no 422 unless profile says otherwise |
| DTO with only `to_example()` | Works + `DeprecationWarning` | **`TypeError`** — implement `to_examples()` |
| `BaseErrorDTO.to_example()` etc. | Deprecated alias | **Removed** — call `to_examples()` |
| `LegacyErrorDTO`, `ErrorDTOLike` | Public exports | **Removed** — annotate with `ErrorDTO` only |

## Upgrade checklist

1. **Rename `to_example` → `to_examples`** on custom DTOs and domain exceptions — **hard break**; `TypeError` at import/route registration if skipped.
2. **Audit codebase** (search patterns below).
3. **Replace legacy kwargs** (`unauthorized`, …) with `*_401` / `*_403` / `*_422` / `*_500`.
4. **Set `validation_error_422` explicitly** on endpoints that should document 422 (or use `ErrorProfile`).
5. **Run tests** and **OpenAPI diff** (checklist below).
6. Bump dependency: `fastapi-errors-plus>=1.0,<2`.

## Search patterns (`rg`)

From repository root:

```bash
# Legacy example method on DTOs (highest priority — breaks at startup)
rg 'def to_example\b' --glob '*.py'
rg '\.to_example\(' --glob '*.py'

# Legacy Errors kwargs (Python call sites)
rg 'unauthorized\s*=\s*True|forbidden\s*=\s*True|validation_error\s*=|internal_server_error\s*=' \
  --glob '*.py' --glob '!**/CHANGELOG.md'

# Shorter variant (may match comments/docs)
rg 'unauthorized=|forbidden=|validation_error=|internal_server_error=' .

# All Errors() usages (manual review)
rg 'Errors\(' -g '*.py'
```

### Codemod hints

**`to_example` → `to_examples`** (method definition only):

```bash
rg -l 'def to_example\b' --glob '*.py' | while read -r f; do
  sed -i 's/def to_example(/def to_examples(/g' "$f"
done
```

Re-run `rg 'def to_example\b'` until clean. Fix call sites: `.to_example()` → `.to_examples()`.

**Legacy kwargs** (review each match; comments need manual edit):

```bash
# Example with sed — dry-run on a single file first
sed -E \
  -e 's/\bunauthorized=True/unauthorized_401=True/g' \
  -e 's/\bforbidden=True/forbidden_403=True/g' \
  -e 's/\bvalidation_error=False/validation_error_422=False/g' \
  -e 's/\bvalidation_error=True/validation_error_422=True/g' \
  -e 's/\binternal_server_error=True/internal_server_error_500=True/g' \
  path/to/file.py
```

## Before / after

### `to_example()` → `to_examples()` (removed in 1.0)

```python
# before
class ItemNotFoundError(DomainException):
    status_code = 404
    message = "Item not found"

    def to_example(self):
        return {self.message: {"value": {"detail": self.message}}}

# after
class ItemNotFoundError(DomainException):
    status_code = 404
    message = "Item not found"

    def to_examples(self):
        return {self.message: {"value": {"detail": self.message}}}
```

### Legacy kwargs

```python
# before
Errors(unauthorized=True, forbidden=True, validation_error=False)

# after
Errors(unauthorized_401=True, forbidden_403=True, validation_error_422=False)
```

Removed names raise at runtime:

```python
Errors(unauthorized=True)
# TypeError: 'unauthorized' was removed; use 'unauthorized_401' instead.
```

### Default 422

```python
# before — implicit 422 in OpenAPI
@router.get("/health", responses=Errors())
def health(): ...

# after — no 422 in documented responses (usually correct for no-arg endpoints)
@router.get("/health", responses=Errors())
def health(): ...

# after — when you want documented 422 (validated params/body)
@router.post("/items", responses=Errors(validation_error_422=True))
def create_item(body: ItemCreate): ...
```

### Project-wide defaults (`ErrorProfile`)

```python
ADR = ErrorProfile(
    unauthorized_401=True,
    validation_error_422=False,  # ADR error bodies, not generic 422
)

Errors(domain_error, profile=ADR)
```

Explicit kwargs still override profile (unchanged from 0.9).

### Typing

```python
# before
from fastapi_errors_plus import ErrorDTOLike, LegacyErrorDTO

def handler(err: ErrorDTOLike): ...

# after
from fastapi_errors_plus import ErrorDTO

def handler(err: ErrorDTO): ...
```

## OpenAPI diff checklist

After upgrading, compare generated OpenAPI (or committed snapshot) against **0.9.x** baseline:

| Check | What to look for |
|-------|------------------|
| **Missing 422** | Endpoints that used bare `Errors()` or omitted `validation_error_422` may **drop** status `422` from `responses`. Add `validation_error_422=True` where the contract should list validation errors. |
| **Unchanged 401/403/500** | Flags renamed only in Python — documented blocks should match if you migrated kwargs correctly. |
| **DTO examples** | Same `examples` keys under `content.application/json` when `to_examples()` returns the same map as old `to_example()`. |
| **Depends() auth** | 401/403 from dependencies still need explicit `unauthorized_401` / `forbidden_403` (or profile) — library does not infer from `Depends`. |
| **FastAPI auto-422** | `validation_error_422=False` disables **library-managed** 422 only; FastAPI may still emit `HTTPValidationError` for invalid params — treat separately in contract tests. |
| **Merge / schema** | No change expected for dict merge, `openapi_json_extras`, or `ErrorDoc` bodies if DTO layer migrated. |

Suggested CI step:

```bash
# Example: export OpenAPI and diff (adjust app import path)
python -c "from myapp.main import app; import json; print(json.dumps(app.openapi(), sort_keys=True))" \
  > openapi-1.0.json
diff -u openapi-0.9-baseline.json openapi-1.0.json
```

## Verification

```bash
# Library repo
make test
make lint
make type-check

# Your service
pytest
# + OpenAPI snapshot diff
rg 'def to_example\b' --glob '*.py'  # expect none on DTOs used with Errors()
rg 'unauthorized=|forbidden=|validation_error=|internal_server_error=' .  # expect no Python call sites
```

## Rollback

Pin `fastapi-errors-plus>=0.9,<1.0` until migration is complete. **0.9.3** is the last non-breaking line before 1.0.
