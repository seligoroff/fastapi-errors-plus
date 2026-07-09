"""Tests for legacy ``Errors`` keyword arguments removed in 1.0 (B1)."""

from __future__ import annotations

import pytest

from fastapi_errors_plus import Errors


@pytest.mark.unit
class TestLegacyErrorsKwargsRemoved:
    """Removed kwargs must raise TypeError with migration hint."""

    @pytest.mark.parametrize(
        ("kwargs", "expected_substring"),
        [
            pytest.param(
                {"unauthorized": True},
                r"'unauthorized' was removed; use 'unauthorized_401'",
                id="unauthorized",
            ),
            pytest.param(
                {"forbidden": True},
                r"'forbidden' was removed; use 'forbidden_403'",
                id="forbidden",
            ),
            pytest.param(
                {"validation_error": False},
                r"'validation_error' was removed; use 'validation_error_422'",
                id="validation_error",
            ),
            pytest.param(
                {"internal_server_error": True},
                r"'internal_server_error' was removed; use 'internal_server_error_500'",
                id="internal_server_error",
            ),
        ],
    )
    def test_legacy_kwarg_raises_type_error(
        self,
        kwargs: dict[str, object],
        expected_substring: str,
    ) -> None:
        with pytest.raises(TypeError, match=expected_substring):
            Errors(**kwargs, validation_error_422=False)
