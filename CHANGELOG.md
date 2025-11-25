# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

---

## [0.1.1] - 2025-01-XX

### Fixed
- Fixed direct key access in `_add_standard_error()` and `_add_error_dto()` methods that could cause KeyError with incomplete dict structures
- Improved robustness: replaced direct dictionary access with safe `setdefault()` calls
- Code is now fully resilient to arbitrary dict structures

### Changed
- None

---

## [0.1.0] - 2025-01-XX

### Fixed
- **Critical bug fix**: Fixed merging/overwriting logic for error examples (issue #5)
  - `_add_standard_error()` now uses unique keys (`StandardUnauthorized`, `StandardForbidden`, etc.) instead of overwriting `default`
  - Created `_add_dict_error()` method to properly merge dict errors instead of simple `update()`
  - `_add_error_dto()` now correctly converts `example` to `examples` while preserving standard flag keys
  - All methods now correctly merge examples regardless of argument order
  - Description priority: dict > DTO > standard flags

### Added
- Initial implementation of `Errors` class for documenting errors in FastAPI endpoints
- Support for standard HTTP status flags (401, 403, 422, 500)
- Support for dict-based errors in FastAPI responses format
- Support for ErrorDTO protocol for project compatibility
- Automatic merging of examples for the same status code
- ErrorDTO protocol validation with clear error messages
- Comprehensive test suite (41 tests, 91% coverage)
- Full documentation in English and Russian
- MIT license
- CHANGELOG.md for tracking changes

### Changed
- None

### Fixed
- ErrorDTO validation now checks all required attributes (status_code, message, to_example) early with clear TypeError messages
- Early error detection: validation happens during `Errors()` creation, not during usage

### Security
- None

---

## [0.1.0] - 2025-01-XX

### Added
- Initial release of fastapi-errors-plus
- `Errors` class with support for:
  - Standard HTTP status flags (unauthorized, forbidden, validation_error, internal_server_error)
  - Dict-based errors in FastAPI responses format
  - ErrorDTO protocol for project compatibility
- `ErrorDTO` protocol definition
- Automatic merging of examples for the same status code
- ErrorDTO validation with comprehensive error messages
- Full type hints support
- Comprehensive test suite:
  - 18 unit tests
  - 16 integration tests
  - 7 validation tests
  - 91% code coverage
- Documentation:
  - README.md (English)
  - README.ru.md (Russian)
  - Examples for standard FastAPI projects
  - Examples for Clean Architecture integration
  - API reference
- Test FastAPI application with 7 endpoints demonstrating different use cases

### Fixed
- ErrorDTO validation now checks all required attributes (status_code, message, to_example)
- Early error detection with clear TypeError messages
- Protection against invalid objects being treated as ErrorDTO

---

## [Unreleased] - Planned

### Added
- Support for additional HTTP status flags (400, 404, 405, 409)
- Mapping protocol implementation for better API ergonomics
- Improved error handling for arbitrary dict structures
- py.typed marker for PEP 561 support

### Fixed
- Consistent merge logic for standard errors and ErrorDTO
- Documentation examples with correct Python syntax
- Bug in example merging that causes data loss

[Unreleased]: https://github.com/seligoroff/fastapi-errors-plus/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/seligoroff/fastapi-errors-plus/releases/tag/v0.1.0

