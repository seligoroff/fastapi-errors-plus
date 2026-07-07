"""Mypy: ErrorDTO / LegacyErrorDTO protocol assignments (0.8)."""

from fastapi_errors_plus.protocol import ErrorDTO, LegacyErrorDTO


class _ModernDTO:
    status_code = 404
    message = "Not found"

    def to_examples(self) -> dict:
        return {"n": {"value": {"detail": "x"}}}


class _LegacyDTO:
    status_code = 404
    message = "Not found"

    def to_example(self) -> dict:
        return {"n": {"value": {"detail": "x"}}}


def _accept_error_dto(_: ErrorDTO) -> None:
    pass


def _accept_legacy(_: LegacyErrorDTO) -> None:
    pass


_accept_error_dto(_ModernDTO())
_accept_legacy(_LegacyDTO())
