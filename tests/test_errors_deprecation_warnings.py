"""DeprecationWarning contract tests — implicit 422 removed in 1.0 (B2)."""

from __future__ import annotations

import warnings

import pytest

from fastapi_errors_plus import Errors


@pytest.mark.unit
class TestErrorsDeprecationWarnings:
    def test_no_implicit_422_warning_on_empty_errors(self) -> None:
        """``Errors()`` must not emit implicit-422 deprecation (1.0 default)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            errors = Errors()

        implicit_422 = [
            w
            for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "Implicit validation_error_422" in str(w.message)
        ]
        assert not implicit_422
        assert len(errors) == 0
