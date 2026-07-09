"""DeprecationWarning contract tests — release 0.9.3 phase 0 (W01–W04)."""

from __future__ import annotations

import warnings
from typing import Any, Iterable, Sequence

import pytest

from fastapi_errors_plus import Errors

from tests.conftest import SimpleErrorDTO

# Library modules that must not appear as the warning origin for flag/kwarg deprecations
# (W04 baseline before phase 2; extended when _flags_and_profile.py exists).
_FORBIDDEN_FLAG_WARNING_PATH_PARTS: tuple[str, ...] = (
    "fastapi_errors_plus/errors.py",
    "fastapi_errors_plus/_flags_and_profile.py",
)


def _deprecation_messages(caught: Sequence[warnings.WarningMessage]) -> list[str]:
    return [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
    ]


def _find_deprecation(
    caught: Sequence[warnings.WarningMessage],
    *,
    substring: str,
) -> warnings.WarningMessage:
    matches = [
        w
        for w in caught
        if issubclass(w.category, DeprecationWarning) and substring in str(w.message)
    ]
    assert len(matches) == 1, (
        f"Expected exactly one DeprecationWarning containing {substring!r}, "
        f"got {len(matches)}: {_deprecation_messages(caught)}"
    )
    return matches[0]


def assert_warning_at_user_call_site(
    warning: warnings.WarningMessage,
    *,
    test_file: str,
    forbidden_path_parts: Iterable[str] = _FORBIDDEN_FLAG_WARNING_PATH_PARTS,
) -> None:
    """Warning must attribute to the test module, not library internals."""
    normalized = warning.filename.replace("\\", "/")
    for part in forbidden_path_parts:
        assert part not in normalized, (
            f"DeprecationWarning must point at user call site, not {part!r}; "
            f"got {warning.filename}:{warning.lineno}"
        )
    assert normalized.endswith(test_file), (
        f"Expected warning from {test_file!r}, got {warning.filename}:{warning.lineno}"
    )


@pytest.mark.unit
class TestErrorsDeprecationWarnings:
    """W01–W04: deprecation messages and stacklevel attribution."""

    def test_w01_implicit_422_without_explicit_kwarg(self) -> None:
        """``Errors()`` without 422 kwargs emits implicit-422 deprecation."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            errors = Errors()

        warning = _find_deprecation(
            caught,
            substring="Implicit validation_error_422=True is deprecated",
        )
        assert 422 in errors
        assert_warning_at_user_call_site(warning, test_file=__file__)

    def test_w02_legacy_unauthorized_kwarg(self) -> None:
        """``Errors(unauthorized=True)`` emits legacy-kw deprecation."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            Errors(unauthorized=True, validation_error_422=False)

        warning = _find_deprecation(
            caught,
            substring="unauthorized is deprecated; use unauthorized_401 instead",
        )
        assert_warning_at_user_call_site(warning, test_file=__file__)

    def test_w03_legacy_to_example_on_dto(self) -> None:
        """DTO with ``to_example()`` emits legacy-method deprecation."""
        dto = SimpleErrorDTO(
            status_code=404,
            message="Not found",
            example_value={"detail": "Not found"},
        )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            Errors(dto, validation_error_422=False)

        warning = _find_deprecation(
            caught,
            substring="implements deprecated to_example(); use to_examples() instead",
        )
        assert "SimpleErrorDTO" in str(warning.message)

    @pytest.mark.parametrize(
        ("kwargs", "substring"),
        [
            pytest.param({}, "Implicit validation_error_422=True is deprecated", id="implicit-422"),
            pytest.param(
                {"unauthorized": True, "validation_error_422": False},
                "unauthorized is deprecated; use unauthorized_401 instead",
                id="legacy-unauthorized",
            ),
            pytest.param(
                {"forbidden": True, "validation_error_422": False},
                "forbidden is deprecated; use forbidden_403 instead",
                id="legacy-forbidden",
            ),
            pytest.param(
                {"validation_error": False},
                "validation_error is deprecated; use validation_error_422 instead",
                id="legacy-validation-error",
            ),
            pytest.param(
                {"internal_server_error": True, "validation_error_422": False},
                "internal_server_error is deprecated; use internal_server_error_500 instead",
                id="legacy-internal-server-error",
            ),
        ],
    )
    def test_w04_flag_warnings_attribute_user_call_site_not_library(
        self,
        kwargs: dict[str, Any],
        substring: str,
    ) -> None:
        """W04 baseline: flag/kwarg warnings must not originate from library modules."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            Errors(**kwargs)

        warning = _find_deprecation(caught, substring=substring)
        assert_warning_at_user_call_site(warning, test_file=__file__)
