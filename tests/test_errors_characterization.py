"""Characterization (golden) tests for Errors output — release 0.9.3 phase 0."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any, Dict

import pytest
from fastapi import status

from tests.fixtures.errors_characterization_data import (
    CHARACTERIZATION_CASES,
    build_c12,
)


def errors_to_mapping(errors: Mapping[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Materialize Errors as a plain dict via Mapping protocol (__getitem__ deepcopy)."""
    return {code: errors[code] for code in sorted(errors)}


@pytest.mark.unit
class TestErrorsCharacterization:
    """Golden snapshots of ``Errors(...)`` OpenAPI response mapping."""

    @pytest.mark.parametrize(
        ("scenario_id", "builder", "expected"),
        CHARACTERIZATION_CASES,
        ids=[case[0] for case in CHARACTERIZATION_CASES],
    )
    def test_snapshot(
        self,
        scenario_id: str,
        builder,
        expected: Dict[int, Dict[str, Any]],
    ) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            errors = builder()

        actual = errors_to_mapping(errors)
        assert actual == expected, f"{scenario_id}: OpenAPI mapping mismatch"

    def test_c12_getitem_returns_deepcopy(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            errors = build_c12()

        assert errors_to_mapping(errors) == errors_to_mapping(errors)

        item = errors[status.HTTP_401_UNAUTHORIZED]
        item["description"] = "MUTATED"
        item["content"]["application/json"]["example"]["detail"] = "MUTATED"

        assert (
            errors[status.HTTP_401_UNAUTHORIZED]["description"] == "Unauthorized"
        )
        assert (
            errors[status.HTTP_401_UNAUTHORIZED]["content"]["application/json"][
                "example"
            ]["detail"]
            == "Unauthorized"
        )
