# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

---

## [0.6.1] - 2025-01-XX

### Added
- **Tests for Domain Exception pattern**: Added comprehensive test suite for `for_openapi()` pattern
  - 5 new integration tests verifying Domain Exception as ErrorDTO pattern works correctly
  - Tests verify OpenAPI schema generation for Domain Exceptions
  - Tests verify `for_openapi()` method returns correct ErrorDTO instances
  - Tests verify integration with `Errors` class
  - Test endpoint `/api/v1/domain-exception/{item_id}` demonstrating the pattern

### Changed
- **Test coverage**: Improved test coverage to 86.50% (from 83%)
  - Added test classes `DomainException`, `TestItemNotFoundError`, `TestItemAccessDeniedError` in test suite
  - All tests for Best Practice pattern now included

### Migration Guide
- **No breaking changes**: All changes are test additions
- **For users**: The documented Best Practice pattern is now fully tested and verified

---

## [0.6.0] - 2025-01-XX

### Added
- **Best Practice documentation**: Added comprehensive guide for connecting exceptions and ErrorDTO
  - New section "Best Practice: Connecting Exceptions and ErrorDTO" in README
  - Demonstrates recommended pattern: Domain Exception as ErrorDTO
  - Shows how to make exceptions implement ErrorDTO protocol directly
  - Benefits: clear connection visible in endpoint, no duplication, type-safe
- **Example implementation**: Added `examples/domain_exceptions.py` with complete working example
  - Base `DomainException` class implementing ErrorDTO protocol
  - Example exceptions (`NotificationNotFoundError`, `NotificationAccessDeniedError`)
  - Example endpoint usage
  - Example exception handlers (commented)
- **API Reference updates**: Added references to best practice in ErrorDTO Protocol section

### Changed
- **Documentation cleanup**: Removed emoji from all documentation files
  - Cleaner, more professional appearance
  - Better compatibility with various markdown renderers
- **Coverage configuration**: Fixed htmlcov generation path
  - Now generates in `tests/htmlcov/` instead of project root
  - Configuration moved from `pytest.ini` to `pyproject.toml`

### Migration Guide
- **No breaking changes**: All changes are documentation and configuration improvements
- **Best Practice**: Consider adopting Domain Exception as ErrorDTO pattern for better code clarity
- **Coverage**: If you have custom coverage scripts, htmlcov will now be in `tests/htmlcov/` instead of root

---

## [0.5.0] - 2025-01-XX

### Fixed
- **Type annotations**: Fixed `validation_error` and `validation_error_422` type annotations from `bool = None` to `Optional[bool] = None`
  - Resolves type checker errors (MyPy, Pyright)
  - Documentation now correctly reflects the actual type signature
- **Documentation examples**: Fixed incorrect argument order in docstring example (positional arguments must come before keyword arguments)
- **README accuracy**: Removed outdated "Callable object" mention, replaced with correct "Mapping object" description
- **Example key collisions**: Fixed potential data loss when merging examples with same keys
  - Added `_unique_key()` method to generate unique keys for examples
  - Prevents overwriting existing examples during merges
- **DTO description priority**: Fixed DTO not overriding standard flag descriptions
  - DTO descriptions now correctly override standard flag descriptions
  - Maintains priority: dict > DTO > standard flags

### Added
- **PEP 561 support**: Added `py.typed` marker file for type checker support
  - MyPy, Pyright, and Pylance now recognize type annotations
  - Improves IDE autocomplete and type checking in user projects
- **Unique key generation**: Added `_unique_key()` method to prevent example key collisions
- **Standard descriptions mapping**: Added `STANDARD_DESCRIPTIONS` for priority checking

### Changed
- Improved type safety with `Optional[bool]` for validation_error parameters
- Enhanced documentation accuracy and consistency

### Migration Guide
- **No breaking changes**: All fixes are backward compatible
- **Type checkers**: If you use MyPy or Pyright, you may see fewer type errors after updating
- **Documentation**: Examples in documentation now follow correct Python syntax

---

## [0.4.0] - 2025-01-XX

### Changed
- **Breaking change (improvement)**: `validation_error` and `validation_error_422` now default to `True` instead of `False`
  - FastAPI automatically validates all parameters (Path, Query, Body), making 422 relevant in 95%+ of endpoints
  - This reduces repetitive code - no need to specify `validation_error=True` in every endpoint
  - For endpoints without parameters, explicitly set `validation_error=False` or `validation_error_422=False`
  - Existing code continues to work (explicit `validation_error=True` still works)
  - This change improves documentation accuracy by default

### Added
- Comprehensive test suite for new default behavior:
  - Tests for `validation_error=True` by default
  - Tests for explicitly disabling validation_error
  - Tests for backward compatibility (explicit `True` still works)
  - Tests for mixing with other errors

### Fixed
- None

### Migration Guide
- **No action required**: Existing code continues to work without changes
- **Optional optimization**: You can remove explicit `validation_error=True` from endpoints (it's now the default)
- **For endpoints without parameters**: Add `validation_error=False` to disable 422 documentation

---

## [0.3.0] - 2025-01-XX

### Added
- **Explicit status code flags**: New parameters with status codes in names for better readability
  - `unauthorized_401=True` → 401 Unauthorized (explicit)
  - `forbidden_403=True` → 403 Forbidden (explicit)
  - `validation_error_422=True` → 422 Unprocessable Entity (explicit)
  - `internal_server_error_500=True` → 500 Internal Server Error (explicit)
  - Status codes are now visible directly in the code, improving readability
  - No need to remember which status code corresponds to which flag
- Comprehensive test suite for new explicit flags:
  - Tests for each new flag parameter
  - Tests for backward compatibility (old flags still work)
  - Tests for mixing old and new flags
  - Tests for priority logic (new flags work independently)

### Changed
- Updated documentation to recommend explicit flags (`_401`, `_403`, etc.)
- Updated examples in README to use new explicit flags
- API Reference section updated with new parameters

### Fixed
- None

### Deprecated
- Old flag parameters (`unauthorized`, `forbidden`, `validation_error`, `internal_server_error`) are still supported for backward compatibility but are marked as deprecated in documentation. New code should use explicit flags with status codes.

---

## [0.2.0] - 2025-01-XX

### Added
- **BaseErrorDTO**: Base implementation of ErrorDTO Protocol for convenience
  - Simple class for errors with a single example
  - No need to write ErrorDTO classes from scratch
  - Ready-to-use implementation with correct format
- **StandardErrorDTO**: Extended implementation for errors with multiple examples
  - Useful for standard HTTP errors (401, 403) with different causes
  - Supports multiple examples in one error object
  - Defaults to single example if not provided
- Comprehensive test suite for BaseErrorDTO and StandardErrorDTO:
  - 15 unit tests for base classes
  - 6 integration tests with FastAPI
  - Tests for inheritance and structural typing compatibility
- Updated documentation with examples of BaseErrorDTO and StandardErrorDTO usage
- New test endpoints in test_app.py demonstrating BaseErrorDTO and StandardErrorDTO

### Changed
- Updated `__init__.py` to export `BaseErrorDTO` and `StandardErrorDTO`
- README now includes section "When to Use Protocol vs BaseErrorDTO"
- API Reference section expanded with BaseErrorDTO and StandardErrorDTO documentation

### Fixed
- None

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

